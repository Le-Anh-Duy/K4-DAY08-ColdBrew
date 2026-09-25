"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os
import threading
import time
from collections import deque
from functools import lru_cache

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

# Free tier Gemini ~15 RPM, vượt thì bị chặn vài phút -> tự giới hạn dưới mức đó.
LLM_RPM = int(os.getenv("LLM_RPM", "12"))
RATE_LIMIT_COOLDOWN = 60  # giây chờ khi provider vẫn trả 429
LLM_MAX_RETRIES = 2

# ponytail: limiter trong 1 process; app và script evaluation chạy song song thì
# mỗi process đếm riêng -> tổng có thể vượt RPM. Cần chung thì chạy lần lượt.
_call_times: deque[float] = deque()
_rate_lock = threading.Lock()

SYSTEM_PROMPT = """Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation. Nếu thiếu evidence, hãy từ chối xác minh."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        parts.append(
            f"[Document {index} | ID: {chunk['id']} | "
            f"Title: {metadata['title']} | Source: {metadata['source']}]\n"
            f"{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def _wait_for_rate_limit(call_times: deque | None = None, lock=None) -> None:
    """Sliding window: tối đa LLM_RPM request trong 60 giây gần nhất.

    Mặc định dùng cửa sổ của generator; model khác (vd evaluator) có quota riêng
    thì truyền deque/lock riêng.
    """
    call_times = _call_times if call_times is None else call_times
    with _rate_lock if lock is None else lock:
        now = time.monotonic()
        while call_times and now - call_times[0] >= 60:
            call_times.popleft()
        if len(call_times) >= LLM_RPM:
            wait = 60 - (now - call_times[0])
            print(f"[rate limit] {LLM_RPM} request/phút, chờ {wait:.0f}s")
            time.sleep(wait)
            call_times.popleft()
        call_times.append(time.monotonic())


def _is_rate_limited(error: Exception) -> bool:
    # google-genai: .code; openai/anthropic: .status_code
    return 429 in (getattr(error, "code", None), getattr(error, "status_code", None))


@lru_cache(maxsize=1)
def _client():
    if LLM_PROVIDER == "gemini":
        from google import genai
        return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    if LLM_PROVIDER == "openai":
        from openai import OpenAI
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic
        return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def _send(system_prompt: str, user_message: str) -> str:
    client = _client()
    if LLM_PROVIDER == "gemini":
        from google.genai import types
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                # Không dùng tool calling; tắt để SDK không in cảnh báo AFC.
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        return response.text or ""
    if LLM_PROVIDER == "openai":
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.choices[0].message.content or ""
    # anthropic: không truyền top_p cùng temperature (một số model từ chối).
    response = client.messages.create(
        model=LLM_MODEL,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=1024,
        temperature=TEMPERATURE,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình, có giới hạn RPM."""
    for attempt in range(LLM_MAX_RETRIES + 1):
        _wait_for_rate_limit()
        try:
            return _send(system_prompt, user_message)
        except Exception as error:
            if not _is_rate_limited(error) or attempt == LLM_MAX_RETRIES:
                raise
            print(f"[rate limit] provider trả 429, chờ {RATE_LIMIT_COOLDOWN}s rồi thử lại")
            time.sleep(RATE_LIMIT_COOLDOWN)
    raise AssertionError("unreachable")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    refusal = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    if top_k <= 0:
        return {
            "answer": refusal,
            "sources": [],
            "retrieval_source": "none",
        }

    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception:
        return {
            "answer": refusal,
            "sources": [],
            "retrieval_source": "none",
        }
    if not chunks:
        return {
            "answer": refusal,
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    if not context.strip():
        return {
            "answer": refusal,
            "sources": [],
            "retrieval_source": "none",
        }

    valid_source_ids = {chunk["id"] for chunk in chunks}
    user_message = (
        f"Context:\n{context}\n\nQuestion: {query}\n\n"
        "Citation rules:\n"
        "- Cite every factual claim with one or more chunk IDs from the context.\n"
        "- Use exactly this format for each citation: [chunk-id].\n"
        "- Put only one chunk ID inside each pair of brackets.\n"
        "- Do not cite Document numbers or invent IDs."
    )
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message).strip()
    except Exception:
        return {
            "answer": refusal,
            "sources": [],
            "retrieval_source": "none",
        }
    if not answer:
        return {
            "answer": refusal,
            "sources": [],
            "retrieval_source": "none",
        }

    import re

    citations = re.findall(r"\[([^\[\]\n]+)\]", answer)
    if not citations or any(citation not in valid_source_ids for citation in citations):
        return {
            "answer": refusal,
            "sources": [],
            "retrieval_source": "none",
        }

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0]["retrieval_method"],
    }


if __name__ == "__main__":
    print(generate_with_citation("test query"))

"""
Evaluation A/B: Config A dense-only vs Config B hybrid + RRF.

Hai config dùng chung golden dataset, generator (generate_with_citation), prompt,
evaluator và top_k; chỉ đổi use_reranking của retrieve().

Metric:
    faithfulness, answer_relevancy — ragas 0.4 collections, evaluator EVALUATOR_MODEL
        (model khác generator: quota free tier riêng + tránh tự chấm).
    context_recall, context_precision — context_overlap_recall / _precision so chunk
        retrieve với evidence nguyên văn trong golden set (không gọi LLM). Bản NonLLM
        của ragas so Levenshtein cả chunk với đoạn evidence nên ra 0 cả khi chunk chứa
        đủ evidence -> không dùng.

Câu out_of_domain không chấm 4 metric; chỉ ghi có safe refusal hay không.

Chạy:  python -m src.evaluation         (resume được: câu đã chấm được bỏ qua)
Ghi:   group_project/evaluation/results.json
"""

import asyncio
import json
import math
import os
import threading
import time
from collections import deque
from functools import partial

from dotenv import load_dotenv

from . import task10_generation as generation
from .golden_dataset import OUTPUT_FILE as GOLDEN_FILE
from .golden_dataset import context_overlap_precision, context_overlap_recall
from .task4_chunking_indexing import QUERY_PREFIX, embed_texts
from .task5_semantic_search import semantic_search
from .task9_retrieval_pipeline import retrieve


load_dotenv()

RESULTS_FILE = GOLDEN_FILE.parent / "results.json"
TOP_K = 5
CONFIGS = {"A": False, "B": True}  # config -> use_reranking
REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
# ragas mặc định 3 câu hỏi sinh ngược; 1 để vừa quota free tier (~15 RPM).
ANSWER_RELEVANCY_STRICTNESS = 1
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL") or "gemini-3.1-flash-lite"

# Quota free tier tính theo model -> evaluator có cửa sổ rate limit riêng với generator.
_evaluator_calls: deque[float] = deque()
_evaluator_lock = threading.Lock()


def _rate_limited_llm():
    """LLM ragas với limiter riêng (cùng LLM_RPM) và retry 429 như call_llm của Task 10."""
    from google import genai
    from ragas.llms import llm_factory

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    llm = llm_factory(EVALUATOR_MODEL, provider="google", client=client)
    # Client genai sync -> ragas không cho agenerate; chạy generate() trong thread.
    sync_generate = llm.generate

    async def agenerate(*args, **kwargs):
        for attempt in range(generation.LLM_MAX_RETRIES + 1):
            await asyncio.to_thread(generation._wait_for_rate_limit, _evaluator_calls, _evaluator_lock)
            try:
                return await asyncio.to_thread(sync_generate, *args, **kwargs)
            except Exception as error:
                # instructor bọc lỗi gốc -> nhận diện qua message. 503 = model quá tải tạm thời.
                message = str(error)
                retryable = generation._is_rate_limited(error) or any(
                    code in message for code in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")
                )
                if not retryable or attempt == generation.LLM_MAX_RETRIES:
                    raise
                print(f"[retry] evaluator {message[:40]}..., chờ {generation.RATE_LIMIT_COOLDOWN}s")
                await asyncio.sleep(generation.RATE_LIMIT_COOLDOWN)

    llm.agenerate = agenerate
    return llm


def _embeddings():
    """Answer relevancy so câu hỏi gốc với câu hỏi sinh ngược bằng embedding Task 4."""
    from ragas.embeddings.base import BaseRagasEmbedding

    class TaskEmbedding(BaseRagasEmbedding):
        def embed_text(self, text, **kwargs):
            return embed_texts([QUERY_PREFIX + text])[0]

        def embed_texts(self, texts, **kwargs):
            return embed_texts([QUERY_PREFIX + t for t in texts])

        async def aembed_text(self, text, **kwargs):
            return self.embed_text(text)

        async def aembed_texts(self, texts, **kwargs):
            return self.embed_texts(texts)

    return TaskEmbedding()


def _metrics():
    from ragas.metrics.collections import AnswerRelevancy, Faithfulness

    llm = _rate_limited_llm()
    return {
        "faithfulness": (Faithfulness(llm=llm), ("user_input", "response", "retrieved_contexts")),
        "answer_relevancy": (
            AnswerRelevancy(llm=llm, embeddings=_embeddings(), strictness=ANSWER_RELEVANCY_STRICTNESS),
            ("user_input", "response"),
        ),
    }


def _run_case(item: dict, use_reranking: bool, metrics: dict) -> dict:
    question = item["question"]
    # Dùng nguyên generate_with_citation (prompt, citation check, refusal) của Task 10,
    # chỉ thay retrieve để đổi config.
    generation.retrieve = partial(retrieve, use_reranking=use_reranking)
    start = time.perf_counter()
    result = generation.generate_with_citation(question, top_k=TOP_K)
    latency = time.perf_counter() - start

    # Context đưa vào LLM; sources bị bỏ khi refusal nên lấy lại để chấm retrieval.
    contexts = [c["content"] for c in retrieve(question, top_k=TOP_K, use_reranking=use_reranking)]
    row = {
        "answer": result["answer"],
        "refused": result["answer"] == REFUSAL,
        "retrieval_source": result["retrieval_source"],
        "best_dense_score": (semantic_search(question, 1) or [{"score": 0.0}])[0]["score"],
        "latency_s": round(latency, 2),
        "contexts": contexts,
        "complete": True,
    }
    if item["type"] == "out_of_domain":
        return row

    row["context_recall"] = context_overlap_recall(item["expected_context"], contexts)
    row["context_precision"] = context_overlap_precision(item["expected_context"], contexts)
    inputs = {
        "user_input": question,
        "response": result["answer"],
        "retrieved_contexts": contexts or [""],
        "reference": item["expected_answer"],
    }
    for name, (metric, fields) in metrics.items():
        try:
            score = asyncio.run(metric.ascore(**{f: inputs[f] for f in fields})).value
            row[name] = None if score is None or math.isnan(score) else float(score)
        except Exception as error:
            print(f"  {name} lỗi: {type(error).__name__}: {str(error)[:150]}")
            row[name] = None
            row["complete"] = False  # lần chạy sau sẽ chấm lại câu này
    return row


def main() -> None:
    golden = json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))
    results = json.loads(RESULTS_FILE.read_text(encoding="utf-8")) if RESULTS_FILE.exists() else {}
    metrics = _metrics()

    for config, use_reranking in CONFIGS.items():
        done = results.setdefault(config, {})
        for index, item in enumerate(golden):
            key = str(index)
            if done.get(key, {}).get("complete"):
                continue
            print(f"[{config}] {index + 1}/{len(golden)} {item['question'][:60]}")
            done[key] = {"question": item["question"], "type": item["type"], **_run_case(item, use_reranking, metrics)}
            # Lưu sau mỗi câu để mất mạng/quota vẫn chạy tiếp được.
            RESULTS_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {RESULTS_FILE}")


if __name__ == "__main__":
    main()

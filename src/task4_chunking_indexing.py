"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
# Chroma 1.5.x không đọc lại được HNSW index (>~1000 vector) nếu đường dẫn có ký tự
# non-ASCII (vd "Thực Chiến") -> đặt CHROMA_DIR trong .env tới thư mục ASCII.
CHROMA_DIR = Path(os.getenv("CHROMA_DIR") or Path(__file__).parent.parent / "chroma_db")

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "structure"  # legal theo Điều, news theo heading; fallback recursive

# Ranh giới section, thử lần lượt; pattern nào tách được >= 2 section thì dùng.
# Không pattern nào khớp (tài liệu không đúng cấu trúc dự kiến) -> recursive thường.
SECTION_PATTERNS = {
    "legal": [
        # "Điều 1." đầu dòng, chấp nhận "**Điều 1**", "## Điều 1"
        re.compile(r"(?m)^(?=[#* \t]*Điều\s+\d+)"),
        # PDF mất xuống dòng: "Điều N." ngay sau dấu kết câu, tránh cắt ở "theo Điều 5"
        re.compile(r"(?:(?<=[.:;] )|(?<=[.:;]\n))(?=\**Điều\s+\d+\s*\.)"),
    ],
    "news": [
        re.compile(r"(?m)^(?=#{1,3} )"),
    ],
}
# Section bắt đầu bằng mẫu này thì dòng đầu là tiêu đề, được lặp lại ở chunk con.
HEADING_START = {
    "legal": re.compile(r"[#* \t]*Điều\s+\d+"),
    "news": re.compile(r"#{1,3} "),
}
HEADING_MAX = 80

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER") or "sentence_transformers"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or "intfloat/multilingual-e5-small"
EMBEDDING_DIM = 384

# Họ model e5 yêu cầu prefix; thiếu prefix thì chất lượng retrieval giảm rõ.
# Task 5 embed query bằng embed_texts([QUERY_PREFIX + query]).
_IS_E5 = "e5" in EMBEDDING_MODEL.lower()
QUERY_PREFIX = "query: " if _IS_E5 else ""
PASSAGE_PREFIX = "passage: " if _IS_E5 else ""

COLLECTION_NAME = "rag_documents"


@lru_cache(maxsize=1)
def _sentence_transformer():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts; caller tự thêm QUERY_PREFIX/PASSAGE_PREFIX."""
    # ponytail: chỉ hỗ trợ sentence_transformers, thêm nhánh openai/gemini khi nhóm đổi provider
    if EMBEDDING_PROVIDER != "sentence_transformers":
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")
    vectors = _sentence_transformer().encode(
        texts, batch_size=32, normalize_embeddings=True
    )
    return vectors.tolist()


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        # NFC: PDF/DOCX hay ra NFD, làm regex "Điều" và BM25 không khớp với query gõ tay.
        content = unicodedata.normalize("NFC", path.read_text(encoding="utf-8"))
        if not content.strip():
            continue
        # Task 3 ghi header "# <title>" và "**Source:** <url>" cho news.
        title = re.search(r"^# (.+)$", content, re.MULTILINE)
        url = re.search(r"^\*\*Source:\*\*\s*(\S+)", content, re.MULTILINE)
        documents.append({
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": {
                "source": path.name,
                "title": title.group(1).strip() if title else path.stem,
                "doc_type": "legal" if "legal" in path.parts else "news",
                "url": url.group(1) if url else None,
            },
        })
    return documents


def _split_sections(text: str, doc_type: str) -> list[tuple[str, str]]:
    """Trả về [(heading, section)]; heading rỗng nếu không nhận ra cấu trúc."""
    for attempt, pattern in enumerate(SECTION_PATTERNS.get(doc_type, [])):
        parts = [p.strip() for p in pattern.split(text) if p.strip()]
        if len(parts) < 2:
            continue
        is_heading = HEADING_START[doc_type].match
        sections, pending = [], ""
        for part in parts:
            # Section chỉ có dòng tiêu đề (vd "## Tham khảo" rỗng) -> gộp vào section sau.
            # Không áp dụng cho pattern fallback: text mất xuống dòng nên part nào cũng 1 dòng.
            if attempt == 0 and "\n" not in part and len(part) <= HEADING_MAX and is_heading(part):
                pending += part + "\n"
                continue
            part = pending + part
            pending = ""
            heading = part.split("\n", 1)[0].strip("#* \t")[:HEADING_MAX]
            sections.append((heading if is_heading(part) else "", part))
        if pending:
            sections.append(("", pending.strip()))
        return sections
    return [("", text)]


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia theo cấu trúc (Điều / heading), section dài thì recursive và lặp lại heading."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    chunks = []
    for document in documents:
        texts = []
        for heading, section in _split_sections(
            document["content"], document["metadata"]["doc_type"]
        ):
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE - len(heading) - 1,
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            pieces = [p for p in splitter.split_text(section) if p.strip()]
            # Chunk con thứ 2 trở đi mất tiêu đề -> chèn lại để giữ ngữ cảnh.
            texts += pieces[:1] + [f"{heading}\n{p}" if heading else p for p in pieces[1:]]
        for index, text in enumerate(texts):
            chunks.append({
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {**document["metadata"], "chunk_index": index},
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    vectors = embed_texts([PASSAGE_PREFIX + chunk["content"] for chunk in chunks])
    return [{**chunk, "embedding": vector} for chunk, vector in zip(chunks, vectors)]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB và xoá chunk cũ không còn tồn tại."""
    collection = get_collection()
    new_ids = {chunk["id"] for chunk in chunks}
    stale = [i for i in collection.get(include=[])["ids"] if i not in new_ids]
    if stale:
        collection.delete(ids=stale)
    if not chunks:
        return
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks from {len(documents)} documents")


if __name__ == "__main__":
    run_pipeline()

"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re
import unicodedata


CORPUS: list[dict] = []


def tokenize(text: str) -> list[str]:
    """Tách âm tiết, bỏ dấu câu; NFC để PDF (thường NFD) khớp với query gõ tay."""
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).lower())


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    tokenized = [tokenize(item["content"]) for item in corpus]
    return BM25Okapi(tokenized)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []

    if not CORPUS:
        from .task4_chunking_indexing import get_collection

        stored = get_collection().get(include=["documents", "metadatas"])
        CORPUS.extend(
            {
                "id": item_id,
                "content": content,
                "metadata": metadata,
            }
            for item_id, content, metadata in zip(
                stored["ids"],
                stored["documents"],
                stored["metadatas"],
            )
        )

    query_tokens = tokenize(query)
    if not CORPUS or not query_tokens:
        return []

    bm25 = build_bm25_index(CORPUS)
    scores = bm25.get_scores(query_tokens)
    indices = sorted(
        range(len(CORPUS)),
        key=lambda index: float(scores[index]),
        reverse=True,
    )

    results = []
    seen_ids = set()
    query_terms = set(query_tokens)
    for index in indices:
        item = CORPUS[index]
        if item["id"] in seen_ids:
            continue
        # BM25Okapi có thể trả 0 cho term xuất hiện trong đúng nửa corpus nhỏ.
        # Vẫn giữ document khớp từ khoá, nhưng bỏ document hoàn toàn không khớp.
        if query_terms.isdisjoint(tokenize(item["content"])):
            continue
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
        seen_ids.add(item["id"])
        if len(results) == top_k:
            break
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)

"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import QUERY_PREFIX, embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []

    query_vector = embed_texts([QUERY_PREFIX + query])[0]
    response = get_collection().query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    results_by_id = {}
    for item_id, content, metadata, distance in zip(
        response["ids"][0],
        response["documents"][0],
        response["metadatas"][0],
        response["distances"][0],
    ):
        result = {
            "id": item_id,
            "content": content,
            "score": max(0.0, 1.0 - distance),
            "metadata": metadata,
            "retrieval_method": "dense",
        }
        previous = results_by_id.get(item_id)
        if previous is None or result["score"] > previous["score"]:
            results_by_id[item_id] = result

    return sorted(
        results_by_id.values(),
        key=lambda item: item["score"],
        reverse=True,
    )[:top_k]


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)

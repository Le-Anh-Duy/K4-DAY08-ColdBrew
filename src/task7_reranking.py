"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Dùng Jina hoặc self host hoặc bất cứ công cụ nào bạn quen
"""


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult."""
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            scores[item["id"]] = scores.get(item["id"], 0.0) + 1 / (k + rank)
            items.setdefault(item["id"], item)

    # sorted ổn định: hoà điểm thì giữ thứ tự xuất hiện (list đầu tiên ưu tiên).
    ranked_ids = sorted(scores, key=scores.get, reverse=True)[:max(top_k, 0)]
    return [
        {**items[i], "score": scores[i], "retrieval_method": "hybrid"}
        for i in ranked_ids
    ]


if __name__ == "__main__":
    def _r(i, method):
        return {"id": i, "content": i, "score": 0.0, "metadata": {}, "retrieval_method": method}

    dense = [_r("a", "dense"), _r("b", "dense")]
    bm25 = [_r("b", "bm25"), _r("c", "bm25")]
    fused = rerank_rrf([dense, bm25], top_k=3)
    assert [r["id"] for r in fused] == ["b", "a", "c"]
    assert fused[0]["score"] == 1 / 62 + 1 / 61
    assert dense[0]["retrieval_method"] == "dense"  # input không bị sửa
    assert rerank_rrf([dense, bm25], top_k=0) == []
    print("OK", [(r["id"], round(r["score"], 5)) for r in fused])

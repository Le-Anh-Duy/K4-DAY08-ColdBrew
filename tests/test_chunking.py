from src.contracts import validate_document
from src.task4_chunking_indexing import CHUNK_SIZE, chunk_documents


def doc(doc_id: str, doc_type: str, content: str) -> dict:
    return {
        "id": doc_id,
        "content": content,
        "metadata": {"source": doc_id, "title": doc_id, "doc_type": doc_type, "url": None},
    }


def texts(document: dict) -> list[str]:
    chunks = chunk_documents([document])
    assert len({c["id"] for c in chunks}) == len(chunks)
    for index, chunk in enumerate(chunks):
        validate_document(chunk, require_chunk=True)
        assert chunk["metadata"]["chunk_index"] == index
        assert len(chunk["content"]) <= int(CHUNK_SIZE * 1.1)
    return [c["content"] for c in chunks]


def test_legal_splits_by_dieu_and_repeats_heading():
    out = texts(doc("nd110", "legal",
        "NGHỊ ĐỊNH 110/2018\n\n**Điều 1. Phạm vi điều chỉnh**\n"
        + "Nghị định này quy định về lễ hội. " * 30
        + "\n## Điều 2. Đối tượng áp dụng\nCơ quan, tổ chức theo Điều 1."))
    assert out[0].startswith("NGHỊ ĐỊNH")
    assert all("Điều 1. Phạm vi điều chỉnh" in t for t in out[1:-1])
    assert out[-1].startswith("## Điều 2")
    assert "theo Điều 1." in out[-1]  # tham chiếu trong câu không bị cắt


def test_legal_without_newlines_uses_sentence_fallback():
    flat = "LUẬT DI SẢN. Điều 1. Phạm vi. Luật quy định về di sản theo Điều 3. Điều 2. Giải thích từ ngữ. Di sản là tài sản."
    out = texts(doc("flat", "legal", flat))
    assert [t.split(".")[0] for t in out] == ["LUẬT DI SẢN", "Điều 1", "Điều 2"]


def test_news_splits_by_heading_and_merges_empty_heading():
    out = texts(doc("news", "news",
        "# Hội Gióng\n\n**Source:** https://x\n\nMở đầu.\n\n## Lịch sử\n"
        + "Thánh Gióng đánh giặc Ân. " * 40
        + "\n\n## Nghi lễ\n### Rước nước\nRước nước từ giếng đền."))
    assert out[0].startswith("# Hội Gióng")
    assert out[1].startswith("## Lịch sử") and out[2].startswith("Lịch sử\n")
    assert out[-1].startswith("## Nghi lễ\n### Rước nước\nRước nước")


def test_unstructured_or_unknown_type_falls_back_to_recursive():
    for document in (
        doc("plain", "legal", "Tuition policy. " * 100),
        doc("plain", "news", "Không có heading nào. " * 60),
        doc("plain", "other", "Loại tài liệu lạ. " * 60),
    ):
        assert len(texts(document)) > 1

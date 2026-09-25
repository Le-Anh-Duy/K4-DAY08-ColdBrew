import pytest

from src.golden_dataset import SPECS, build, context_overlap_recall


EVIDENCE = "2. Lễ hội truyền thống cấp tỉnh được tổ chức hàng năm phải thông báo với Ủy ban nhân dân cùng cấp trước khi tổ chức lễ hội."


def test_full_recall_when_chunk_contains_evidence_despite_formatting():
    # Chunk có heading chèn thêm, xuống dòng khác, khoảng trắng kép (như PDF).
    chunk = "Điều 14. Thông báo tổ chức lễ hội\n2.  Lễ hội truyền thống cấp tỉnh được tổ chức\nhàng năm phải thông báo với Ủy ban nhân dân cùng cấp trước khi tổ chức lễ hội. 3. Khác"
    assert context_overlap_recall([EVIDENCE], [chunk]) == 1.0


def test_partial_recall_when_evidence_split_across_chunks():
    first, second = EVIDENCE[:60], EVIDENCE[60:]
    half = context_overlap_recall([EVIDENCE], [first])
    assert 0.3 < half < 0.7
    assert context_overlap_recall([EVIDENCE], [first, second]) == pytest.approx(1.0, abs=0.05)


def test_scattered_common_words_do_not_count():
    unrelated = "Lễ hội văn hóa được tổ chức tại tỉnh. Ủy ban nhân dân ban hành."
    assert context_overlap_recall([EVIDENCE], [unrelated]) < 0.2
    assert context_overlap_recall([EVIDENCE], []) == 0.0


def test_golden_dataset_builds_from_standardized_files():
    data = build()
    assert len(data) == len(SPECS) >= 15
    for item in data:
        assert item["question"] and item["expected_answer"] and item["expected_context"]
        if item["type"] != "out_of_domain":
            assert item["evidence"]

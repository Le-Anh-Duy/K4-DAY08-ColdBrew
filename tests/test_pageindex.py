import json
import threading
import time

import pytest

import src.task8_pageindex_vectorless as pi
from src.contracts import validate_search_results


class FakeClient:
    """Giả lập PageIndex: submit_query -> retrieval_id, get_retrieval -> nodes."""

    def __init__(self, behaviour):
        self.behaviour = behaviour  # doc_id -> "ok" | "error" | "hang"

    def submit_query(self, doc_id, query):
        if self.behaviour[doc_id] == "error":
            raise RuntimeError("provider down")
        return {"retrieval_id": doc_id}

    def get_retrieval(self, retrieval_id):
        if self.behaviour[retrieval_id] == "hang":
            threading.Event().wait(5)  # treo lâu hơn SEARCH_TIMEOUT
        return {
            "status": "completed",
            "retrieved_nodes": [
                {"title": "Điều 2. Đăng ký", "node_id": "0002",
                 "relevant_contents": [{"page_index": 2, "relevant_content": "Đăng ký trước 45 ngày."}]},
                {"title": "Điều 3. Cấm", "node_id": "0003",
                 "relevant_contents": [{"page_index": 3, "relevant_content": "Cấm rải tiền lẻ."}]},
            ],
        }


@pytest.fixture
def setup(monkeypatch, tmp_path):
    def configure(behaviour):
        ids_file = tmp_path / "ids.json"
        ids_file.write_text(json.dumps({f"{d}.md": d for d in behaviour}), encoding="utf-8")
        monkeypatch.setattr(pi, "DOC_IDS_FILE", ids_file)
        monkeypatch.setattr(pi, "PAGEINDEX_API_KEY", "test")
        monkeypatch.setattr(pi, "SEARCH_TIMEOUT", 1)
        monkeypatch.setattr(pi, "_client", lambda: FakeClient(behaviour))
    return configure


def test_parses_nodes_into_contract(setup):
    setup({"nd110": "ok"})
    out = pi.pageindex_search("đăng ký", top_k=5)
    validate_search_results(out, top_k=5, expected_method="pageindex")
    assert out[0]["content"] == "Đăng ký trước 45 ngày."
    assert out[0]["metadata"]["source"] == "nd110.md"
    assert out[0]["metadata"]["title"] == "Điều 2. Đăng ký"


def test_failing_or_hanging_document_does_not_block_others(setup):
    setup({"good": "ok", "bad": "error", "slow": "hang"})
    start = time.monotonic()
    out = pi.pageindex_search("đăng ký", top_k=5)
    assert time.monotonic() - start < 3  # không chờ document bị treo
    assert {r["metadata"]["source"] for r in out} == {"good.md"}


def test_no_key_or_no_documents_returns_empty(setup, monkeypatch):
    setup({"nd110": "ok"})
    monkeypatch.setattr(pi, "PAGEINDEX_API_KEY", "")
    assert pi.pageindex_search("x") == []
    monkeypatch.setattr(pi, "PAGEINDEX_API_KEY", "test")
    assert pi.pageindex_search("x", top_k=0) == []

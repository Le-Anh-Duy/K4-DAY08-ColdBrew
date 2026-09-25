"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
LEGAL_PDF_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
DOC_IDS_FILE = Path(__file__).parent.parent / "pageindex_doc_ids.json"

SEARCH_TIMEOUT = 30  # giây cho cả lần fallback; SDK không có timeout riêng
POLL_INTERVAL = 2


def _client():
    from pageindex import PageIndexClient

    return PageIndexClient(PAGEINDEX_API_KEY)


def _load_doc_ids() -> dict[str, str]:
    if not DOC_IDS_FILE.exists():
        return {}
    return json.loads(DOC_IDS_FILE.read_text(encoding="utf-8"))


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    # ponytail: chỉ upload PDF legal gốc (PageIndex chỉ nhận PDF). News/DOCX
    # đã có dense + BM25; cần thì convert standardized .md sang PDF rồi thêm vào đây.
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("Thiếu PAGEINDEX_API_KEY trong .env")
    client = _client()
    doc_ids = _load_doc_ids()
    for pdf in sorted(LEGAL_PDF_DIR.glob("*.pdf")):
        # Key = tên file standardized để citation khớp metadata.source của Task 4.
        source = f"{pdf.stem}.md"
        if source in doc_ids:
            continue
        doc_ids[source] = client.submit_document(str(pdf))["doc_id"]
        DOC_IDS_FILE.write_text(json.dumps(doc_ids, indent=2), encoding="utf-8")
        print(f"Uploaded: {pdf.name} -> {doc_ids[source]}")
    print(f"{len(doc_ids)} documents in {DOC_IDS_FILE.name}")


def _query_one(client, doc_id: str, query: str, deadline: float) -> list[dict]:
    """Submit query cho 1 document rồi poll tới khi xong hoặc hết giờ."""
    retrieval_id = client.submit_query(doc_id, query)["retrieval_id"]
    while time.monotonic() < deadline:
        response = client.get_retrieval(retrieval_id)
        status = response.get("status")
        if status == "completed":
            return response.get("retrieved_nodes") or []
        if status == "failed":
            return []
        time.sleep(POLL_INTERVAL)
    return []


def _node_text(node: dict) -> str:
    contents = node.get("relevant_contents") or []
    text = "\n".join(
        c.get("relevant_content", "") if isinstance(c, dict) else str(c) for c in contents
    )
    return (text or node.get("text") or "").strip()


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    doc_ids = _load_doc_ids()
    if top_k <= 0 or not PAGEINDEX_API_KEY or not doc_ids:
        return []

    client = _client()
    deadline = time.monotonic() + SEARCH_TIMEOUT
    # Query song song mọi document; không dùng "with" để không chờ thread bị treo.
    pool = ThreadPoolExecutor(max_workers=min(8, len(doc_ids)))
    futures = {
        pool.submit(_query_one, client, doc_id, query, deadline): source
        for source, doc_id in doc_ids.items()
    }
    # +1s cho vòng poll cuối; request HTTP treo thì bỏ qua document đó.
    wait(futures, timeout=max(0.0, deadline - time.monotonic()) + 1)
    pool.shutdown(wait=False, cancel_futures=True)

    results = []
    for future, source in futures.items():
        if not future.done() or future.exception():
            continue
        for rank, node in enumerate(future.result(), 1):
            content = _node_text(node)
            if not content:
                continue
            node_id = node.get("node_id") or str(rank)
            results.append({
                "id": f"pageindex::{source}::{node_id}",
                "content": content,
                # API không trả score -> gán theo rank trong từng document.
                "score": 1.0 / rank,
                "metadata": {
                    "source": source,
                    "title": node.get("title") or Path(source).stem,
                    "doc_type": "legal",
                    "url": None,
                    "chunk_index": rank - 1,
                },
                "retrieval_method": "pageindex",
            })

    unique = {item["id"]: item for item in results}
    return sorted(unique.values(), key=lambda item: item["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    upload_documents()

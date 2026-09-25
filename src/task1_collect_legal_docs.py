"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

import time
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Chủ đề: Văn hóa và lễ hội. Ưu tiên bản Công báo (PDF có text, không phải bản scan).
# Task 3 dùng title/url ở đây làm header để citation hiển thị tên văn bản và link gốc.
SOURCES = {
    "luat-di-san-van-hoa-45-2024-phan-1.pdf": {
        "title": "Luật Di sản văn hóa số 45/2024/QH15 (Chương I–IV)",
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/01/luat45.pdf",
    },
    "luat-di-san-van-hoa-45-2024-phan-2.pdf": {
        "title": "Luật Di sản văn hóa số 45/2024/QH15 (Chương V trở đi)",
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/01/luat45_tiep.pdf",
    },
    "nghi-dinh-110-2018-quan-ly-to-chuc-le-hoi.pdf": {
        "title": "Nghị định 110/2018/NĐ-CP quy định về quản lý và tổ chức lễ hội",
        "url": "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2018/8/27216/23652-1-2018903-904110-2018-nd-cp.pdf",
    },
    "thong-tu-04-2011-nep-song-van-minh-cuoi-tang-le-hoi.pdf": {
        "title": "Thông tư 04/2011/TT-BVHTTDL về nếp sống văn minh trong việc cưới, việc tang và lễ hội",
        "url": "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2011/1/7857/4308-1-2011109-110-042011tt-bvhttdlpdf",
    },
    "thong-tu-04-2023-thu-chi-le-hoi-tien-cong-duc.pdf": {
        "title": "Thông tư 04/2023/TT-BTC hướng dẫn quản lý, thu chi tài chính cho tổ chức lễ hội và tiền công đức",
        # Bản Công báo 357+358 tải tay; trang vanban.chinhphu.vn chỉ có link bản ký số.
        "url": "https://vanban.chinhphu.vn/?pageid=27160&docid=207374",
    },
    "nghi-dinh-208-2025-quy-hoach-tu-bo-di-tich.docx": {
        "title": "Nghị định 208/2025/NĐ-CP về quy hoạch khảo cổ, bảo quản, tu bổ, phục hồi di tích",
        # DOCX tải tay; trang gốc chỉ có bản PDF ký số.
        "url": "https://vanban.chinhphu.vn/?docid=214676&pageid=27160",
    },
}

# File thật bắt đầu bằng magic bytes; trang HTML (link tải tay) thì không.
_MAGIC = {".pdf": b"%PDF", ".docx": b"PK"}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def _download(url: str, retries: int = 3) -> bytes:
    import requests

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url, timeout=60, headers={"User-Agent": "Mozilla/5.0"}
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(5 * attempt)
    raise AssertionError("unreachable")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    missing = []
    for filename, source in SOURCES.items():
        path = DATA_DIR / filename
        if path.exists():
            print(f"Skip (đã có): {filename}")
            continue
        try:
            content = _download(source["url"])
        except Exception as error:
            print(f"Failed: {filename} — {error}")
            missing.append(filename)
            continue
        if not content.startswith(_MAGIC[path.suffix.lower()]):
            print(f"Không phải file {path.suffix}: {filename} — tải tay từ {source['url']}")
            missing.append(filename)
            continue
        path.write_bytes(content)
        print(f"Saved: {filename} ({len(content) // 1024} KB)")
    if missing:
        print(f"Còn thiếu {len(missing)} file: {missing}")


if __name__ == "__main__":
    setup_directory()
    download_documents()

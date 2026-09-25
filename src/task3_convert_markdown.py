"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import re
import unicodedata
from pathlib import Path

from .task1_collect_legal_docs import SOURCES


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Header lặp lại mỗi trang của bản Công báo, vd "20 CÔNG BÁO/Số 903 + 904/Ngày 09-9-2018".
_CONG_BAO_HEADER = re.compile(r"(?m)^[ \t\f]*(\d+[ \t]+)?CÔNG BÁO/Số[^\n]*\n?")


def _clean_stale(output_dir: Path) -> None:
    """Xoá .md cũ để file đã đổi tên/xoá ở landing không còn sót lại."""
    for old in output_dir.glob("*.md"):
        old.unlink()


def convert_legal_docs() -> None:
    # TODO:Convert PDF/DOCX vào standardized/legal. 
    #
    from markitdown import MarkItDown
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    _clean_stale(output_dir)

    converter = MarkItDown()
    valid_extensions = {".pdf", ".doc", ".docx"}

    for path in sorted(legal_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in valid_extensions:
            try:
                result = converter.convert(str(path))
            except Exception as error:
                print(f"Failed legal: {path.name} — {error}")
                continue
            content = unicodedata.normalize("NFC", result.text_content or "")
            content = _CONG_BAO_HEADER.sub("", content).strip()

            # Bỏ qua không tạo file nếu nội dung rỗng (vd PDF scan không có text)
            if not content:
                print(f"Skip legal (không có text): {path.name}")
                continue

            # Cùng format header với news để Task 4 lấy được title/url cho citation.
            source = SOURCES.get(path.name, {})
            header = f"# {source.get('title', path.stem)}\n\n"
            if source.get("url"):
                header += f"**Source:** {source['url']}\n\n"
            (output_dir / f"{path.stem}.md").write_text(
                header + "---\n\n" + content, encoding="utf-8"
            )
            print(f"Saved legal: {path.stem}.md")
    # raise NotImplementedError("Implement convert_legal_docs")


def convert_news_articles() -> None:
    # TODO: Convert JSON vào standardized/news.
    #
    import json
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    _clean_stale(output_dir)
    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n---\n\n"
        )
        (output_dir / f"{path.stem}.md").write_text(
            unicodedata.normalize("NFC", header + data["content_markdown"]),
            encoding="utf-8",
        )
    # raise NotImplementedError("Implement convert_news_articles")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()

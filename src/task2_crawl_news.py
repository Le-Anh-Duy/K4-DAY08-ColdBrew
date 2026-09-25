"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

from playwright.async_api import async_playwright
import asyncio
import json
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md

import sys
import os

# Ép console trên Windows dùng UTF-8 để không bị lỗi 'charmap'
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    os.environ["PYTHONIOENCODING"] = "utf-8"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    # TODO: Thêm ít nhất 5 public URL.
    "https://dsvh.gov.vn/hoi-giong-o-den-phu-dong-va-den-soc-486",
    "https://ich.unesco.org/en/RL/worship-of-hung-kings-in-phu-th-00735",
    "https://ich.unesco.org/en/RL/festival-of-ba-chua-xu-goddess-at-sam-mountain-01999",
    "https://vietnam.travel/vi/things-to-do/tet-tradition-reunion-taste",
    "https://dsvh.gov.vn/danh-muc-di-san-van-hoa-phi-vat-the-quoc-gia-1789",
    # Bổ sung nguồn tiếng Việt (BM25 không khớp query tiếng Việt với bài UNESCO tiếng Anh).
    "https://dsvh.gov.vn/thuc-hanh-tin-nguong-tho-mau-tam-phu-cua-nguoi-viet-tro-thanh-di-san-van-hoa-phi-vat-the-dai-dien-cua-nhan-loai-1536",
    "https://dsvh.gov.vn/di-san-le-hoi-via-ba-chua-xu-nui-sam-duoc-unesco-ghi-danh-vao-danh-sach-di-san-van-hoa-phi-vat-the-dai-dien-cua-nhan-loai-22193",
    "https://dsvh.gov.vn/di-tich-lich-su-den-hung-2939",
    "https://dsvh.gov.vn/nghi-le-chau-van-cua-nguoi-viet-3150",
    "https://bvhttdl.gov.vn/ao-dai-viet-nam-bieu-tuong-van-hoa-truyen-thong-bac-nhip-cau-ra-nam-chau-202508051430158.htm",
]


async def crawl_article(url: str) -> dict:
    # TODO: Implement crawling logic.
    #
    

    from datetime import datetime
    from crawl4ai import AsyncWebCrawler
    
    # async with AsyncWebCrawler() as crawler:
    #     result = await crawler.arun(url=url)
    #     return {
    #         "url": url,
    #         "title": result.metadata.get("title", "Unknown"),
    #         "date_crawled": datetime.now().isoformat(),
    #         "content_markdown": result.markdown,
    #     }
    # raise NotImplementedError("Implement crawl_article")

    async with httpx.AsyncClient(
        headers=HEADERS, 
        follow_redirects=True, 
        timeout=30.0,
        verify=False  # Bỏ qua lỗi SSL nếu có trang chứng chỉ lỗi thời
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    # Dùng BeautifulSoup để phân tích HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # 1. Trích xuất Title (Thử thẻ meta trước, sau đó tới thẻ <title> hoặc <h1>)
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"]
    elif soup.title and soup.title.string:
        title = soup.title.string
    elif soup.find("h1"):
        title = soup.find("h1").get_text()
    else:
        title = "Unknown"

    # 2. Xóa bớt các thẻ rác không chứa nội dung chính
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        tag.decompose()

    # Thân bài = khối có nhiều <p> con trực tiếp nhất. dsvh.gov.vn/bvhttdl.gov.vn không
    # có <article>/<main>, và div "content" đầu tiên chứa cả menu điều hướng.
    blocks = soup.find_all(["article", "main", "section", "div"])
    best = max(blocks, key=lambda b: len(b.find_all("p", recursive=False)), default=None)
    if best is not None and len(best.find_all("p", recursive=False)) >= 3:
        main_content = best
    else:
        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_=lambda c: c and any(k in c.lower() for k in ["content", "detail", "post", "article"]))
            or soup.body
            or soup
        )

    # 3. Chuyển đổi HTML sang định dạng Markdown
    content_markdown = md(
        str(main_content),
        heading_style="ATX",
        strip=["a", "img"]  # Giữ lại văn bản sạch
    ).strip()

    return {
        "url": url,
        "title": title.strip(),
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": content_markdown,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")



if __name__ == "__main__":
    asyncio.run(crawl_all())

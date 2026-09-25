"""
Backend Server for Vite React Web UI.
Serves API endpoints on http://127.0.0.1:8000:
  - GET  /api/documents: List all legal & news documents with metadata
  - GET  /api/pdf/{filename}: Stream PDF files directly for browser viewer
  - GET  /api/content/{doc_type}/{filename}: Document preview content
  - POST /api/chat: RAG retrieval & generation using functions from src/
"""

import json
import mimetypes
import os
import urllib.parse
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
LANDING_LEGAL_DIR = DATA_DIR / "landing" / "legal"
LANDING_NEWS_DIR = DATA_DIR / "landing" / "news"
STANDARDIZED_LEGAL_DIR = DATA_DIR / "standardized" / "legal"
STANDARDIZED_NEWS_DIR = DATA_DIR / "standardized" / "news"


def get_all_documents():
    """Tổng hợp toàn bộ tài liệu pháp lý và bài viết di sản."""
    docs = []

    # 1. Legal documents (PDF, DOCX)
    if LANDING_LEGAL_DIR.exists():
        for path in sorted(LANDING_LEGAL_DIR.glob("*.*")):
            if path.name.startswith(".") or path.suffix.lower() not in {".pdf", ".docx", ".doc"}:
                continue
            std_md = STANDARDIZED_LEGAL_DIR / f"{path.stem}.md"
            word_count = len(std_md.read_text(encoding="utf-8").split()) if std_md.exists() else 0
            size_kb = round(path.stat().st_size / 1024, 1)

            docs.append({
                "id": path.name,
                "name": path.name,
                "stem": path.stem,
                "type": "legal",
                "format": path.suffix.lower().replace(".", "").upper(),
                "size_bytes": path.stat().st_size,
                "size_formatted": f"{size_kb} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB",
                "is_pdf": path.suffix.lower() == ".pdf",
                "pdf_url": f"/api/pdf/{urllib.parse.quote(path.name)}" if path.suffix.lower() == ".pdf" else None,
                "standardized_exists": std_md.exists(),
                "standardized_path": f"legal/{std_md.name}" if std_md.exists() else None,
                "word_count": word_count,
                "title": path.stem.replace("_", " ").replace("+", "&"),
                "category": "Văn bản quy phạm pháp luật / Quản lý lễ hội",
            })

    # 2. News articles (JSON)
    if LANDING_NEWS_DIR.exists():
        for path in sorted(LANDING_NEWS_DIR.glob("*.json")):
            if path.name.startswith("."):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
            std_md = STANDARDIZED_NEWS_DIR / f"{path.stem}.md"
            title = data.get("title") or path.stem
            size_kb = round(path.stat().st_size / 1024, 1)
            content_md = data.get("content_markdown", "")
            word_count = len(content_md.split()) if content_md else 0

            docs.append({
                "id": path.name,
                "name": path.name,
                "stem": path.stem,
                "type": "news",
                "format": "JSON",
                "size_bytes": path.stat().st_size,
                "size_formatted": f"{size_kb} KB",
                "is_pdf": False,
                "pdf_url": None,
                "url": data.get("url"),
                "date_crawled": data.get("date_crawled"),
                "standardized_exists": std_md.exists(),
                "standardized_path": f"news/{std_md.name}" if std_md.exists() else None,
                "word_count": word_count,
                "title": title,
                "category": "Di sản văn hóa phi vật thể / Lễ hội truyền thống",
            })

    return docs


async def api_documents(request: Request):
    docs = get_all_documents()
    stats = {
        "total_documents": len(docs),
        "legal_count": sum(1 for d in docs if d["type"] == "legal"),
        "news_count": sum(1 for d in docs if d["type"] == "news"),
        "pdf_count": sum(1 for d in docs if d["is_pdf"]),
        "standardized_count": sum(1 for d in docs if d["standardized_exists"]),
    }
    return JSONResponse({"stats": stats, "documents": docs})


async def api_pdf(request: Request):
    filename = urllib.parse.unquote(request.path_params["filename"])
    file_path = LANDING_LEGAL_DIR / filename
    if not file_path.exists():
        return Response("File not found", status_code=404)
    
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        media_type = "application/pdf"
        headers = {"Content-Disposition": f'inline; filename="{filename}"'}
    elif ext in {".docx", ".doc"}:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    else:
        media_type, _ = mimetypes.guess_type(str(file_path))
        headers = {"Content-Disposition": f'inline; filename="{filename}"'}

    return FileResponse(
        str(file_path),
        media_type=media_type or "application/octet-stream",
        headers=headers,
    )


async def api_content(request: Request):
    doc_type = request.path_params["doc_type"]
    filename = urllib.parse.unquote(request.path_params["filename"])

    if doc_type in {"legal", "news"}:
        md_path = DATA_DIR / "standardized" / doc_type / f"{Path(filename).stem}.md"
        if md_path.exists():
            return JSONResponse({
                "filename": filename,
                "type": doc_type,
                "content": md_path.read_text(encoding="utf-8"),
                "is_markdown": True,
            })
        if doc_type == "news":
            json_path = LANDING_NEWS_DIR / filename
            if json_path.exists():
                data = json.loads(json_path.read_text(encoding="utf-8"))
                return JSONResponse({
                    "filename": filename,
                    "type": doc_type,
                    "content": data.get("content_markdown", ""),
                    "metadata": data,
                    "is_markdown": True,
                })

    return JSONResponse({"error": "Content not found"}, status_code=404)


async def api_chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    query = (body.get("query") or "").strip()
    top_k = int(body.get("top_k") or 5)

    if not query:
        return JSONResponse({"error": "Query cannot be empty"}, status_code=400)

    sources = []
    retrieval_source = "hybrid"
    answer = ""

    # Call functions from src/ safely
    try:
        from src.task10_generation import generate_with_citation
        result = generate_with_citation(query, top_k=top_k)
        if isinstance(result, dict) and "answer" in result:
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            retrieval_source = result.get("retrieval_source", "hybrid")
    except Exception:
        try:
            from src.task9_retrieval_pipeline import retrieve
            sources = retrieve(query, top_k=top_k)
            retrieval_source = "hybrid"
        except Exception:
            try:
                from src.task6_lexical_search import lexical_search
                sources = lexical_search(query, top_k=top_k)
                retrieval_source = "bm25"
            except Exception:
                try:
                    from src.task5_semantic_search import semantic_search
                    sources = semantic_search(query, top_k=top_k)
                    retrieval_source = "dense"
                except Exception:
                    sources = []

    # Map sources and link to PDF where applicable
    mapped_sources = []
    for s in sources:
        meta = s.get("metadata", {})
        source_name = meta.get("source", "")
        pdf_name = None
        for p in LANDING_LEGAL_DIR.glob("*.pdf"):
            if p.stem in source_name or source_name in p.name:
                pdf_name = p.name
                break

        mapped_sources.append({
            "id": s.get("id"),
            "content": s.get("content"),
            "score": round(float(s.get("score", 0.0)), 4),
            "retrieval_method": s.get("retrieval_method", retrieval_source),
            "title": meta.get("title", source_name),
            "source": source_name,
            "doc_type": meta.get("doc_type", "unknown"),
            "url": meta.get("url"),
            "chunk_index": meta.get("chunk_index"),
            "pdf_name": pdf_name,
            "pdf_url": f"/api/pdf/{urllib.parse.quote(pdf_name)}" if pdf_name else None,
        })

    # Grounded synthesis if answer was not produced by LLM
    
    if not answer and mapped_sources:
        top_refs = [
            f"- **[{s['title']}]**: {s['content'][:260].strip()}..."
            for s in mapped_sources[:3]
        ]
        answer = (
            f"Dựa trên các tài liệu đã thu thập trong hệ thống, dưới đây là các thông tin liên quan nhất đến câu hỏi **\"{query}\"**:\n\n"
            + "\n\n".join(top_refs)
            + f"\n\n*(Hệ thống đã truy xuất thành công {len(mapped_sources)} đoạn ngữ cảnh từ nguồn tài liệu pháp lý và di sản văn hóa)*"
        )
    elif not answer:
        answer = f"Không tìm thấy đoạn ngữ cảnh liên quan trực tiếp đến câu hỏi **\"{query}\"** trong bộ tài liệu hiện tại."

    return JSONResponse({
        "query": query,
        "answer": answer,
        "sources": mapped_sources,
        "retrieval_source": retrieval_source,
    })


DIST_DIR = ROOT_DIR / "app" / "dist"


async def index(request: Request):
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        from starlette.responses import HTMLResponse
        return HTMLResponse(index_file.read_text(encoding="utf-8"))
    from starlette.responses import HTMLResponse
    return HTMLResponse("<h1>Di Sản AI API Server is running. Chạy frontend tại: cd app && npm run dev</h1>")


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

routes = [
    Route("/api/documents", endpoint=api_documents, methods=["GET"]),
    Route("/api/pdf/{filename:path}", endpoint=api_pdf, methods=["GET"]),
    Route("/api/file/{filename:path}", endpoint=api_pdf, methods=["GET"]),
    Route("/api/content/{doc_type}/{filename:path}", endpoint=api_content, methods=["GET"]),
    Route("/api/chat", endpoint=api_chat, methods=["POST"]),
    Route("/", endpoint=index, methods=["GET"]),
]

if (DIST_DIR / "assets").exists():
    routes.append(Mount("/assets", app=StaticFiles(directory=str(DIST_DIR / "assets")), name="assets"))

app = Starlette(routes=routes, middleware=middleware)


def run(host: str = "127.0.0.1", port: int = 8000):
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import uvicorn
    print("=" * 55)
    print(f"  [API SERVER] Di San AI Server running at http://{host}:{port}")
    print("=" * 55)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()

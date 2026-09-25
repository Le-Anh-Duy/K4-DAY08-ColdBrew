# Di Sản AI — RAG Chatbot về Văn hóa và lễ hội Việt Nam

**Nhóm ColdBrew** · Day 8 — RAG Pipeline · Thành viên: [TEAMMATES.md](TEAMMATES.md)

Chatbot trả lời câu hỏi về **phong tục, trang phục và lễ hội truyền thống Việt Nam** từ bộ tài liệu nhóm tự thu thập: văn bản pháp luật về di sản và lễ hội, cùng các bài viết của Cục Di sản văn hóa, Bộ VHTTDL và UNESCO. Mỗi câu trả lời có citation tới chunk nguồn. Câu hỏi ngoài phạm vi được từ chối an toàn.

## Kết quả chính

| | Dense-only (A) | Hybrid + RRF (B) |
|---|---:|---:|
| Faithfulness | 0.900 | 0.922 |
| Answer relevance | 0.872 | 0.866 |
| Context recall | 0.927 | 0.910 |
| Context precision | 0.881 | 0.904 |
| **Trung bình** | **0.895** | **0.900** |

Chấm trên 21 câu in-domain: faithfulness và relevance bằng ragas 0.4.3 (evaluator `gemini-3.1-flash-lite`), recall và precision bằng độ phủ evidence (không dùng LLM). Cả hai config từ chối đúng 3/3 câu ngoài phạm vi. Phân tích lỗi và khuyến nghị: [`group_project/evaluation/RESULT.md`](group_project/evaluation/RESULT.md).

## Dữ liệu

**Văn bản pháp lý** (`data/landing/legal/`, nguồn ghi trong `SOURCES` của `src/task1_collect_legal_docs.py`):

| Văn bản | Nội dung |
|---|---|
| Luật Di sản văn hóa 45/2024/QH15 (2 phần) | Định nghĩa di sản phi vật thể, loại hình, lễ hội truyền thống, hành vi bị cấm |
| Nghị định 110/2018/NĐ-CP | Quản lý và tổ chức lễ hội: đăng ký, thông báo, trách nhiệm người tham gia |
| Thông tư 04/2011/TT-BVHTTDL | Nếp sống văn minh trong việc cưới, việc tang và lễ hội |
| Thông tư 04/2023/TT-BTC | Thu chi tài chính lễ hội, tiền công đức |
| Nghị định 208/2025/NĐ-CP | Quy hoạch khảo cổ, bảo quản, tu bổ di tích |

**Bài viết** (`data/landing/news/`, 10 bài, URL trong `ARTICLE_URLS` của `src/task2_crawl_news.py`): Hội Gióng, Tín ngưỡng thờ Mẫu Tam phủ, Lễ hội Vía Bà Chúa Xứ núi Sam, Đền Hùng, Nghi lễ Chầu văn, Áo dài, Tết Nguyên Đán, Danh mục di sản phi vật thể quốc gia (dsvh.gov.vn, bvhttdl.gov.vn, ich.unesco.org, vietnam.travel).

## Kiến trúc

```
Task 1-3  PDF/DOCX + HTML ──► Markdown chuẩn hoá (NFC, header title/url, bỏ header Công báo)
Task 4    chunk theo cấu trúc (Điều / heading, 500 ký tự) ──► multilingual-e5-small ──► ChromaDB (cosine)
Task 5    dense search ─┐
Task 6    BM25 (chunk) ─┴► Task 7 RRF (k=60, fuse 1 lần) ──► Task 9 retrieve
                             cosine dense < 0.85 ──► Task 8 PageIndex fallback (lỗi thì giữ hybrid)
Task 10   Gemini + citation [chunk-id] đối chiếu với sources, không đủ evidence thì từ chối
UI        app.py (Streamlit) · server.py + app/ (Vite + React)
```

| Thành phần | Lựa chọn |
|---|---|
| Embedding | `intfloat/multilingual-e5-small` (CPU, 384 chiều, prefix `query:`/`passage:`) |
| Vector DB | ChromaDB, cosine, upsert idempotent |
| LLM | `gemini-3.5-flash-lite`, giới hạn 12 request/phút và thử lại khi gặp lỗi 429 |
| Fallback | `SCORE_THRESHOLD=0.85`, hiệu chỉnh trên golden set (in-domain ≥ 0.865, out-of-domain ≤ 0.836) |

## Cài đặt

Yêu cầu: Python 3.10–3.13, Node.js 18+ (cho UI).

```bash
python -m venv .venv
.venv\Scripts\activate                # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"              # hoặc: uv pip install -e ".[dev]"
cp .env.example .env
```

Điền `.env` (không commit file này):

```ini
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite
GEMINI_API_KEY=...
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=intfloat/multilingual-e5-small
SCORE_THRESHOLD=0.85
LLM_RPM=12                            # free tier Gemini ~15 RPM
EVALUATOR_MODEL=gemini-3.1-flash-lite # model chấm ragas (quota riêng)
PAGEINDEX_API_KEY=...                 # tuỳ chọn, key riêng của pageindex.ai (không phải key Gemini)
CHROMA_DIR=C:/Users/<you>/.chroma/k4-day08
```

> **`CHROMA_DIR` là bắt buộc nếu đường dẫn repo có dấu tiếng Việt** (vd `Vin AI Thực Chiến`). ChromaDB 1.5.x không đọc lại được HNSW index (trên khoảng 1000 vector) từ đường dẫn non-ASCII, lỗi sẽ là `Error loading hnsw index`.

## Chạy

```bash
# 1. Dữ liệu (đã có sẵn trong repo; chỉ cần chạy khi muốn tải/crawl lại)
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown

# 2. Index (lần đầu tải model e5-small ~470MB)
python -m src.task4_chunking_indexing

# 3. Kiểm tra
pytest -q
```

**Chatbot (Streamlit):**

```bash
streamlit run app.py
```

Mỗi câu trả lời có citation `[chunk-id]`. Mục "Nguồn đã dùng" liệt kê từng chunk: tiêu đề văn bản, ID (khớp với citation), phương thức retrieval, score và link gốc.

**Web UI (tuỳ chọn, cần Node.js):** gồm màn duyệt tài liệu và màn chat. Bấm vào nguồn thì mở văn bản PDF tương ứng.

```bash
python server.py                      # API tại http://127.0.0.1:8000
cd app && npm install && npm run dev  # UI tại http://localhost:5173
```

**Kiểm tra trước khi nộp:**

```bash
pytest tests/test_contracts.py -q
pytest tests/test_acceptance.py -q
pytest -q
```

Demo: một câu đúng phạm vi (vd *"Có được rải tiền trên đường đưa tang không?"*), một câu ngoài phạm vi (vd *"Làm sao để nấu phở bò ngon?"*, phải được từ chối) và kết quả A/B trong `RESULT.md`.

**Evaluation:**

```bash
python -m src.golden_dataset          # build lại golden set từ data/standardized
python -m src.evaluation              # A/B, ~20 phút với free tier; chạy lại sẽ tiếp tục từ câu còn thiếu
```

## Cấu trúc thư mục

```
src/task1..10_*.py        pipeline theo từng task (xem docs/MODULE_CONTRACTS.md)
src/golden_dataset.py     golden set (trích evidence nguyên văn) + context_overlap_recall
src/evaluation.py         evaluation A/B với ragas
app.py                    chatbot Streamlit
server.py, app/           API + giao diện web (Vite + React)
data/landing/             tài liệu gốc (PDF/DOCX, JSON)
data/standardized/        Markdown đã chuẩn hoá
group_project/evaluation/ golden_dataset.json, results.json, RESULT.md
reports/                  báo cáo cá nhân (K4-L3B-<MSSV>-<Ten>.md)
TEAMMATES.md              thành viên nhóm
tests/                    contract, acceptance và unit tests
```

## Hạn chế đã biết

- BM25 tách từ theo âm tiết nên hybrid có recall thấp hơn dense-only. Khuyến nghị thêm bigram và bỏ stopword (xem `RESULT.md`).
- `gemini-3.5-flash-lite` đôi khi từ chối dù context đã đủ thông tin (lỗi generation, không phải retrieval).
- PageIndex fallback chưa được kiểm chứng với API thật.
- Corpus chưa có mô tả chi tiết một số nghi thức (vd tắm Bà, rước kiệu ở Lễ hội Vía Bà Chúa Xứ). Với các câu hỏi này, hệ thống chỉ trả lời được phần thông tin chung.

## Tài liệu

- [Module contracts](docs/MODULE_CONTRACTS.md) · [Step-by-step](docs/STEP_BY_STEP.md) · [Grading rubric](docs/GRADING_RUBRIC.md) · [Template báo cáo cá nhân](reports/INDIVIDUAL_REPORT.md)

# Individual contribution report

## Thông tin

- Họ và tên: Lê Quang Thành
- Mã học viên: 2A202602647
- Nhóm: ColdBrew
- Repository/branch: https://github.com/Le-Anh-Duy/K4-L3B-RAG-Pipeline — `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 — tài liệu pháp lý | Thu thập bộ văn bản ban đầu: Luật Di sản văn hóa 45/2024 (phần tiếp theo), TT 04/2023/TT-BTC (bản Công báo), NĐ 208/2025/NĐ-CP | `data/landing/legal/` — `8b13f12` | Done |
| Task 2 — crawl bài viết | Crawler bằng `httpx` + BeautifulSoup + `markdownify` (không cần trình duyệt), lấy title từ `og:title`, bỏ thẻ script/nav/footer; 5 URL đầu tiên (dsvh.gov.vn, UNESCO, vietnam.travel) | `src/task2_crawl_news.py`, `data/landing/news/` — `8b13f12` | Done |
| Task 3 — chuẩn hoá | MarkItDown cho PDF/DOCX; header `# title` / `**Source:**` / `**Crawled:**` cho news; bỏ qua file rỗng | `src/task3_convert_markdown.py`, `data/standardized/` — `8b13f12` | Done |
| Web UI | Giao diện Vite + React: màn duyệt tài liệu (lọc, xem nội dung chuẩn hoá) và màn split view (trình xem PDF + khung chat, bấm nguồn để mở PDF tương ứng); API Starlette `/api/documents`, `/api/pdf`, `/api/content`, `/api/chat` gọi pipeline trong `src/` | `app/`, `server.py` — `000bbf3`, `a244496` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Crawl bằng `httpx` + BeautifulSoup + `markdownify` thay vì Crawl4AI/Playwright.
   **Lý do/evidence:** Các trang nguồn (dsvh.gov.vn, ich.unesco.org, vietnam.travel) là HTML tĩnh; không cần tải và chạy Chromium, crawl nhanh và ít phụ thuộc hơn (`8b13f12`).
   **Trade-off:** Không xử lý được trang render bằng JavaScript; heuristic chọn khối nội dung ban đầu còn lẫn menu điều hướng của dsvh.gov.vn (sau đó nhóm đổi sang chọn khối có nhiều `<p>` nhất, `ba51036`).

2. **Quyết định:** Làm web UI riêng (React + API Starlette) thay vì chỉ dùng Streamlit.
   **Lý do/evidence:** Cho phép xem song song văn bản PDF gốc và câu trả lời, bấm vào nguồn trích dẫn để mở đúng văn bản, giúp đối chiếu citation khi demo (`000bbf3`, `a244496`).
   **Trade-off:** Cần Node.js và chạy 2 tiến trình (API + Vite); thêm một lớp code phải giữ đồng bộ với contract của pipeline.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest tests/test_acceptance.py` cho số lượng và metadata dữ liệu; chạy thử UI với các câu gợi ý (tiền công đức, tín ngưỡng Hùng Vương, vía Bà Chúa Xứ, Nghị định 208).
- Kết quả trước/sau nếu có: bộ dữ liệu ban đầu có 4 văn bản pháp lý và 4 bài viết (URL thứ 5 crawl lỗi); nhóm bổ sung lên 6 văn bản và 10 bài để đạt yêu cầu ≥ 5 bài.
- Lỗi đã phát hiện và cách xử lý: UI chưa hoạt động đúng ở bản đầu → sửa `App.jsx` và `server.py` (`a244496`). Commit `000bbf3` vô tình thêm lại 4 file pháp lý dưới tên cũ (trùng từng byte với file đã đổi tên) → nhóm gỡ ở `23e71f2`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: khi `generate_with_citation` trả safe refusal, `/api/chat` gọi thẳng LLM với context mà không kiểm tra citation, nên trên web UI câu hỏi ngoài phạm vi vẫn có thể nhận câu trả lời thay vì bị từ chối; danh sách tài liệu mẫu trong `App.jsx` còn dùng tên file cũ.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: bỏ nhánh gọi LLM trực tiếp để `/api/chat` trả đúng `GenerationResult` của Task 10 (giữ safe refusal và citation đã kiểm tra), và lấy danh sách tài liệu hoàn toàn từ `/api/documents`.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Lê Quang Thành

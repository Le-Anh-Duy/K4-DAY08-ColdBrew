# 🏛️ Di Sản AI — Vite + React Web UI

Web UI giao diện hiện đại với phong cách Dark Mode Glassmorphism và hiệu ứng chuyển động mượt mà (animations).

## 🚀 Tính năng

1. **Màn 1: Tổng hợp tài liệu (`Document Explorer`)**:
   - Thống kê tổng số tài liệu, văn bản pháp lý (PDF/DOCX), bài viết di sản văn hóa, và các tệp Markdown đã chuẩn hoá.
   - Thanh tìm kiếm và bộ lọc nhanh theo danh mục (Tất cả / Pháp lý / Bài viết di sản).
   - Thẻ tài liệu hiển thị định dạng (PDF/DOCX/JSON), dung lượng, số từ, ngày thu thập.
   - Xem chi tiết nội dung văn bản qua cửa sổ trượt (Slide-over Drawer).
   - Nút **"Xem PDF"** chuyển ngay sang Màn 2 và tải văn bản tương ứng.

2. **Màn 2: Xem PDF & Khung Chat RAG (`Split View`)**:
   - **Cột trái (Trình xem PDF)**:
     - Menu chọn nhanh các văn bản pháp lý PDF trong kho dữ liệu.
     - Trình đọc PDF tích hợp trực tiếp trên trình duyệt với đầy đủ thanh công cụ zoom, in ấn, tìm kiếm văn bản.
     - Mở tệp trong tab mới hoặc tải về máy.
   - **Cột phải (Khung chat RAG)**:
     - Giao diện chat hiện đại với hiệu ứng gõ chữ và bóng chat người dùng/trợ lý.
     - Các gợi ý câu hỏi nhanh (tiền công đức, tín ngưỡng Hùng Vương, vía Bà Chúa Xứ, Nghị định 208).
     - Khối trích dẫn nguồn (Sources / Citations) có điểm tương đồng, phương thức tìm kiếm (hybrid/dense/bm25).
     - **Nút nhảy trực tiếp**: Bấm vào nguồn PDF trích dẫn để tự động chuyển tài liệu PDF ở cột bên trái.

## 🛠️ Hướng dẫn khởi chạy

### Bước 1: Khởi động API Server (Python backend)

Từ thư mục gốc dự án:
```bash
python server.py
# Hoặc: .venv\Scripts\python server.py
```
API server sẽ chạy tại `http://127.0.0.1:8000`.

### Bước 2: Khởi động giao diện Vite + React

Trong một cửa sổ terminal mới:
```bash
cd app
npm run dev
```
Giao diện sẽ chạy tại `http://localhost:5173`.
Mọi yêu cầu API `/api/*` sẽ được Vite tự động chuyển tiếp (proxy) sang server Python `http://127.0.0.1:8000`.

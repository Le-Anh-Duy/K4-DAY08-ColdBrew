# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Thị Phương Duyên
- Mã học viên: 2A202603001
- Nhóm: ColdBrew
- Repository/branch: https://github.com/Le-Anh-Duy/K4-L3B-RAG-Pipeline — `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 5 — semantic search | Embed query bằng `embed_texts([QUERY_PREFIX + query])` dùng chung với Task 4, query ChromaDB, đổi cosine distance thành `score = max(0, 1 − distance)`, loại ID trùng, sort giảm dần, cắt `top_k` | `src/task5_semantic_search.py` — `1368fc4` | Done |
| Task 6 — BM25 | `CORPUS` nạp từ ChromaDB (cùng ID chunk với dense để RRF gộp được), `BM25Okapi`, bỏ chunk không chứa từ nào của query, trả `SearchResult` với `retrieval_method="bm25"` | `src/task6_lexical_search.py` — `957a286` | Done |
| Task 10 — generation có citation | `reorder_for_llm` (đưa chunk quan trọng về đầu/cuối, không sửa input), `format_context` (nhãn Document, ID, Title, Source), `generate_with_citation` trả `GenerationResult` với safe refusal khi retrieve lỗi, không có chunk hoặc LLM lỗi | `src/task10_generation.py` — `4ee2871` | Done |
| Kiểm tra citation | Quy tắc citation `[chunk-id]` trong prompt; câu trả lời chỉ được trả về khi mọi citation khớp ID trong `sources`, ngược lại trả safe refusal | `src/task10_generation.py` — `b372db2` | Done |
| Nghiên cứu nguồn dữ liệu | Tìm kiếm, chọn và bàn giao cho nhóm các file văn bản pháp lý cùng URL bài viết công khai về văn hóa, di sản và lễ hội để đưa vào corpus; phần tải, crawl và chuẩn hóa được các thành viên phụ trách Task 1–3 tích hợp sau đó | `data/landing/legal/`, `data/landing/news/`, danh sách `SOURCES`/`ARTICLE_URLS` trong `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** BM25 dùng đúng tập chunk đã index trong ChromaDB thay vì tự chunk lại.
   **Lý do/evidence:** RRF ở Task 7 gộp theo `id`; lấy corpus từ `get_collection().get()` bảo đảm dense và BM25 cùng ID và metadata (`957a286`), contract test `test_lexical_search_returns_bm25_contract` pass.
   **Trade-off:** `CORPUS` được cache trong process, nên sau khi index lại phải khởi động lại app; BM25 index dựng lại ở mỗi truy vấn (chấp nhận được với khoảng 1500 chunk).

2. **Quyết định:** Kiểm tra citation chặt: mọi `[...]` trong câu trả lời phải là ID có trong `sources`, nếu không thì trả safe refusal.
   **Lý do/evidence:** Contract yêu cầu "citation phải đối chiếu được với phần tử trong `sources`"; cách này chặn citation bịa ID (`b372db2`). Kết quả evaluation chung của nhóm cho thấy 3/3 câu ngoài domain được từ chối ở cả hai config.
   **Trade-off:** Có thể góp phần gây từ chối sai nếu model dùng sai định dạng citation. Theo `RESULT.md`, câu #5 (bán vé lễ hội, config B) có evidence đầy đủ (recall 1.0) nhưng kết quả cuối vẫn là safe refusal; lần chạy 1 cũng có #1 và #15. Do chưa lưu answer thô trước bước kiểm tra citation, chưa thể kết luận lỗi đến từ model tự từ chối hay từ citation validator.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: contract test `test_semantic_search_uses_shared_embedding_and_contract`, `test_lexical_search_returns_bm25_contract`, `test_reorder_is_non_mutating_and_context_contains_source`, `test_generation_result_validator_accepts_safe_refusal`; query thử "Có được rải tiền trên đường đưa tang không?" trả lời đúng kèm citation `[legal/thong-tu-04-2011-...::chunk-...]`.
- Kết quả trước/sau nếu có: trước `b372db2`, câu trả lời có thể trích số Document hoặc ID không có trong sources; sau đó mọi câu trả lời được trả về đều có citation hợp lệ.
- Lỗi đã phát hiện và cách xử lý: Task 6 ban đầu do tôi triển khai dùng `split()`, khiến dấu câu dính vào từ ("Gióng?" không khớp "Gióng,"). Lỗi được phát hiện khi nhóm chạy evaluation; thành viên Lê Anh Duy bổ sung tokenizer `\w+` và chuẩn hoá NFC tại commit `4bace13`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: `SYSTEM_PROMPT` ngắn hoặc bước kiểm tra citation chặt có thể góp phần làm hệ thống từ chối dù context đủ thông tin; hiện chưa lưu answer thô trước validator nên chưa phân biệt được nguyên nhân. Kết quả cũng chưa ổn định giữa các lần chạy với temperature 0.3.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: viết lại prompt bằng tiếng Việt (cho phép trả lời một phần và nêu phần thiếu), chỉ xét nội dung trong ngoặc có dạng ID chunk (`::chunk-`), và ghi lại câu trả lời thô của LLM để phân biệt model tự từ chối với citation bị loại (khuyến nghị 1 trong `RESULT.md`).

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Nguyễn Thị Phương Duyên

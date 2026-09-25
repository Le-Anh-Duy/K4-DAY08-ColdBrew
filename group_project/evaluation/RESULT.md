# RAG evaluation results

Nhóm ColdBrew — chủ đề **Văn hóa và lễ hội** (phong tục, trang phục, lễ hội truyền thống).
Số liệu thô từng câu: [`results.json`](results.json) (lần chạy chính) và [`results_run1.json`](results_run1.json) (lần 1, xem cuối trang). Chạy lại: `python -m src.evaluation`.

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | ragas 0.4.3 (`ragas.metrics.collections`: Faithfulness, AnswerRelevancy) + `context_overlap_recall` / `context_overlap_precision` tự viết (`src/golden_dataset.py`, không gọi LLM) |
| Evaluator model                    | `gemini-3.1-flash-lite`: khác model generator để tránh tự chấm và có quota riêng; giới hạn 12 request/phút |
| Generator model                    | `gemini-3.5-flash-lite`, temperature 0.3, top_p 0.9 (`generate_with_citation`, Task 10) |
| Embedding model                    | `intfloat/multilingual-e5-small` (384 chiều, prefix `query:`/`passage:`) |
| Corpus version/commit              | Dữ liệu tại `23e71f2` (6 văn bản pháp lý + 10 bài viết); chunking tại `bae8193`: 1545 chunk theo Điều/heading, 500 ký tự, overlap 50 |
| Golden dataset size                | 24 câu: 12 legal, 7 news, 2 multi-doc, 3 out-of-domain. 4 metric chấm trên 21 câu in-domain |
| `top_k`                            | 5 (dense và BM25 mỗi bên lấy 10 ứng viên trước khi fuse/cắt) |
| Fallback threshold and calibration | `SCORE_THRESHOLD = 0.85` trên cosine dense gốc. Trên golden set, cosine cao nhất của câu in-domain thấp nhất là 0.865, của câu out-of-domain cao nhất là 0.836, nên ngưỡng 0.85 tách được toàn bộ 24 câu. 3/3 câu out-of-domain được safe refusal ở cả hai config |

Cách chấm:

- **Faithfulness, answer relevance:** ragas, LLM-as-judge. Câu bị từ chối được chấm 0 nên trung bình phản ánh cả tỉ lệ từ chối sai. `answer_relevancy` dùng `strictness=1` (mặc định ragas là 3) để vừa quota free tier.
- **Context recall:** tỉ lệ token của evidence (đoạn nguyên văn trong golden set) xuất hiện trong top 5, tính theo đoạn khớp liên tiếp ≥ 4 token.
- **Context precision:** average precision@5 như công thức ragas. Một chunk được coi là relevant nếu một mình nó phủ ≥ 20 token (hoặc nửa đoạn) evidence.
- Không dùng bản LLM của ragas cho recall/precision: mỗi câu tốn 6 request (precision gọi 1 lần cho mỗi chunk). Không dùng bản `NonLLM` (Levenshtein) của ragas vì nó so cả chunk với đoạn evidence ngắn hơn nhiều và cho 0 ngay cả khi chunk chứa trọn evidence (đã thử trên câu #1 và #7). Trên dữ liệu lần 1, overlap precision tương quan với LLM precision (r = 0.72 ở config A).

## Configurations

- **Config A — dense-only:** `retrieve(query, top_k=5, use_reranking=False)`: top 5 chunk theo cosine từ ChromaDB.
- **Config B — hybrid + RRF:** `retrieve(query, top_k=5, use_reranking=True)`: dense top 10 + BM25 top 10, fuse một lần bằng RRF (k=60), lấy top 5.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |    0.900 |    0.922 |    +0.022 |
| Answer relevance  |    0.872 |    0.866 |    −0.006 |
| Context recall    |    0.927 |    0.910 |    −0.018 |
| Context precision |    0.881 |    0.904 |    +0.023 |
| **Average**       |**0.895** |**0.900** |**+0.005** |

Faithfulness tính trên 20/21 câu mỗi config: ragas trả NaN khi không tách được statement (A #11, B #8).

| Chỉ số bổ sung                          | Config A | Config B |
| --------------------------------------- | -------: | -------: |
| Câu in-domain bị từ chối                | 2/21 (#20, #21) | 1/21 (#5) |
| Out-of-domain được từ chối              |      3/3 |      3/3 |
| Điểm trung bình nhóm multi-doc (4 metric) |    0.410 |    0.758 |
| Latency trung vị (giây)                 |     1.60 |     1.48 |

## A/B comparison

- **Cấu hình tốt hơn:** Config B (hybrid + RRF), nhưng chỉ hơn rất ít (average 0.900 so với 0.895). Với 21 câu, chênh lệch này nằm trong mức nhiễu. Nhóm chọn B làm mặc định vì B tốt hơn rõ ở câu nhiều ý và precision.
- **Evidence:**
  - **Câu multi-doc:** B trả lời được, A từ chối. Ở #21 (Chầu văn + Luật), B có faithfulness 0.83 và relevance 0.96, còn A từ chối. Điểm trung bình nhóm multi-doc là 0.758 (B) so với 0.410 (A). Hai config có cùng recall (0.63) nên khác biệt đến từ thứ tự và độ đa dạng của chunk đưa vào LLM.
  - **Precision tăng (+0.023):** BM25 đẩy chunk khớp từ khóa lên đầu. Ở #12 (tri thức trang phục), precision tăng từ 0.33 lên 1.00.
  - **Recall giảm (−0.018):** BM25 tách theo âm tiết nên các chunk dày chữ "lễ hội", "tổ chức" chen vào top 5. Ở #3 (thắp hương, vàng mã), recall giảm từ 0.96 xuống 0.59; ở #1, precision giảm từ 1.00 xuống 0.70.
- **Trade-off về latency/cost:** số lời gọi LLM như nhau (1 lần generate mỗi câu). BM25 chạy trong process, không tốn API. Latency trung vị gần như bằng nhau (1.48 giây với B, 1.60 giây với A). Latency trung bình (A 11.4 giây, B 6.4 giây) bị chi phối bởi thời gian chờ rate limiter và retry 429 nên không dùng để so sánh.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Theo Luật Di sản văn hóa 2024, lễ hội truyền thống được hiểu như thế nào? (#11) | B | 0.60 | 0.92 | 0.24 | 0.00 | retrieval | Định nghĩa "lễ hội truyền thống" ở NĐ 110 Điều 3 có cùng từ khóa nên xếp trên Luật 45 Điều 10 (cả dense và BM25). Model nói Luật không có định nghĩa rồi trả lời theo NĐ 110, tức sai nguồn so với câu hỏi. Config A cũng lỗi y hệt (recall 0.24, precision 0.00) |
|   2 | Tín ngưỡng thờ Mẫu Tam phủ thuộc loại hình di sản nào theo Luật 2024, và được UNESCO ghi danh năm nào? (#20, multi-doc) | A | 0.00 | 0.00 | 0.64 | 1.00 | retrieval | Top 5 chỉ gồm chunk của bài thờ Mẫu; đoạn Luật 45 Điều 10.3 không lọt vào, nên model từ chối cả câu. Ở B model trả lời được phần UNESCO nhưng relevance vẫn 0.00 vì thiếu nửa câu hỏi |
|   3 | Ban tổ chức có được bán vé vào dự lễ hội không? (#5) | B | 0.00 | 0.00 | 1.00 | 1.00 | generation | Retrieval hoàn hảo (đúng TT 04/2011 Điều 12) nhưng kết quả cuối là safe refusal. Config A trả lời đúng với cùng evidence. Generator không ổn định (temperature 0.3): ở lần chạy 1, câu #1 và #15 cũng bị từ chối sai dù evidence đủ |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Viết lại `SYSTEM_PROMPT` bằng tiếng Việt: trả lời khi context có thông tin liên quan kể cả khi cần diễn giải câu chữ; cho phép trả lời một phần và nêu phần thiếu; chỉ từ chối khi context không liên quan. Giảm temperature xuống 0 và ghi lại câu trả lời thô của LLM để biết nguyên nhân từ chối là do model tự từ chối hay do bước kiểm tra citation | #5 (B, lần 2), #1 và #15 (lần 1) bị từ chối dù recall 1.0; #20/#21 ở A từ chối cả câu thay vì trả lời phần có evidence | Giảm từ chối sai, tăng faithfulness/relevance, kết quả ổn định giữa các lần chạy | Chạy lại `python -m src.evaluation` 2 lần; số câu in-domain bị từ chối phải giảm và giống nhau giữa 2 lần, 3/3 câu out-of-domain vẫn được từ chối |
|        2 | BM25: thêm bigram âm tiết ("lễ_hội", "vàng_mã") và bỏ stopword tiếng Việt trong `tokenize` | #3 recall 0.96 → 0.59 và #1 precision 1.00 → 0.70 khi thêm BM25 | Hybrid không còn kém dense về recall, giữ lợi thế precision | So context recall của A và B bằng `context_overlap_recall`; không tốn lời gọi LLM |
|        3 | Câu hỏi nhiều ý: tách câu hỏi (query decomposition) hoặc đa dạng hóa nguồn trong top k (MMR / giới hạn số chunk mỗi tài liệu); ưu tiên văn bản được nêu tên trong câu hỏi ("Luật Di sản văn hóa 2024") | #20, #21 recall chỉ 0.63–0.64 vì top 5 dồn vào một bài; #11 lấy nhầm NĐ 110 thay vì Luật 45 | Recall câu multi-doc từ khoảng 0.64 lên gần 1.0; #11 lấy đúng văn bản | Context recall trên nhóm `multi_doc` và câu #11 |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Chưa thực hiện thí nghiệm bonus (HyDE, reranker nâng cao) | Config B | — | — | Ưu tiên khuyến nghị 1–2 trước vì lỗi hiện tại nằm ở prompt và tokenizer BM25 |

## Lịch sử: lần chạy 1 và thay đổi

Lần 1 (`results_run1.json`) chạy trên chunking cũ (1578 chunk, tiêu đề bài bị lặp vào mọi chunk con) và dùng chính generator làm evaluator, với cả 4 metric chấm bằng LLM:

| Metric | A (lần 1) | B (lần 1) |
| ------ | --------: | --------: |
| Faithfulness | 0.838 | 0.889 |
| Answer relevance | 0.827 | 0.817 |
| Context recall (LLM) | 0.952 | 0.889 |
| Context precision (LLM) | 0.810 | 0.843 |
| Average | 0.857 | 0.860 |

Giữa lần 1 và lần 2 có 3 thay đổi:

1. **Sửa chunking:** tiêu đề bài không còn bị lặp vào mọi chunk con. Trước đó cả 27 chunk của bài Bà Chúa Xứ mở đầu giống hệt nhau, nên tiêu đề lấn át nội dung khi xếp hạng.
2. **Đổi evaluator** sang model khác generator.
3. **Recall/precision tính bằng overlap** với evidence thay vì LLM.

Số liệu recall/precision của hai lần vì vậy không so trực tiếp được. Kết luận A/B giữ nguyên ở cả hai lần: B nhỉnh hơn A rất ít, từ chối sai ít hơn, precision cao hơn và recall thấp hơn do BM25.

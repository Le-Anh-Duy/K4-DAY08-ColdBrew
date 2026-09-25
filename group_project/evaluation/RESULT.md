# RAG evaluation results

Nhóm ColdBrew — chủ đề **Văn hóa và lễ hội** (phong tục, trang phục, lễ hội truyền thống).
Số liệu thô từng câu: [`results.json`](results.json). Chạy lại: `python -m src.evaluation`.

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | ragas 0.4.3 (`ragas.metrics.collections`) + `context_overlap_recall` tự viết (`src/golden_dataset.py`, không gọi LLM) |
| Evaluator model                    | `gemini-3.5-flash-lite` (qua instructor, giới hạn 12 RPM) |
| Generator model                    | `gemini-3.5-flash-lite`, temperature 0.3, top_p 0.9 (`generate_with_citation`, Task 10) |
| Embedding model                    | `intfloat/multilingual-e5-small` (384 chiều, prefix `query:`/`passage:`) |
| Corpus version/commit              | `23e71f2` — 6 văn bản pháp lý + 10 bài viết, 1578 chunk (chunk theo Điều/heading, 500 ký tự, overlap 50) |
| Golden dataset size                | 24 câu: 12 legal, 7 news, 2 multi-doc, 3 out-of-domain. 4 metric chấm trên 21 câu in-domain |
| `top_k`                            | 5 (dense và BM25 mỗi bên lấy 10 ứng viên trước khi fuse/cắt) |
| Fallback threshold and calibration | `SCORE_THRESHOLD = 0.85` trên cosine dense gốc. Trên golden set: cosine cao nhất của câu in-domain thấp nhất là 0.865, của câu out-of-domain cao nhất là 0.836 → 0.85 tách được toàn bộ 24 câu. 3/3 câu out-of-domain được safe refusal ở cả hai config |

Lưu ý khi đọc số liệu:

- Câu bị từ chối (safe refusal) được ragas chấm faithfulness/relevancy = 0, nên trung bình phản ánh cả tỉ lệ từ chối sai.
- `answer_relevancy` dùng `strictness=1` (mặc định ragas là 3) để vừa quota free tier.
- Evaluator và generator cùng một model nên có thể thiên vị theo hướng dễ dãi với câu trả lời của chính nó.

### Cập nhật sau evaluation: sửa chunking (chưa chấm lại ragas)

Sau lần chạy trên, nhóm phát hiện lỗi ở Task 4. Tiêu đề bài (`# ...`) bị lặp vào đầu mọi chunk con của các bài không có heading con. Ví dụ, cả 27 chunk của bài Lễ hội Vía Bà Chúa Xứ đều mở đầu bằng cùng một tiêu đề 80 ký tự, nên top 5 trông giống hệt nhau và tiêu đề lấn át nội dung khi xếp hạng. Bản sửa chỉ lặp heading của mục con (`##`, `###`) và "Điều N"; tiêu đề bài đã có trong `metadata.title`.

Đo lại phần không cần LLM trên cùng golden set:

| Chỉ số | Trước sửa | Sau sửa |
| ------ | --------: | ------: |
| Số chunk | 1578 | 1545 |
| Overlap recall — Config A | 0.933 | 0.927 |
| Overlap recall — Config B | 0.910 | 0.910 |
| Cosine in-domain thấp nhất / out-of-domain cao nhất | 0.865 / 0.836 | 0.865 / 0.836 |

Các chỉ số ragas bên dưới vẫn là số của bản chunking cũ (commit `23e71f2`). Top 5 sau khi sửa đa dạng hơn (không còn các chunk trùng phần đầu), còn overlap recall và ngưỡng fallback gần như không đổi.

## Configurations

- **Config A — dense-only:** `retrieve(query, top_k=5, use_reranking=False)` — top 5 chunk theo cosine từ ChromaDB.
- **Config B — hybrid + RRF:** `retrieve(query, top_k=5, use_reranking=True)` — dense top 10 + BM25 top 10, fuse một lần bằng RRF (k=60), lấy top 5.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |    0.838 |    0.889 |    +0.051 |
| Answer relevance  |    0.827 |    0.817 |    −0.010 |
| Context recall    |    0.952 |    0.889 |    −0.063 |
| Context precision |    0.810 |    0.843 |    +0.033 |
| **Average**       |**0.857** |**0.860** |**+0.003** |

Chỉ số bổ sung (21 câu in-domain):

| Chỉ số                                   | Config A | Config B |
| ---------------------------------------- | -------: | -------: |
| Overlap recall (evidence nằm trong top 5) |    0.933 |    0.910 |
| Số câu in-domain bị từ chối               |     3/21 |     1/21 |
| Out-of-domain được từ chối                |      3/3 |      3/3 |
| Latency trung bình / trung vị (giây)      | 6.02 / 1.83 | 7.12 / 3.27 |

## A/B comparison

- Cấu hình tốt hơn: **Config B (hybrid + RRF), nhưng chỉ nhỉnh hơn rất ít** (average 0.860 so với 0.857). Với 21 câu, chênh lệch này nằm trong mức nhiễu; nhóm giữ B làm mặc định vì từ chối sai ít hơn.
- Evidence:
  - B tăng faithfulness (+0.051) chủ yếu vì chỉ từ chối sai 1 câu thay vì 3. Ví dụ câu #15 (Lễ hội Bà Chúa Xứ): A từ chối dù context đúng (recall 1.0), còn B trả lời đúng (faithfulness 1.0).
  - B tăng context precision (+0.033): BM25 đẩy chunk khớp từ khóa lên đầu, vd câu #4 (đốt pháo, đèn trời) precision 0.50 → 1.00, câu #12 (tri thức trang phục) 0.33 → 0.70.
  - B giảm context recall (−0.063) và overlap recall (0.933 → 0.910): BM25 tách theo âm tiết nên các chunk dày chữ "lễ hội", "tổ chức" chen vào top 5. Câu #3 (thắp hương, vàng mã) overlap 0.96 → 0.59; câu #11 context recall 1.00 → 0.00.
- Trade-off về latency/cost: số lời gọi LLM như nhau (1 lần generate mỗi câu). B chậm hơn khoảng 1.4 giây ở trung vị do dựng lại BM25 index trên 1578 chunk mỗi truy vấn (latency đo được gồm cả thời gian chờ rate limiter nên trung bình bị đẩy lên).

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Nghi lễ Chầu văn thuộc lĩnh vực di sản nào, và Luật Di sản văn hóa 2024 mô tả lĩnh vực đó ra sao? (#21, multi-doc) | A | 0.00 | 0.00 | 0.50 | 0.00 | retrieval | Top 5 toàn chunk của bài Chầu văn; đoạn định nghĩa "tập quán xã hội và tín ngưỡng" (Luật 45, Điều 10) không lọt vào → model từ chối. Ở B model trả lời được nửa đầu và nói rõ thiếu nửa sau. |
|   2 | Theo Luật Di sản văn hóa 2024, lễ hội truyền thống được hiểu như thế nào? (#11) | B | 0.60 | 0.95 | 0.00 | 0.00 | retrieval | Định nghĩa "lễ hội truyền thống" ở NĐ 110 Điều 3 cùng từ khóa nên xếp trên Luật 45 Điều 10; BM25 khuếch đại thêm. Model trả lời theo NĐ 110, sai nguồn so với câu hỏi. |
|   3 | Lễ hội truyền thống cấp tỉnh được tổ chức hằng năm phải thông báo với cơ quan nào? (#1) | B | 0.40 | 0.00 | 1.00 | 1.00 | generation | Retrieval hoàn hảo (NĐ 110 Điều 14 đứng đầu) nhưng flash-lite trả lời "không có thông tin cụ thể" vì câu chữ là "Ủy ban nhân dân cùng cấp" chứ không ghi "cấp tỉnh" — prompt nhấn mạnh từ chối khiến model không dám suy luận một bước. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Viết lại `SYSTEM_PROMPT` (tiếng Việt): trả lời khi context có thông tin liên quan kể cả cần diễn giải câu chữ, cho phép trả lời một phần và nêu phần thiếu; chỉ từ chối khi context không liên quan. Thử thêm model flash không phải lite. | #1 (B) và #15 (A) có context recall 1.0 nhưng relevancy 0.00 do model tự từ chối | Hết từ chối sai ở các câu đã retrieve đúng (#1 B, #15 A), tăng faithfulness/relevancy | Chạy lại `python -m src.evaluation` trên các câu trên; số câu in-domain bị từ chối phải giảm, 3/3 câu out-of-domain vẫn phải được từ chối |
|        2 | BM25: thêm bigram âm tiết ("lễ_hội", "vàng_mã") và bỏ stopword tiếng Việt trong `tokenize` | #3 overlap 0.96 → 0.59 và #11 recall 1.00 → 0.00 khi thêm BM25 | Hybrid không còn kém dense về recall, giữ lợi thế precision | So `overlap_recall` A và B bằng `context_overlap_recall` — không tốn lời gọi LLM |
|        3 | Câu nhiều ý: tách câu hỏi (query decomposition) hoặc đa dạng hóa nguồn trong top k (MMR / giới hạn số chunk mỗi tài liệu) | #20, #21 overlap chỉ 0.63–0.64: top 5 dồn vào một tài liệu, thiếu evidence thứ hai | Tăng recall cho câu multi-doc từ 0.50 lên gần 1.0 | Overlap recall trên nhóm `multi_doc` của golden set |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Chưa thực hiện thí nghiệm bonus (HyDE, reranker nâng cao) | Config B | — | — | Ưu tiên các khuyến nghị 1–2 trước vì lỗi hiện tại nằm ở prompt và tokenizer BM25 |

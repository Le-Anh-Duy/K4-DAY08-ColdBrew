"""
Golden dataset cho evaluation.

- SPECS khai báo câu hỏi, đáp án chuẩn và vị trí evidence bằng anchor (cụm từ
  đầu/cuối) trong data/standardized. expected_context được trích tự động nên luôn
  khớp nguyên văn file (kể cả xuống dòng, khoảng trắng kép của PDF).
- context_overlap_recall() chấm recall theo độ phủ token của expected_context trong
  các chunk đã retrieve. Không dùng chunk ID hay offset nên vẫn đúng khi đổi
  chunk size, chunking strategy hoặc index lại.

Chạy:  python -m src.golden_dataset
Ghi:   group_project/evaluation/golden_dataset.json
"""

import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from .task6_lexical_search import tokenize


ROOT = Path(__file__).parent.parent
STANDARDIZED_DIR = ROOT / "data" / "standardized"
OUTPUT_FILE = ROOT / "group_project" / "evaluation" / "golden_dataset.json"

REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
OUT_OF_CORPUS = "Không có trong corpus"

# Đoạn khớp ngắn hơn ngưỡng này bị bỏ qua để cụm phổ biến ("lễ hội", "di sản văn hóa")
# ở chỗ khác không bị tính là đã phủ evidence.
MIN_MATCH_TOKENS = 4


def _read(source: str) -> str:
    matches = list(STANDARDIZED_DIR.rglob(source))
    if len(matches) != 1:
        raise FileNotFoundError(f"{source}: tìm thấy {len(matches)} file trong {STANDARDIZED_DIR}")
    return unicodedata.normalize("NFC", matches[0].read_text(encoding="utf-8"))


def _anchor(phrase: str) -> re.Pattern:
    # Khớp bất kể xuống dòng/khoảng trắng kép giữa các từ.
    words = unicodedata.normalize("NFC", phrase).split()
    return re.compile(r"\s+".join(re.escape(w) for w in words))


def extract_context(source: str, start: str, end: str) -> dict:
    """Trích nguyên văn đoạn từ `start` tới hết `end` trong file standardized."""
    text = _read(source)
    starts = list(_anchor(start).finditer(text))
    if len(starts) != 1:
        raise ValueError(f"{source}: anchor đầu {start!r} xuất hiện {len(starts)} lần, cần đúng 1")
    begin = starts[0].start()
    end_match = _anchor(end).search(text, begin)
    if end_match is None:
        raise ValueError(f"{source}: không thấy anchor cuối {end!r} sau anchor đầu")
    return {
        "text": text[begin:end_match.end()],
        "source": source,
        "char_start": begin,
        "char_end": end_match.end(),
    }


def context_overlap_recall(expected_contexts: list[str], retrieved: list[str]) -> float:
    """Tỉ lệ token của evidence xuất hiện (theo đoạn liên tiếp) trong các chunk retrieve.

    1.0 = mọi đoạn evidence đều nằm trong các chunk; 0.0 = không chunk nào chứa.
    So theo token (NFC, bỏ dấu câu) nên không bị ảnh hưởng bởi heading chèn thêm,
    xuống dòng hay overlap giữa các chunk.
    """
    expected = [tokenize(text) for text in expected_contexts]
    total = sum(len(tokens) for tokens in expected)
    if total == 0:
        return 0.0
    chunks = [tokenize(text) for text in retrieved]

    covered = 0
    for tokens in expected:
        hit = [False] * len(tokens)
        for chunk in chunks:
            matcher = SequenceMatcher(None, tokens, chunk, autojunk=False)
            for block in matcher.get_matching_blocks():
                if block.size >= MIN_MATCH_TOKENS:
                    hit[block.a:block.a + block.size] = [True] * block.size
        covered += sum(hit)
    return covered / total


# type: legal | news | multi_doc | out_of_domain
# Câu out_of_domain không có evidence: dùng để calibrate SCORE_THRESHOLD và kiểm tra
# safe refusal; nên loại khỏi trung bình context recall/precision.
SPECS = [
    # ---- legal ----
    {
        "question": "Lễ hội truyền thống cấp tỉnh được tổ chức hằng năm phải thông báo với cơ quan nào?",
        "expected_answer": "Phải thông báo với Ủy ban nhân dân cùng cấp (Ủy ban nhân dân cấp tỉnh) trước khi tổ chức lễ hội.",
        "type": "legal",
        "evidence": [("nghi-dinh-110-2018-quan-ly-to-chuc-le-hoi.md",
                      "2. Lễ hội truyền thống, lễ hội văn hóa, lễ hội ngành nghề cấp tỉnh",
                      "trước khi tổ chức lễ hội.")],
    },
    {
        "question": "Những lễ hội nào phải đăng ký với Bộ Văn hóa, Thể thao và Du lịch trước khi tổ chức?",
        "expected_answer": "Gồm: lễ hội văn hóa, lễ hội ngành nghề cấp quốc gia (do cơ quan trung ương tổ chức) được tổ chức lần đầu; lễ hội văn hóa, lễ hội ngành nghề cấp khu vực (từ 02 tỉnh trở lên tham gia) được tổ chức lần đầu; và lễ hội có nguồn gốc từ nước ngoài được tổ chức lần đầu hoặc khôi phục sau thời gian gián đoạn từ 02 năm trở lên.",
        "type": "legal",
        "evidence": [("nghi-dinh-110-2018-quan-ly-to-chuc-le-hoi.md",
                      "1. Lễ hội phải đăng ký với Bộ Văn hóa, Thể thao và Du lịch",
                      "gián đoạn từ 02 năm trở lên.")],
    },
    {
        "question": "Khi đi lễ hội, người tham gia phải thắp hương, đốt vàng mã như thế nào?",
        "expected_answer": "Phải thắp hương, đốt vàng mã đúng nơi quy định; không chen lấn, xô đẩy gây mất trật tự an ninh và phải giữ gìn vệ sinh môi trường.",
        "type": "legal",
        "evidence": [("nghi-dinh-110-2018-quan-ly-to-chuc-le-hoi.md",
                      "c) Thắp hương, đốt vàng mã đúng nơi quy định",
                      "giữ gìn vệ sinh môi trường;")],
    },
    {
        "question": "Trong khu vực lễ hội có được đốt pháo, thả đèn trời hay đốt đồ mã không?",
        "expected_answer": "Không. Khi dự lễ hội phải bảo đảm trật tự, an ninh, không đốt pháo, không đốt và thả đèn trời, và không đốt đồ mã trong khu vực lễ hội.",
        "type": "legal",
        "evidence": [("thong-tu-04-2011-nep-song-van-minh-cuoi-tang-le-hoi.md",
                      "e) Bảo đảm trật tự, an ninh khi dự lễ hội",
                      "m) Không đốt đồ mã trong khu vực lễ hội.")],
    },
    {
        "question": "Ban tổ chức có được bán vé vào dự lễ hội không?",
        "expected_answer": "Không được bán vé vào dự lễ hội. Chỉ được bán vé cho các trò chơi, trò diễn, biểu diễn nghệ thuật, hội chợ, trưng bày triển lãm trong khu vực lễ hội, với giá vé theo quy định của pháp luật về tài chính.",
        "type": "legal",
        "evidence": [("thong-tu-04-2011-nep-song-van-minh-cuoi-tang-le-hoi.md",
                      "i) Không bán vé vào dự lễ hội;",
                      "theo quy định của pháp luật về tài chính;")],
    },
    {
        "question": "Nhạc trong đám cưới được phép mở trong khung giờ nào?",
        "expected_answer": "Không được mở nhạc trước 06 giờ sáng và sau 22 giờ đêm; âm nhạc phải lành mạnh, vui tươi và âm thanh không vượt quá độ ồn cho phép.",
        "type": "legal",
        "evidence": [("thong-tu-04-2011-nep-song-van-minh-cuoi-tang-le-hoi.md",
                      "e) Âm nhạc trong đám cưới",
                      "sau 22 giờ đêm.")],
    },
    {
        "question": "Có được rải tiền trên đường đưa tang không?",
        "expected_answer": "Không. Cấm rải tiền Việt Nam và các loại tiền của nước ngoài trên đường đưa tang.",
        "type": "legal",
        "evidence": [("thong-tu-04-2011-nep-song-van-minh-cuoi-tang-le-hoi.md",
                      "e) Cấm rải tiền Việt Nam",
                      "trên đường đưa tang;")],
    },
    {
        "question": "Tiền công đức, tài trợ cho di tích và hoạt động lễ hội gồm những hình thức nào?",
        "expected_answer": "Gồm các khoản hiến, tặng cho, tài trợ bằng tiền (tiền Việt Nam, ngoại tệ, gồm tiền mặt và tiền chuyển khoản) và bằng giấy tờ có giá, kim khí quý, đá quý theo quy định của Ngân hàng Nhà nước Việt Nam.",
        "type": "legal",
        "evidence": [("thong-tu-04-2023-thu-chi-le-hoi-tien-cong-duc.md",
                      "1. Tiền công đức, tài trợ cho di tích và hoạt động lễ hội bao gồm",
                      "Ngân hàng Nhà nước Việt Nam.")],
    },
    {
        "question": "Tiền trong hòm công đức phải được kiểm đếm bao lâu một lần?",
        "expected_answer": "Định kỳ hằng ngày hoặc hằng tuần phải kiểm đếm và ghi tổng số tiền tiếp nhận; đơn vị phải cử người tiếp nhận và mở sổ ghi chép đầy đủ số tiền.",
        "type": "legal",
        "evidence": [("thong-tu-04-2023-thu-chi-le-hoi-tien-cong-duc.md",
                      "Cử người tiếp nhận, mở sổ ghi chép đầy đủ số tiền đã tiếp nhận. Đối với tiền",
                      "ghi tổng số tiền tiếp nhận.")],
    },
    {
        "question": "Ngày Di sản văn hóa Việt Nam là ngày nào?",
        "expected_answer": "Ngày 23 tháng 11 hằng năm.",
        "type": "legal",
        "evidence": [("luat-di-san-van-hoa-45-2024-phan-1.md",
                      "Ngày 23 tháng 11 hằng năm",
                      "là Ngày Di sản văn hóa Việt Nam.")],
    },
    {
        "question": "Theo Luật Di sản văn hóa 2024, lễ hội truyền thống được hiểu như thế nào?",
        "expected_answer": "Lễ hội truyền thống gồm các thực hành nghi lễ và sinh hoạt văn hóa dân gian của cộng đồng, được thực hiện theo chu kỳ tại không gian văn hóa liên quan.",
        "type": "legal",
        "evidence": [("luat-di-san-van-hoa-45-2024-phan-1.md",
                      "4. Lễ hội truyền thống gồm",
                      "tại không gian văn hóa liên quan;")],
    },
    {
        "question": "Tri thức về trang phục thuộc loại hình di sản văn hóa phi vật thể nào?",
        "expected_answer": "Thuộc loại hình tri thức dân gian, gồm tri thức về tự nhiên và vũ trụ, sức khỏe và đời sống con người, lao động, sản xuất, phòng bệnh, chữa bệnh, ẩm thực, trang phục và các tri thức dân gian khác.",
        "type": "legal",
        "evidence": [("luat-di-san-van-hoa-45-2024-phan-1.md",
                      "5. Tri thức dân gian gồm",
                      "các tri thức dân gian khác;")],
    },
    # ---- news ----
    {
        "question": "Hội Gióng ở đền Phù Đổng và đền Sóc được UNESCO công nhận khi nào?",
        "expected_answer": "Tháng 11 năm 2010, Hội Gióng được UNESCO công nhận là Di sản văn hóa phi vật thể đại diện của nhân loại.",
        "type": "news",
        "evidence": [("article_01.md",
                      "Là một hội trận được trình diễn bằng một hệ thống biểu tượng",
                      "vào tháng 11 năm 2010.")],
    },
    {
        "question": "Thực hành Tín ngưỡng Thờ Mẫu Tam phủ được UNESCO ghi danh khi nào và ở đâu?",
        "expected_answer": "Ngày 01 tháng 12 năm 2016, tại Phiên họp lần thứ 11 của Ủy ban Liên Chính phủ về bảo vệ di sản văn hóa phi vật thể của UNESCO ở Addis Ababa, Ethiopia; di sản được ghi danh vào Danh sách Di sản văn hóa phi vật thể đại diện của nhân loại.",
        "type": "news",
        "evidence": [("article_06.md",
                      "Vào hồi 17h15’ giờ địa phương",
                      "đại diện của nhân loại.")],
    },
    {
        "question": "Lễ hội Vía Bà Chúa Xứ núi Sam diễn ra vào thời gian nào và ở đâu?",
        "expected_answer": "Từ ngày 22 đến ngày 27 tháng 4 Âm lịch, trong miếu Bà Chúa Xứ núi Sam và khu vực bệ đá thờ Bà trên núi Sam, ở Châu Đốc, An Giang.",
        "type": "news",
        "evidence": [("article_07.md",
                      "Lễ hội Vía Bà Chúa Xứ núi Sam diễn ra từ ngày 22",
                      "ở Châu Đốc, An Giang.")],
    },
    {
        "question": "Mỗi vấn hầu trong nghi lễ hầu đồng gồm những bước nào?",
        "expected_answer": "Gồm 4 bước: mời Thánh nhập (Thánh giáng), phán truyền, ban lộc và đưa tiễn (Thánh thăng).",
        "type": "news",
        "evidence": [("article_09.md",
                      "Mỗi vấn hầu được thực hành qua 4 bước",
                      "âm nhạc sôi động, náo nhiệt).")],
    },
    {
        "question": "Đường đi lên đền Tổ mẫu Âu Cơ được xây bằng bao nhiêu bậc đá?",
        "expected_answer": "Đường lên đền Tổ mẫu Âu Cơ được xây bằng 553 bậc đá.",
        "type": "news",
        "evidence": [("article_08.md",
                      "Trong đền có tượng thờ Mẹ Âu Cơ",
                      "553 bậc đá.")],
    },
    {
        "question": "Hiệp hội Văn hóa Áo dài Việt Nam được thành lập theo quyết định nào?",
        "expected_answer": "Theo Quyết định số 579/QĐ-BNV ngày 9/6/2025 của Bộ trưởng Bộ Nội vụ.",
        "type": "news",
        "evidence": [("article_10.md",
                      "Hiệp hội được thành lập theo Quyết định số 579",
                      "trong nước và quốc tế.")],
    },
    {
        "question": "Theo phong tục Tết của người Việt, ngày mùng ba Tết dành cho ai?",
        "expected_answer": "Ngày mùng ba Tết dành cho thầy cô; học trò thường cùng nhau đi thăm thầy cô, mang theo hoa quả và hoa tươi.",
        "type": "news",
        "evidence": [("article_04.md",
                      "Ngày mùng ba là ngày dành cho thầy cô",
                      "hoa quả và hoa tươi.")],
    },
    # ---- multi_doc: cần evidence từ cả luật và bài viết ----
    {
        "question": "Tín ngưỡng thờ Mẫu Tam phủ thuộc loại hình di sản văn hóa phi vật thể nào theo Luật Di sản văn hóa 2024, và được UNESCO ghi danh năm nào?",
        "expected_answer": "Thuộc loại hình tập quán xã hội và tín ngưỡng (các thực hành thể hiện quan niệm, niềm tin của cộng đồng qua lễ nghi gắn với phong tục, tập quán truyền thống); được UNESCO ghi danh năm 2016.",
        "type": "multi_doc",
        "evidence": [
            ("luat-di-san-van-hoa-45-2024-phan-1.md",
             "3. Tập quán xã hội và tín ngưỡng gồm",
             "bản sắc văn hóa của cộng đồng chủ thể;"),
            ("article_06.md",
             "Vào hồi 17h15’ giờ địa phương",
             "đại diện của nhân loại."),
        ],
    },
    {
        "question": "Nghi lễ Chầu văn thuộc lĩnh vực di sản nào, và Luật Di sản văn hóa 2024 mô tả lĩnh vực đó ra sao?",
        "expected_answer": "Nghi lễ Chầu văn thuộc lĩnh vực tập quán xã hội và tín ngưỡng. Theo Luật, loại hình này gồm các thực hành thường xuyên, ổn định, thể hiện quan niệm, niềm tin của cộng đồng thông qua các lễ nghi gắn liền với phong tục, tập quán truyền thống mang bản sắc văn hóa của cộng đồng chủ thể.",
        "type": "multi_doc",
        "evidence": [
            ("article_09.md",
             "Nghi lễ Chầu văn của người Việt là di sản văn hóa phi vật thể thuộc lĩnh vực",
             "tập trung nhiều nhất ở các tỉnh miền Bắc và Bắc Trung bộ."),
            ("luat-di-san-van-hoa-45-2024-phan-1.md",
             "3. Tập quán xã hội và tín ngưỡng gồm",
             "bản sắc văn hóa của cộng đồng chủ thể;"),
        ],
    },
    # ---- out_of_domain ----
    {"question": "Giá vé máy bay từ Hà Nội đi Phú Thọ là bao nhiêu?",
     "expected_answer": REFUSAL, "type": "out_of_domain", "evidence": []},
    {"question": "Thời tiết Hà Nội ngày mai thế nào?",
     "expected_answer": REFUSAL, "type": "out_of_domain", "evidence": []},
    {"question": "Làm sao để nấu phở bò ngon?",
     "expected_answer": REFUSAL, "type": "out_of_domain", "evidence": []},
]


def build() -> list[dict]:
    """Trích evidence cho mọi câu trong SPECS; lỗi anchor sẽ raise ngay."""
    dataset = []
    for spec in SPECS:
        contexts = [extract_context(*evidence) for evidence in spec["evidence"]]
        dataset.append({
            "question": spec["question"],
            "expected_answer": spec["expected_answer"],
            # list[str] để dùng thẳng làm reference_contexts và cho câu multi_doc.
            "expected_context": [c["text"] for c in contexts] or [OUT_OF_CORPUS],
            "type": spec["type"],
            "evidence": [{k: c[k] for k in ("source", "char_start", "char_end")} for c in contexts],
        })
    return dataset


if __name__ == "__main__":
    data = build()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = {t: sum(d["type"] == t for d in data) for t in dict.fromkeys(d["type"] for d in data)}
    print(f"Saved {len(data)} cases -> {OUTPUT_FILE.relative_to(ROOT)} {counts}")

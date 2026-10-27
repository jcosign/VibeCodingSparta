"""example_02 - PDF 텍스트 추출 + 로컬 요약 + 원본 대조, 이미지 OCR → JSON + 검산 (D2·D3, 키 불필요).

실행(프로젝트 폴더에서):  python -m examples.example_02_pdf_and_image
"""
import re

from extract import image_extract, pdf_to_text, safe_json, summarize, verify_receipt
from sample_docs import SAMPLE_PDF_PATH, make_sample_image

# ── PDF (D3) ──
t = pdf_to_text(SAMPLE_PDF_PATH)
print("추출 길이:", len(t))
s, meta = summarize(t)                                # 기본 engine="local"
print("요약:\n" + s)
print("모드:", meta["mode"])

items = re.findall(r"qty:\s*(\d+)\s*price:\s*(\d+)", t)          # D3 4-2: 원본에서 코드가 직접 계산
calc_total = sum(int(q) * int(p) for q, p in items)
m = re.search(r"TOTAL:\s*(\d+)", t)
print("원본에 TOTAL 포함?", "TOTAL" in t, "| 항목합:", calc_total, "| 원본 TOTAL:", int(m.group(1)) if m else None)

# ── 이미지 (D2) ──
text, meta = image_extract(make_sample_image())
print("\nOCR 원문:\n" + meta.get("ocr_text", "(없음)").strip())
obj = safe_json(text)
print("파싱 결과:", obj)
print("검산:", verify_receipt(obj))
print("END OK")

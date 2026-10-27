"""sample_docs.py - 실습용 샘플 문서 (네트워크·파일 없이 바로 연습).

- SAMPLE_HTML        : D4 교안의 카테고리별 매출 표(표 1개) + 제목·문단
- make_sample_image(): D2 교안의 가짜 영수증을 PNG 바이트로 그림
  (교안 그림은 260×110이지만, 그 크기에선 글자가 너무 작아 OCR이 놓치기 쉬워
   같은 글자를 큰 글씨·넉넉한 여백으로 그립니다 = "OCR 친화적 렌더링")
- SAMPLE_PDF_PATH    : 같은 폴더의 sample_invoice.pdf (D3 교안의 샘플 인보이스)
"""
from io import BytesIO
from pathlib import Path

SAMPLE_PDF_PATH = str(Path(__file__).with_name("sample_invoice.pdf"))

SAMPLE_HTML = """<html>
<body>
<h2>2026년 6월 매출</h2>
<p>의류가 매출 1위, 뷰티가 주문수 1위입니다.</p>
<table>
  <tr><th>카테고리</th><th>매출(만원)</th><th>주문수</th></tr>
  <tr><td>의류</td><td>1351</td><td>420</td></tr>
  <tr><td>신발</td><td>1167</td><td>310</td></tr>
  <tr><td>가방</td><td>1188</td><td>260</td></tr>
  <tr><td>뷰티</td><td>942</td><td>500</td></tr>
</table>
</body>
</html>"""

RECEIPT_LINES = [
    "RECEIPT (demo)",
    "item: apple  qty: 2  price: 15000",
    "item: banana qty: 3  price: 3000",
    "TOTAL: 39000",
]


def make_sample_image(font_size: int = 32) -> bytes:
    """가짜 영수증 PNG(바이트)를 만듭니다. 흰 바탕·검은 글씨·큰 글자 = OCR이 읽기 쉬움."""
    from PIL import Image, ImageDraw, ImageFont

    try:
        font = ImageFont.load_default(size=font_size)   # Pillow 10.1+ : 크기 지정 가능한 기본 글꼴
    except TypeError:
        font = ImageFont.load_default()                 # 아주 옛 Pillow: 작은 비트맵 글꼴(인식률 낮음)

    pad, gap = 40, int(font_size * 0.6)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    boxes = [probe.textbbox((0, 0), line, font=font) for line in RECEIPT_LINES]
    line_h = max(b[3] - b[1] for b in boxes)
    width = max(b[2] - b[0] for b in boxes) + pad * 2
    height = line_h * len(RECEIPT_LINES) + gap * (len(RECEIPT_LINES) - 1) + pad * 2

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    y = pad
    for line in RECEIPT_LINES:
        draw.text((pad, y), line, fill="black", font=font)
        y += line_h + gap
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


if __name__ == "__main__":
    png = make_sample_image()
    print("샘플 영수증 PNG:", len(png), "bytes")
    print("샘플 PDF:", SAMPLE_PDF_PATH, "존재" if Path(SAMPLE_PDF_PATH).exists() else "없음")
    print("SAMPLE_HTML 표 행 수:", SAMPLE_HTML.count("<tr>"))

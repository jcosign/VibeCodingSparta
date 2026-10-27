"""extract.py - 로컬 OCR·로컬 요약(기본) + CLI/Gemini(선택) 핵심 로직.

함수 4개만 기억하세요 (반환은 교안과 같이 (텍스트, meta) 또는 리스트/문자열).
- image_extract() : 이미지 → JSON     engine="local"(기본, Tesseract OCR + 정규식) | "gemini"
- pdf_to_text()   : PDF → 텍스트      pypdf (항상 로컬)
- summarize()     : 텍스트 → 불릿 요약 engine="local"(기본, 규칙 기반 추출 요약) | "cli" | "gemini"
- html_tables()   : HTML → 표 리스트  BeautifulSoup (항상 로컬)  (+ html_text: 본문만)

선택 경로(cli·gemini)는 실패하거나 키·CLI가 없으면 조용히 로컬 결과로 대체합니다.
meta["mode"]를 보면 실제로 어떤 경로가 쓰였는지 알 수 있습니다: "local" | "cli" | "gemini".
"""
import json
import os
import re
import shutil
from collections import Counter
from io import BytesIO

from cli_augment import augment
from gemini_client import ask, ask_image, current_mode

DEFAULT_IMAGE_PROMPT = "이 이미지(영수증/표)에서 항목·수량·금액을 JSON으로 추출해줘."
SUMMARY_SYSTEM = "너는 문서 요약가야. 핵심만 한국어 불릿 3개로 요약해."


# ═══════════════════════════════ D2: 안전한 JSON 파싱 ═══════════════════════════════
def safe_json(s):
    try:
        return json.loads(s)                                   # 정상: 문자열 → 딕셔너리
    except Exception:
        return {"error": "형식오류", "원본": s[:30]}            # 실패: 죽지 않고 에러 표시


def loose_json(s: str):
    """(D2 심화) ```json ... ``` 껍질과 앞뒤 군더더기를 벗기고 다시 파싱. 실패하면 None."""
    s = re.sub(r"^```(json)?|```$", "", s.strip(), flags=re.MULTILINE).strip()
    i, j = s.find("{"), s.rfind("}")                           # 첫 { 부터 마지막 } 까지만
    if i != -1 and j != -1:
        s = s[i:j + 1]
    try:
        return json.loads(s)
    except Exception:
        return None


# ═══════════════════════════════ D1·D2: 이미지 → JSON ═══════════════════════════════
def _pytesseract():
    """pytesseract를 불러오고, Windows에서 PATH에 tesseract가 안 잡히면 기본 설치 경로를 지정합니다."""
    import pytesseract
    if shutil.which("tesseract") is None and pytesseract.pytesseract.tesseract_cmd == "tesseract":
        for p in (r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                  r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                break
    return pytesseract


def tesseract_version():
    """Tesseract 엔진 버전 문자열. pytesseract나 tesseract 프로그램이 없으면 None."""
    try:
        return str(_pytesseract().get_tesseract_version())
    except Exception:
        return None


def _ocr_lang() -> str:
    """OCR_LANG 환경변수가 있으면 그 값, 없으면 한국어 언어팩(kor)이 있을 때 'kor+eng', 아니면 'eng'."""
    if os.getenv("OCR_LANG"):
        return os.getenv("OCR_LANG")
    try:
        return "kor+eng" if "kor" in _pytesseract().get_languages(config="") else "eng"
    except Exception:
        return "eng"


def ocr_image(image_bytes: bytes):
    """Tesseract로 이미지 속 글자를 실제로 인식합니다. 반환: (OCR 원문, 사용 언어)."""
    from PIL import Image
    pytesseract = _pytesseract()
    lang = _ocr_lang()
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    return pytesseract.image_to_string(img, lang=lang), lang


_ITEM_RE = re.compile(r"item\s*:\s*(?P<name>.+?)\s+qty\s*:\s*(?P<qty>\d+)\s+price\s*:\s*(?P<price>[\d,]+)", re.I)
_TOTAL_RE = re.compile(r"(?:TOTAL|합계)\s*:?\s*(?P<total>[\d,]+)", re.I)


def _to_int(s: str) -> int:
    return int(s.replace(",", ""))


def _parse_receipt_lines(text: str) -> dict:
    """OCR 원문을 한 줄씩 정규식으로 읽어 항목·수량·금액 JSON 구조로 만듭니다.

    지금은 샘플 영수증 형식("item: 이름 qty: 수량 price: 단가", "TOTAL: 합계")만 읽습니다.
    실제 영수증 형식에 맞게 정규식을 넓히는 것이 과제 "더 해보기"입니다.
    금액 = 수량 × 단가 는 AI가 아니라 코드가 계산합니다(D3 4-2).
    읽지 못한 값은 지어내지 않고 null(None)로 둡니다(D2 2-3 습관 ②).
    """
    items, total = [], None
    for line in text.splitlines():
        m = _ITEM_RE.search(line)
        if m:
            qty, price = int(m["qty"]), _to_int(m["price"])
            items.append({"이름": m["name"].strip(), "수량": qty, "단가": price, "금액": qty * price})
            continue
        m = _TOTAL_RE.search(line)
        if m:
            total = _to_int(m["total"])
    return {"항목": items, "합계": total}


def verify_receipt(obj) -> dict | None:
    """(D2 4-2·D3 4-2) 항목 금액의 합 == 적힌 합계 인지 코드로 검산. 구조가 안 맞으면 None."""
    if not isinstance(obj, dict) or not isinstance(obj.get("항목"), list) or not obj["항목"]:
        return None
    amounts = [it.get("금액") for it in obj["항목"] if isinstance(it, dict)]
    if not amounts or not all(isinstance(a, (int, float)) for a in amounts):
        return None
    total = obj.get("합계")
    items_sum = sum(amounts)
    return {"항목합": items_sum, "합계": total,
            "일치": (items_sum == total) if isinstance(total, (int, float)) else None}


def image_extract(image_bytes: bytes, prompt: str | None = None, mime: str = "image/png", engine: str = "local"):
    """이미지에서 정보를 JSON으로 추출. 반환: (JSON 텍스트, meta).

    engine="local"(기본): Tesseract OCR → _parse_receipt_lines() 정규식 구조화. prompt는 쓰지 않음.
    engine="gemini"     : Gemini 멀티모달(D2). 키가 없거나 실패하면 자동으로 local 대체.
    """
    fallback = None
    if engine == "gemini":
        if current_mode() == "gemini":
            prompt = prompt or DEFAULT_IMAGE_PROMPT
            text, meta = ask_image(prompt, image_bytes, mime=mime)
            if meta.get("mode") == "gemini":
                return text, meta
            fallback = f"Gemini 호출 실패 → 로컬 OCR로 대체 ({meta.get('error', '')})"
        else:
            fallback = "GEMINI_API_KEY 없음 → 로컬 OCR로 대체"

    try:
        ocr_text, lang = ocr_image(image_bytes)
    except Exception as e:
        meta = {"mode": "local", "engine": "tesseract", "error": f"{type(e).__name__}: {e}"}
        if fallback:
            meta["fallback"] = fallback
        return json.dumps({"error": "OCR 실패", "원인": type(e).__name__}, ensure_ascii=False), meta

    obj = _parse_receipt_lines(ocr_text)
    meta = {"mode": "local", "engine": "tesseract", "lang": lang, "ocr_text": ocr_text}
    if fallback:
        meta["fallback"] = fallback
    return json.dumps(obj, ensure_ascii=False, indent=2), meta


# ═══════════════════════════════ D3: PDF → 텍스트 → 요약 ═══════════════════════════════
def pdf_to_text(path: str) -> str:
    """PDF에서 텍스트를 추출한다."""
    from pypdf import PdfReader
    reader = PdfReader(path)                                                          # ① PDF 파일을 연다
    return "\n".join((p.extract_text() or "") for p in reader.pages).strip()          # ② 페이지마다 글자를 뽑아 이어붙인다


_WORD_RE = re.compile(r"[A-Za-z가-힣]{2,}|\d[\d,]*")
_NUM_RE = re.compile(r"\d[\d,]*")
# 문서에서 특히 중요한 단어(D3 2-3: 금액·납기일은 반드시 포함)가 든 문장에 가산점
KEY_TERMS = ("total", "합계", "총액", "금액", "납기", "마감", "기한")


def _split_sentences(text: str):
    """줄 단위로 나눈 뒤, 마침표·물음표·느낌표 뒤 공백에서 한 번 더 자릅니다."""
    out = []
    for line in text.splitlines():
        line = " ".join(line.split())
        if line:
            out += [p for p in re.split(r"(?<=[.!?。])\s+", line) if p]
    return out


def _local_summary(text: str, n: int = 3):
    """규칙 기반 추출 요약: 문장마다 점수를 매겨 상위 n개 문장을 원래 순서대로 불릿으로.

    점수 = (문장 속 단어들이 문서 전체에 나온 횟수의 평균)
         + 0.5 (숫자가 있으면) + 1.0 (KEY_TERMS 단어가 있으면)
    문장을 새로 쓰지 않고 원문 문장을 그대로 고르므로, 숫자가 바뀌지 않습니다(D3 2-3 "숫자는 인용").
    """
    sentences = _split_sentences(text)
    if not sentences:
        return "(요약할 텍스트가 없습니다)", {"mode": "local", "engine": "rule-based", "sentences": 0}
    freq = Counter(w.lower() for w in _WORD_RE.findall(text))

    def score(s):
        words = {w.lower() for w in _WORD_RE.findall(s)}
        base = sum(freq[w] for w in words) / len(words) if words else 0.0
        bonus = (0.5 if _NUM_RE.search(s) else 0.0) + (1.0 if any(k in s.lower() for k in KEY_TERMS) else 0.0)
        return base + bonus

    top = sorted(range(len(sentences)), key=lambda i: score(sentences[i]), reverse=True)[:n]
    picked = [sentences[i] for i in sorted(top)]                 # 원래 순서 유지
    return "\n".join("- " + s for s in picked), {"mode": "local", "engine": "rule-based",
                                                  "sentences": len(sentences), "picked": len(picked)}


def unverified_numbers(summary: str, source: str):
    """(D3 4-2) 요약에 나왔지만 원본에는 없는 숫자 목록. 빈 리스트면 숫자가 모두 원본에 있음."""
    body = re.sub(r"(?m)^\s*(?:\d+[.)]|[-*•])\s*", "", summary)   # 줄 앞 목록 번호·불릿 기호는 제외
    src = {n.replace(",", "") for n in _NUM_RE.findall(source)}
    return sorted({n.replace(",", "") for n in _NUM_RE.findall(body)} - src)


def summarize(text: str, max_tokens: int = 300, engine: str = "local"):
    """긴 텍스트를 요약. 반환: (요약, meta).

    engine="local"(기본): 규칙 기반 추출 요약(외부 호출 없음).
    engine="cli"        : 로컬 요약을 Claude/Codex CLI로 다듬기(USE_CLAUDE_CLI / USE_CODEX_CLI 필요).
                          원문에 없는 숫자가 끼어들면 그 결과는 버리고 로컬 요약을 씁니다.
    engine="gemini"     : D3의 summarize()와 같은 호출(앞 4000자). 키가 없거나 실패하면 local 대체.
    """
    fallback = None
    if engine == "gemini":
        if current_mode() == "gemini":
            s, meta = ask(system=SUMMARY_SYSTEM, user=text[:4000], max_tokens=max_tokens)
            if meta.get("mode") == "gemini":
                return s, meta
            fallback = f"Gemini 호출 실패 → 로컬 요약으로 대체 ({meta.get('error', '')})"
        else:
            fallback = "GEMINI_API_KEY 없음 → 로컬 요약으로 대체"

    local, meta = _local_summary(text)
    if engine == "cli" and meta.get("sentences"):
        notes = augment("PDF·문서 요약", local)
        rejected = []
        for name in ("claude", "codex"):
            if name in notes:
                bad = unverified_numbers(notes[name], text)
                if bad:
                    rejected.append(f"{name}: 원문에 없는 숫자 {bad}")
                    continue
                return notes[name], {"mode": "cli", "engine": name, "local_summary": local}
        fallback = ("CLI 결과에 원문에 없는 숫자가 있어 버림 → 로컬 요약 (" + "; ".join(rejected) + ")") if rejected \
            else "CLI 결과 없음(플래그 꺼짐·미설치·로그인 안 됨·실패) → 로컬 요약"
    if fallback:
        meta["fallback"] = fallback
    return local, meta


# ═══════════════════════════════ D4: HTML → 표·본문 ═══════════════════════════════
def html_tables(html: str):
    """HTML의 표(table)를 [[행,...], ...] 형태로 모두 추출한다."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")                  # ① 문서를 '수프'로 끓임(=구조 분석)
    tables = []
    for t in soup.find_all("table"):                           # ② 모든 <table>을 찾아 하나씩
        rows = []
        for tr in t.find_all("tr"):                            # ③ 그 표 안의 모든 <tr>(행)
            cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]  # ④ 칸의 '글자만'
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def html_text(html: str) -> str:
    """HTML에서 사람이 읽는 본문 텍스트만 뽑는다."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):                      # ① 눈에 안 보이는 코드 조각을 걷어냄
        tag.decompose()                                        #    decompose = 그 태그를 통째로 삭제
    return " ".join(soup.get_text(" ").split())                # ② 남은 글자만, 공백 정리해서


if __name__ == "__main__":
    from sample_docs import SAMPLE_HTML, SAMPLE_PDF_PATH, make_sample_image

    print("=== PDF ===")
    t = pdf_to_text(SAMPLE_PDF_PATH)
    print("추출 길이:", len(t))
    s, meta = summarize(t)
    print("요약:\n" + s)
    print("meta:", meta)

    print("\n=== HTML ===")
    tables = html_tables(SAMPLE_HTML)
    print("표 개수:", len(tables))
    for row in tables[0]:
        print(row)
    print("본문:", html_text(SAMPLE_HTML))

    print("\n=== 이미지 ===")
    print("Tesseract:", tesseract_version() or "없음")
    text, meta = image_extract(make_sample_image())
    print("OCR 원문:\n" + meta.get("ocr_text", "(없음)").strip())
    print("JSON:", text)
    print("검산:", verify_receipt(safe_json(text)))

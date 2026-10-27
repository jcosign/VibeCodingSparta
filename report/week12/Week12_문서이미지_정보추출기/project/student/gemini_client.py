"""gemini_client.py - Gemini 공용 호출기 (선택 경로, mock 폴백 포함).

이 프로젝트의 기본 경로는 "로컬"(extract.py의 Tesseract OCR·규칙 기반 요약)입니다.
Gemini는 각 탭에서 engine="gemini"를 골랐을 때만 쓰는 선택 경로입니다.

- GEMINI_API_KEY (또는 GOOGLE_API_KEY) 가 있으면 → 진짜 Gemini 호출
- 키가 없거나 호출이 실패하면              → mock(가짜 AI) 결과로 안전 대체 (앱이 멈추지 않음)
- 반환은 항상 (텍스트, meta) 두 개. meta["mode"]가 "gemini"면 진짜, "mock"이면 가짜.

보안: 키는 코드에 쓰지 않고 환경변수에서만 읽습니다(D2 4-3·D3 4-3).
모델 이름은 2026년 기준 예시이며 바뀔 수 있으니 GEMINI_MODEL 환경변수로 바꿔 쓰세요.
"""
import json
import os

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")   # 최신 Gemini Flash 계열(변동 가능)


def _api_key() -> str:
    """GEMINI_API_KEY → GOOGLE_API_KEY 순서로 키를 찾습니다. 없으면 빈 문자열."""
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()


def current_mode() -> str:
    return "gemini" if _api_key() else "mock"      # 키 있으면 'gemini', 없으면 'mock'


# ───────────────────────────── mock (키 없을 때) ─────────────────────────────
def _mock_meta(system: str, user: str, error: str | None = None) -> dict:
    meta = {"mode": "mock", "model": "mock-gemini",
            # 가짜 토큰 계산: 글자 수 기반 어림값(실제 토크나이저 아님)
            "input_tokens": max(1, len(system + user) // 4), "output_tokens": 42}
    if error:
        meta["error"] = error
    return meta


def _mock_text(system: str, user: str, error: str | None = None):
    text = ("- [MOCK 요약] 키가 없어 가짜 요약을 돌려줍니다.\n"
            "- 입력 앞부분: " + " ".join(user.split())[:60] + "\n"
            "- GEMINI_API_KEY를 켜면 같은 코드가 실제 Gemini 요약으로 바뀝니다.")
    return text, _mock_meta(system, user, error)


def _mock_image(prompt: str, error: str | None = None):
    text = json.dumps({"추출": {"항목": "샘플상품", "수량": 2, "금액": 30000},
                       "비고": "MOCK 결과 - 키를 켜면 Gemini가 실제 이미지를 읽습니다."}, ensure_ascii=False)
    return text, _mock_meta("", prompt, error)


# ───────────────────────────── 진짜 Gemini (키 있을 때) ─────────────────────────────
def _client():
    from google import genai                       # pip install google-genai
    return genai.Client(api_key=_api_key())


def _meta_from(resp) -> dict:
    usage = getattr(resp, "usage_metadata", None)
    return {"mode": "gemini", "model": GEMINI_MODEL,
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None)}


def _gemini_text(system: str, user: str, max_tokens: int):
    from google.genai import types
    client = _client()                              # 변수에 담아 둬야 호출 도중 연결이 닫히지 않음
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user,
        config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=max_tokens),
    )
    return (resp.text or "").strip(), _meta_from(resp)


def _gemini_image(prompt: str, image_bytes: bytes, mime: str):
    from google.genai import types
    client = _client()
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime), prompt],
    )
    return (resp.text or "").strip(), _meta_from(resp)


# ───────────────────────────── 공용 호출기 ─────────────────────────────
def ask(system: str, user: str, max_tokens: int = 400):
    """텍스트 질문. 실패/무키 시 mock으로 안전 대체."""
    if _api_key():                                  # 키가 있으면
        try:
            return _gemini_text(system, user, max_tokens)          # → 진짜 Gemini 호출
        except Exception as e:
            return _mock_text(system, user, error=f"{type(e).__name__}: {e}")  # 실패해도 mock으로
    return _mock_text(system, user)                 # 키가 없으면 → mock(가짜 요약)


def ask_image(prompt: str, image_bytes: bytes, mime: str = "image/png"):
    """이미지 + 프롬프트(멀티모달). 무키 시 mock으로 안전 대체."""
    if _api_key():                                  # GEMINI_API_KEY(또는 GOOGLE_API_KEY)가 있으면
        try:
            return _gemini_image(prompt, image_bytes, mime)        # → 진짜 Gemini 호출
        except Exception as e:
            return _mock_image(prompt, error=f"{type(e).__name__}: {e}")  # 실패해도 mock으로 떨어져 멈추지 않음
    return _mock_image(prompt)                      # 키 없으면 mock(가짜 결과)


if __name__ == "__main__":
    print("현재 모드:", current_mode(), f"(모델: {GEMINI_MODEL if current_mode() == 'gemini' else 'mock-gemini'})")
    text, meta = ask("너는 문서 요약가야. 핵심만 한국어 불릿 3개로 요약해.",
                     "TOTAL: 39000 KRW. 사과 2개 15000원, 바나나 3개 3000원.")
    print("텍스트 호출 예시:\n" + text)
    print("meta:", meta)

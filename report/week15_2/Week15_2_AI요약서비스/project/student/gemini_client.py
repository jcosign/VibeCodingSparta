"""Gemini 공용 호출기 (mock 우선) — 15-2주차 배포용 AI 요약 서비스.

- 키는 코드에 쓰지 않고 환경변수(GEMINI_API_KEY 또는 GOOGLE_API_KEY)에서만 읽는다.
- 키가 없으면 mock(가짜 응답)으로 동작 → 키 없이도 앱이 죽지 않는다.
- 키가 있어도 호출이 실패하면 mock으로 자동 대체한다(앱이 죽지 않게).
- ask(system, user) → (text, meta). meta에 모드·모델·입력/출력 토큰 수를 담는다(토큰=돈 감각).
"""
import os

# 교재: "Gemini Flash 계열(빠르고 저렴, 변동 가능)". 정확한 모델명은 바뀔 수 있어 환경변수로 교체 가능.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def current_mode() -> str:
    return "gemini" if _api_key() else "mock"  # 키 없으면 mock으로 동작!


def _approx(*texts: str) -> int:
    """토큰 수 대략 추정(글자 수 / 2). 실제 과금 토큰과 다를 수 있음 — 감각용."""
    return max(1, sum(len(t or "") for t in texts) // 2)


def _mock(system: str, user: str) -> tuple[str, dict]:
    sentences = [s.strip() for s in user.replace("\n", " ").split(".") if s.strip()]
    head = ". ".join(sentences[:2]) + ("." if sentences else "")
    text = f"[MOCK 요약] {head[:200]} (키를 넣으면 실제 Gemini가 요약합니다.)"
    return text, {"mode": "mock", "model": "mock-gemini",
                  "input_tokens": _approx(system, user),   # 입력이 길수록 큼
                  "output_tokens": _approx(text)}          # 출력이 길수록 큼


def ask(system: str, user: str, max_tokens: int = 300) -> tuple[str, dict]:
    """system(역할·규칙) + user(내용) → (text, meta). 실패하면 mock으로 대체."""
    key = _api_key()
    if not key:
        return _mock(system, user)
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system,
                                               max_output_tokens=max_tokens),
        )
        usage = resp.usage_metadata
        return (resp.text or "").strip(), {
            "mode": "gemini", "model": GEMINI_MODEL,
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None)}
    except Exception as e:  # 키 만료·네트워크·패키지 없음 등
        # 로그엔 '정황'만: 에러 종류만 남기고 키·원문은 남기지 않는다.
        print(f"[gemini_client] ERROR Gemini 호출 실패({type(e).__name__}) → mock으로 대체")
        return _mock(system, user)


if __name__ == "__main__":
    print("모드:", current_mode())
    # 숫자는 코드가 확정하고, AI에게는 '해석만' 시키는 형태(데이터 분석 황금 흐름)
    text, meta = ask(system="너는 데이터 리포터야. 주어진 숫자만 사용해 3줄로 해석해.",
                     user="총매출 46,480,000원, 1위 카테고리는 의류, 주문 223건.")
    print("요약:", text)
    print("메타:", meta)

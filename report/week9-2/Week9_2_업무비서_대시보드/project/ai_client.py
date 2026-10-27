"""ai_client.py - AI 호출기. mock / anthropic / openai 를 자동으로 고릅니다.

- ask(system, user, task, ...) -> (text, meta)
    meta = {"mode", "model", "input_tokens", "output_tokens", "cost_usd"}
- 키가 없으면 mock(규칙 기반, 무료)으로 동작하고, 실제 API 호출이 실패해도 mock으로 폴백합니다.
- classify(text)  : 규칙 기반 감정 분류(긍정/부정/중립). 키 불필요.
- safe_json(text) : AI 답에서 JSON을 안전하게 뽑기(파싱 실패 대비).
- mask_pii(text)  : AI에 보내기 전 개인정보 치환.

API 키는 코드에 적지 않습니다. 환경변수 AI_MODE / ANTHROPIC_API_KEY / OPENAI_API_KEY 로만 넣습니다.
"""
import json
import os
import re

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")  # 저렴/빠름
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")              # 저렴/빠름

# 1M(백만) 토큰당 (입력비, 출력비) USD - 교재(D3)의 강의용 근사치입니다.
# 실제 단가는 수시로 바뀌므로 각 회사 요금표에서 확인하세요. 원리만 기억: 출력이 입력보다 비싸다.
_PRICE = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
    "gpt-4o-mini": (0.15, 0.60),
}

# 규칙 기반 감정 분류에 쓰는 단어 조각
_POS_WORDS = ["좋", "만족", "예뻐", "재구매", "빨라", "꼼꼼"]
_NEG_WORDS = ["별로", "불량", "느려", "실망", "환불", "교환", "냄새"]
_TOPICS = {"배송": ["배송"], "품질": ["품질", "불량", "마감", "냄새"], "사이즈": ["사이즈"],
           "가격": ["가격"], "디자인": ["디자인", "사진"]}


def _auto_mode() -> str:
    m = os.getenv("AI_MODE", "").strip().lower()
    if m in ("mock", "anthropic", "openai"):
        return m                      # ① AI_MODE를 명시하면 그대로 따른다
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"            # ② 키가 있으면 실제 Claude
    if os.getenv("OPENAI_API_KEY"):
        return "openai"               # ③ OpenAI 키가 있으면 실제 OpenAI
    return "mock"                     # ④ 아무것도 없으면 mock (기본값)


def current_mode() -> str:
    """지금 쓰일 모드(mock / anthropic / openai). 사이드바 배지용."""
    return _auto_mode()


def _approx_tokens(text: str) -> int:
    """토큰 수 흉내: 단어 수 + 한글 글자 수 (진짜 토큰 계산이 아님)."""
    return len(text.split()) + len(re.findall(r"[가-힣]", text))


def _cost(model, tin, tout):
    pin, pout = _PRICE.get(model, (0.0, 0.0))
    return round(tin / 1_000_000 * pin + tout / 1_000_000 * pout, 6)


def classify(text: str) -> str:
    """규칙 기반 감정 분류: 긍정/부정 단어 수를 세어 많은 쪽, 같으면 중립."""
    pos = sum(w in text for w in _POS_WORDS)
    neg = sum(w in text for w in _NEG_WORDS)
    if pos > neg:
        return "긍정"
    if neg > pos:
        return "부정"
    return "중립"


def _mock(system, user, task, max_tokens=600):
    if task == "sentiment":
        topics = [k for k, words in _TOPICS.items() if any(w in user for w in words)]
        text = json.dumps({"감정": classify(user), "카테고리": topics or ["기타"]}, ensure_ascii=False)
    elif task == "summary":
        head = user.strip().replace("\n", " ")[:60]          # 입력의 앞 60자만 잘라
        text = (f"[MOCK 요약] 핵심 내용은 다음과 같습니다: {head}...\n"
                "- 실제 AI 요약을 보려면 AI_MODE=anthropic(또는 openai)로 키를 켜세요.")
    else:
        text = f"[MOCK 응답] 입력 {len(user)}자를 받았습니다. 실제 AI는 AI_MODE와 키로 켭니다."
    while text and _approx_tokens(text) > max_tokens:       # max_tokens 를 넘으면 잘라낸다(실제 API처럼)
        text = text[:-1]
    meta = {"mode": "mock", "model": "mock",
            "input_tokens": _approx_tokens(system + " " + user),
            "output_tokens": _approx_tokens(text), "cost_usd": 0.0}
    return text, meta


def _anthropic(system, user, temperature, max_tokens):
    import anthropic                                         # 실제 AI를 켤 때만 필요
    client = anthropic.Anthropic()                           # 키는 환경변수 ANTHROPIC_API_KEY 에서 읽음
    resp = client.messages.create(
        model=ANTHROPIC_MODEL, max_tokens=max_tokens, temperature=temperature,
        system=system, messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    tin, tout = resp.usage.input_tokens, resp.usage.output_tokens
    return text, {"mode": "anthropic", "model": ANTHROPIC_MODEL, "input_tokens": tin,
                  "output_tokens": tout, "cost_usd": _cost(ANTHROPIC_MODEL, tin, tout)}


def _openai(system, user, temperature, max_tokens):
    from openai import OpenAI                                # 실제 AI를 켤 때만 필요
    client = OpenAI()                                        # 키는 환경변수 OPENAI_API_KEY 에서 읽음
    resp = client.chat.completions.create(
        model=OPENAI_MODEL, temperature=temperature, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    text = resp.choices[0].message.content or ""
    tin, tout = resp.usage.prompt_tokens, resp.usage.completion_tokens
    return text, {"mode": "openai", "model": OPENAI_MODEL, "input_tokens": tin,
                  "output_tokens": tout, "cost_usd": _cost(OPENAI_MODEL, tin, tout)}


def ask(system, user, task="generic", temperature=0.2, max_tokens=600, mode=None):
    """AI에게 묻는다. 반환: (text, meta). 실제 API가 실패하면 mock으로 대체해 앱이 죽지 않는다."""
    mode = (mode or _auto_mode())
    if mode == "anthropic":
        try:
            return _anthropic(system, user, temperature, max_tokens)
        except Exception as e:
            text, meta = _mock(system, user, task, max_tokens)
            meta["mode"] = f"mock(anthropic 실패: {type(e).__name__})"
            return text, meta
    if mode == "openai":
        try:
            return _openai(system, user, temperature, max_tokens)
        except Exception as e:
            text, meta = _mock(system, user, task, max_tokens)
            meta["mode"] = f"mock(openai 실패: {type(e).__name__})"
            return text, meta
    return _mock(system, user, task, max_tokens)


def safe_json(text, default=None):
    """AI 답에서 JSON을 안전하게 뽑는다. 실패해도 앱이 안 죽는다."""
    try:
        return json.loads(text)                              # ① 정상 JSON이면 바로 성공
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)                 # ② 설명에 둘러싸인 {...}만 뽑기
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return default or {"감정": "판정불가", "카테고리": ["확인필요"]}  # ③ 최후엔 안전한 기본값


def mask_pii(text: str) -> str:
    """AI에 보내기 전 개인정보를 치환한다."""
    text = re.sub(r"\d{6}-\d{7}", "[주민번호]", text)
    text = re.sub(r"01[016789]-?\d{3,4}-?\d{4}", "[전화번호]", text)
    text = re.sub(r"[\w.]+@[\w.]+\.\w+", "[이메일]", text)
    text = re.sub(r"sk-[A-Za-z0-9_\-]+", "[키]", text)       # 실수로 낀 API 키도 제거
    return text


if __name__ == "__main__":
    print("AI 모드:", current_mode())
    t, m = ask("너는 데이터 분석 리포터야.", "총매출 4000만원, 총주문 200건.", task="summary", max_tokens=300)
    print(t)
    print(m)
    for r in ["배송 빨라 좋아요", "불량이 와서 환불했어요", "보통이에요"]:
        print(r, "->", classify(r))
    print(safe_json('여기 결과입니다! ```json\n{"감정": "긍정", "카테고리": ["배송"]}\n``` 도움이 되셨길'))
    print(mask_pii("홍길동 010-9876-5432, hong@abc.com 환불 요청"))

"""도구(calc/faq) + 메모리(history)를 가진 미니 에이전트.

D2: PromptTemplate 으로 프롬프트 재사용
D3: _route() 규칙으로 도구 선택, TOOLS 로 실행
D4: self.history 에 대화를 쌓고, 최근 6줄을 {history} 에 넣어 기억
"""
import re

from langchain_core.prompts import PromptTemplate

from cli_augment import augment
from llm import current_mode, generate

PROMPT = PromptTemplate.from_template(
    "너는 친절한 업무 비서야. 지금까지의 대화를 참고해 한국어로 답해.\n"
    "[대화 기록]\n{history}\n사용자:{user}\n비서:")

FAQ = {
    "환불": "환불은 반품 도착 후 3영업일 이내 처리됩니다.",
    "배송": "일반 배송은 2~3일, 도서산간은 3~5일 걸립니다.",
    "영업": "고객센터는 평일 09~18시 운영합니다.",
}


def calc(expr: str) -> str:
    """사칙연산만 안전하게 계산 (정규식 화이트리스트 + __builtins__ 차단)."""
    if not re.fullmatch(r"[\d\s+\-*/().]+", expr or ""):
        return "계산할 수 없는 입력이에요."
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))
    except Exception:
        return "계산 오류"


def faq(q: str) -> str:
    """회사가 정한 FAQ 표에서 답을 읽어 온다. 없으면 지어내지 않는다."""
    for k, v in FAQ.items():
        if k in q:
            return v
    return "관련 FAQ를 찾지 못했어요."


TOOLS = {"calc": calc, "faq": faq}


class MemoryAgent:
    """도구 + 메모리를 가진 미니 에이전트."""

    def __init__(self):
        self.history = []  # [{"role","content"}] ← 이게 메모리의 전부!

    def _route(self, text: str):
        """규칙 기반 도구 선택. (tool, arg) 또는 (None, None)."""
        if any(op in text for op in "+-*/") and any(c.isdigit() for c in text):
            expr = re.findall(r"[\d][\d\s+\-*/().]*[\d)]", text)
            return ("calc", expr[0]) if expr else (None, None)
        if any(k in text for k in FAQ):
            return "faq", text
        return None, None

    def chat(self, user: str) -> str:
        tool, arg = self._route(user)
        if tool:
            reply = f"[{tool}] {TOOLS[tool](arg)}"
        else:
            hist = "\n".join(f"{h['role']}:{h['content']}" for h in self.history[-6:]) or "(없음)"
            reply = generate(PROMPT.format(history=hist, user=user))
            reply = augment(user, reply)  # 하이브리드 CLI 해설(선택). 꺼져 있으면 그대로 반환
        self.history.append({"role": "사용자", "content": user})
        self.history.append({"role": "비서", "content": reply})
        return reply


if __name__ == "__main__":
    agent = MemoryAgent()
    print("모드:", current_mode())
    for q in ["내 이름은 홍길동이야", "12 * 8 계산해줘", "환불 규정 알려줘", "내 이름 뭐였지?"]:
        print(f"\n사용자: {q}\n비서: {agent.chat(q)}")
    print("\n메모리 길이(turns):", len(agent.history))

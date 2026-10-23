"""LLM 호출 모듈 (D2·D4 + 토요일 프로젝트).

응답 순서 (Week15_1_Project 흐름도 그대로):
  ① 로컬 LLM (Qwen/Qwen2.5-0.5B-Instruct, transformers로 직접 로드)  ← 기본, API 키 불필요
  ② OPENAI_API_KEY 가 있으면 OpenAI
  ③ ANTHROPIC_API_KEY 가 있으면 Anthropic
  ④ mock_generate() - 최종 폴백, 항상 동작

키는 코드에 쓰지 않고 환경변수로만 읽습니다(보안).
"""
import os
import re
from functools import lru_cache

# 더 큰 모델로 바꿔 보기: LOCAL_LLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
LOCAL_MODEL = os.getenv("LOCAL_LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")              # 예시·변동 가능
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")  # 예시·변동 가능

_load_error = ""


@lru_cache(maxsize=1)
def _load_local():
    """로컬 모델을 한 번만 로드한다. 실패하면 None (→ 다음 단계로 폴백)."""
    global _load_error
    if os.getenv("DISABLE_LOCAL_LLM") == "1":  # 로컬 LLM을 끄고 폴백만 시험할 때
        _load_error = "DISABLE_LOCAL_LLM=1"
        return None
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        tok = AutoTokenizer.from_pretrained(LOCAL_MODEL)
        model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL, torch_dtype=dtype).to(device)
        model.eval()
        return tok, model, device
    except Exception as e:  # 패키지 없음·다운로드 실패·메모리 부족 등
        _load_error = f"{type(e).__name__}: {e}"
        print(f"[llm] 로컬 LLM 로드 실패 → 폴백합니다. ({_load_error})")
        return None


def local_generate(prompt: str, max_new_tokens: int = 256) -> str:
    """로컬 LLM으로 생성. 사용할 수 없으면 RuntimeError."""
    loaded = _load_local()
    if loaded is None:
        raise RuntimeError(f"로컬 LLM 사용 불가: {_load_error}")
    tok, model, device = loaded
    import torch

    messages = [{"role": "user", "content": prompt}]
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(text, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    answer = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    if not answer:
        raise RuntimeError("로컬 LLM이 빈 응답을 반환")
    return answer


def current_mode() -> str:
    """지금 generate()가 먼저 쓸 모드: local / openai / anthropic / mock."""
    if _load_local() is not None:
        return "local"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "mock"


def mock_generate(prompt: str) -> str:
    """키·모델 없이 규칙으로 만드는 가짜 응답. 대화 기록에서 이름을 찾아 '기억'을 흉내 낸다."""
    last = prompt.split("사용자:")[-1]                     # 이번 질문 부분
    m = re.search(r"이름은\s*([가-힣A-Za-z]+)", prompt)     # 기록에서 '이름은 XXX' 탐색
    if "이름" in last and m:
        name = re.sub(r"(이에요|예요|입니다|이야|이고|야)$", "", m.group(1))  # 조사 제거
        return f"[MOCK] 당신의 이름은 {name}님이라고 기억하고 있어요."
    return "[MOCK] 요청을 이해했어요. (키를 켜면 실제 LLM이 더 자연스럽게 답합니다.)"


def generate(prompt: str) -> str:
    """프롬프트 → 텍스트. ①로컬 → ②OpenAI → ③Anthropic → ④mock 순서로 시도."""
    try:
        return local_generate(prompt)
    except Exception:
        pass
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=OPENAI_MODEL).invoke(prompt).content
        except Exception as e:
            print(f"[llm] OpenAI 호출 실패 → 다음 단계: {type(e).__name__}")
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=ANTHROPIC_MODEL).invoke(prompt).content
        except Exception as e:
            print(f"[llm] Anthropic 호출 실패 → 다음 단계: {type(e).__name__}")
    return mock_generate(prompt)


if __name__ == "__main__":
    print("모드:", current_mode())
    print("응답:", generate("한 문장으로 자기소개를 해줘."))

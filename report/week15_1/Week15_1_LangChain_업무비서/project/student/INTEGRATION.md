# INTEGRATION - 확장 가이드

> 교재(D3·D4)가 이 문서의 (B)·(C) 섹션을 참조합니다. 원본 INTEGRATION.md 내용은 제공되지 않아, 교재 설명을 바탕으로 새로 작성했습니다.

## (A) 모델 바꾸기 / 실제 API 연결

`llm.py`의 `generate()`는 **① 로컬 LLM → ② OpenAI → ③ Anthropic → ④ mock** 순서로 시도합니다.

| 하고 싶은 것 | 방법 |
|---|---|
| 더 큰 로컬 모델로 품질 비교 | `LOCAL_LLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct streamlit run app.py` |
| 로컬 LLM을 끄고 폴백만 시험 | `DISABLE_LOCAL_LLM=1 streamlit run app.py` |
| 클라우드 폴백 사용 | `export OPENAI_API_KEY=...` 또는 `export ANTHROPIC_API_KEY=...` |
| 클라우드 모델 이름 변경 | `OPENAI_MODEL=...`, `ANTHROPIC_MODEL=...` (기본값은 교재 예시, 변동 가능) |

🔒 키는 **환경변수로만**. 코드·깃·Dockerfile에 키를 적지 마세요.

## (B) 도구 늘리기

1. `agent.py`의 `FAQ`에 한 줄 추가 → `_route()`가 키워드를 자동으로 잡습니다.

```python
FAQ = {
    ...,
    "교환": "교환은 수령 후 7일 이내 고객센터로 신청해 주세요.",  # 예시 문구
}
```

2. 새 도구 함수를 만들면 `TOOLS`에 등록하고 `_route()`에 규칙 한 줄을 추가합니다.

```python
def count_chars(text: str) -> str:
    return f"{len(text)}자"

TOOLS = {"calc": calc, "faq": faq, "count": count_chars}

# _route() 안, 기존 규칙 사이 원하는 우선순위 위치에
if "글자수" in text:
    return "count", text
```

- `_route()`는 **위에서부터 처음 맞는 하나만** 고릅니다(계산 → FAQ → 없음). 순서에 주의하세요.
- 되돌리기 어려운 행동(삭제·전송) 도구는 실행 전 **사람 승인**을 거치게 하세요.

## (C) 메모리 영속화 (8주차 TinyDB)

`self.history`는 RAM이라 앱을 끄면 사라집니다. 파일에 저장하면 재시작해도 남습니다.

```bash
pip install tinydb
```

```python
from tinydb import TinyDB
from cli_augment import mask_pii

db = TinyDB("chat_history.json")

class PersistentAgent(MemoryAgent):
    def __init__(self):
        super().__init__()
        self.history = db.all()                       # (복원) 지난 대화 불러오기

    def chat(self, user: str) -> str:
        reply = super().chat(user)
        db.insert({"role": "사용자", "content": mask_pii(user)})   # (저장) PII 가린 뒤
        db.insert({"role": "비서", "content": mask_pii(reply)})
        return reply
```

- `app.py`에서 `MemoryAgent()` 대신 `PersistentAgent()`를 쓰면 됩니다.
- 초기화 버튼에서 파일도 지우려면 `db.truncate()`를 함께 호출하세요.
- 🔒 대화엔 개인정보가 쌓입니다. **저장 전에 가리고(mask_pii), 필요한 것만 최소 보관**하세요.
- 이 예시는 사용자 1명 기준입니다. 여러 사용자가 쓰면 사용자/세션별로 파일을 나눠야 합니다.

## (D) 하이브리드 CLI 해설 (선택)

`cli_augment.py` - LLM 응답 뒤에 Claude CLI / Codex CLI의 해설을 덧붙입니다.

```bash
USE_CLAUDE_CLI=1 streamlit run app.py   # claude -p "<프롬프트>" 로 호출
USE_CODEX_CLI=1  streamlit run app.py   # codex exec "<프롬프트>" 로 호출
```

- CLI가 없거나, 로그인이 안 됐거나, 시간 초과(기본 60초, `CLI_AUGMENT_TIMEOUT`)면 **조용히 skip**하고 원래 답만 보여 줍니다.
- 도구 응답(`[calc]`/`[faq]`)에는 해설을 붙이지 않습니다(흐름도 기준).
- 외부 CLI로 보내기 전에 `mask_pii()`로 개인정보를 가립니다.

## (E) Docker

```bash
docker build -t week15-assistant .
docker run -p 8501:8501 -v hf-cache:/root/.cache/huggingface week15-assistant
```

브라우저에서 http://localhost:8501 을 엽니다. 모델은 첫 실행 때 내려받습니다.

# Week15_1 토요일 프로젝트 - LangChain 업무 비서

Week15_1 Day1~4 교재와 `Week15_1_Project.pdf`를 바탕으로 만든 과제 폴더입니다.
학생용 코드는 `project/student/`에 있고, 안내는 `project/student/과제안내_쉬운버전.md`를 보세요.

```
project/student/
├── app.py              Streamlit 채팅 웹앱
├── agent.py            도구(calc/faq) + 메모리 + CLI 해설 확장 지점
├── llm.py              로컬 LLM(Qwen2.5-0.5B-Instruct) 기본 + 클라우드/mock 폴백
├── cli_augment.py      Claude/Codex CLI 해설(선택)
├── requirements.txt
├── run.sh / env_set_up.sh
├── Dockerfile / .dockerignore
├── INTEGRATION.md
├── 과제안내_쉬운버전.md
└── examples/ (example_01_prompt_template.py, example_02_memory_chat.py)
```

## 확인이 필요한 부분 (교재에 없거나 실행 검증하지 못한 것)

1. **실행 검증 결과 (2026-10-23, Windows 11, Python 3.12.10, CPU)**
   - 설치 버전: torch 2.14.1+cpu, transformers 5.20.2, langchain-core 1.7.0, streamlit 1.66.1
   - ✅ `examples/example_01`, `agent.py`(mock·local 둘 다), `examples/example_02`, `app.py`(Streamlit AppTest로 4턴 입력·초기화 버튼) 정상
   - ✅ 로컬 LLM이 "내 이름 뭐였지?"에 "당신의 이름은 홍길동입니다"로 답함(메모리 동작)
   - ⚠ 0.5B 모델은 첫 턴에 "안녕하세요, 홍길동입니다"처럼 역할을 헷갈리기도 함(모델 품질 한계)
   - ⚠ Python 3.15에서는 의존성(`zstandard`) 빌드에 실패 → 3.12 사용
   - ⚠ transformers 5.x에서 `torch_dtype is deprecated` 경고가 뜸(동작에는 문제없음. 구버전 호환을 위해 그대로 둠)
   - ❌ 미검증: `env_set_up.sh`/`run.sh` 자체(이 PC에 bash 없음, 같은 단계를 PowerShell로 수행), Docker 빌드, OpenAI/Anthropic 폴백(키 없음), Claude/Codex CLI 해설(CLI 미설치 → skip 동작만 확인)
2. **교재에 코드가 없어 새로 작성한 파일** - `cli_augment.py`, `env_set_up.sh`, `run.sh`, `Dockerfile`, `INTEGRATION.md`, `과제안내_쉬운버전.md`, `examples/example_02_memory_chat.py`, 그리고 `llm.py`의 로컬 LLM 부분. 원본(강사용) 파일이 있다면 그쪽과 대조가 필요합니다.
3. **mock의 "조사 제거"** - 교재에 `name = ...  # 조사 제거`로 생략돼 있어 `이에요|예요|입니다|이야|이고|야`를 지우는 규칙으로 직접 채웠습니다.
4. **CLI 호출 형식** - Claude CLI는 `claude -p "<프롬프트>"`, Codex CLI는 `codex exec "<프롬프트>"`로 호출하도록 했습니다. 교재에는 호출 방법이 없고, 설치된 CLI 버전에 맞는지 확인이 필요합니다. "10주차부터 이어지는 공통 아키텍처"의 원래 구조도 알 수 없습니다.
5. **폴백 세부 동작** - 흐름도는 "키가 있으면 사용"까지만 나와 있습니다. 클라우드 호출이 실패해도 다음 단계(최종적으로 mock)로 넘어가도록 했습니다.
6. **교재에 없는 환경변수(직접 추가)** - `LOCAL_LLM_MODEL`(모델 교체), `DISABLE_LOCAL_LLM`(로컬 끄기), `OPENAI_MODEL`/`ANTHROPIC_MODEL`, `CLI_AUGMENT_TIMEOUT`.
7. **경로 불일치** - Day 교재는 `week15_1/project/`, 프로젝트 PDF는 `project/student/`를 씁니다. 이 폴더는 PDF를 따랐습니다.
8. **제출물 "app.py 수정본"** - 무엇을 고치라는지 PDF에 명시돼 있지 않아 과제안내에 예시만 적었습니다.
9. **GPU** - Windows에서 PyPI 기본 `torch`는 CPU 버전이라, Windows+NVIDIA GPU에서는 CUDA용 설치 명령이 따로 필요할 수 있습니다. 모델 첫 다운로드에는 인터넷과 약 1GB 안팎의 디스크가 필요합니다(정확한 크기는 미확인).
10. **모델 이름** - `gpt-4o-mini`, `claude-haiku-4-5`는 교재의 예시 그대로이며 변경될 수 있습니다.
11. **Windows** - 스크립트는 bash입니다. Windows에서는 Git Bash나 WSL에서 실행하세요(`.venv/Scripts/activate`는 두 스크립트 모두 처리함).

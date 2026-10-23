# Week15_2 토요일 프로젝트 — 배포용 AI 요약 서비스

Week15_2 Day1~4 교재와 `Week15_2_Project.pdf`를 바탕으로 만든 과제 폴더입니다.
학생용 코드는 `project/student/`에 있고, 안내는 `project/student/과제안내_쉬운버전.md`를 보세요.

## 교재 코드를 그대로 옮긴 부분
- `Dockerfile` 전체(D3 2-3), `requirements.txt` 전체(D1 3-3), `.env.example`(D1 3-4), `.dockerignore`의 4줄(D3 3-1)
- `gemini_client.py`의 `_api_key()`·`current_mode()`·mock 메타 형식(D1·D4), `app.py`의 입력창·슬라이더·버튼·사이드바 문구·PORT 표시(D1·D2), `max_tokens=300`(D4)
- `run.sh`의 streamlit 확인 줄과 실행 줄(D4 4-1)

## 실행 검증 결과 (2026-10-23, Windows 11, Python 3.12, streamlit 1.66.1, google-genai 2.33.0)
- ✅ `examples/example_01_config_check.py`, `examples/example_02_deploy_readiness.py`(6종 모두 [O])
- ✅ `python gemini_client.py` → 키 없을 때 mock 응답 + 토큰 메타 출력
- ✅ 잘못된 키로 호출 → Google API가 거절(ClientError) → mock으로 자동 대체(앱이 죽지 않음)
- ✅ `app.py`: Streamlit AppTest로 요약 버튼·빈 입력 경고·사이드바(모드·PORT 8615) 확인, 예외 없음
- ✅ 실제 서버를 8615 포트로 띄워 `/_stcore/health` → `ok`
- ✅ SDK 확인: 설치된 google-genai에 `GenerateContentConfig(system_instruction, max_output_tokens)`, `usage_metadata.prompt_token_count/candidates_token_count`가 있음
- ✅ `.sh`·`Dockerfile`이 LF 줄바꿈
- ❌ 미검증: `env_set_up.sh`·`run.sh`를 bash로 직접 실행(이 PC에 bash 없음 → 같은 단계를 PowerShell로 수행), `docker build`(Docker 없음), 실제 Gemini 응답(유효한 키 없음), AI Studio·Cloud Run·Streamlit Cloud 배포

## 확인이 필요한 부분
1. **원본 파일 없음** — Day 교재에 전체 코드가 나온 것은 Dockerfile·requirements·.env.example뿐입니다. `app.py`, `gemini_client.py`의 `ask()`·mock 요약 방식, `env_set_up.sh`, `examples/*`, `INTEGRATION.md`, `과제안내_쉬운버전.md`, `README.md`는 교재 설명을 근거로 새로 작성했습니다. 강사용 원본이 있다면 대조가 필요합니다.
2. **모델 이름** — 교재는 "Gemini Flash 계열(변동 가능)"이라고만 합니다. 기본값을 `gemini-2.5-flash`로 두었고 `GEMINI_MODEL` 환경변수로 바꿀 수 있습니다. 실제 키로 호출해 보지 못해 현재 사용 가능한 모델명인지 확인되지 않았습니다.
3. **PORT 표시 불일치(교재 내부)** — 교재의 `app.py`는 `os.getenv('PORT','8501')`인데 `run.sh`는 8615로 띄워, 그대로면 사이드바에 8501이 보입니다. D4는 "PORT 8615가 보이는지 확인"하라고 하므로 `run.sh`에서 `export PORT="${PORT:-8615}"`를 추가했습니다.
4. **`run.sh` 추가분** — 교재 발췌(핵심)에 `.venv` 자동 활성화와 `python3`가 없을 때 `python`을 쓰는 줄을 더했습니다(Windows Git Bash 대비).
5. **`.env` 자동 로드 안 함** — 교재에 `.env`를 읽는 코드(python-dotenv 등)가 없어 추가하지 않았습니다. 로컬은 `export GEMINI_API_KEY=...`로 넣어야 합니다. 또 `.env.example`의 `PORT=8501`을 그대로 Docker `--env-file`에 쓰면 포트가 어긋나므로 INTEGRATION.md에 주의를 적었습니다.
6. **비용 상한 표현** — 교재는 "초과 시 자동 비활성화"라고 쓰지만, Google Cloud 예산은 기본적으로 알림만 보내고 자동 차단은 별도 설정이 필요합니다. INTEGRATION.md에 그렇게 적었습니다. 결제 메뉴 이름은 콘솔에서 확인하세요.
7. **AI Studio 원클릭 배포 대상** — AI Studio Deploy는 AI Studio Build에서 만든 앱을 올립니다. 이 Streamlit `app.py`를 AI Studio로 올리는 방법은 교재에 없어, `app.py`는 Docker/Cloud Run 또는 Streamlit Cloud로 배포하도록 안내했습니다.
8. **Streamlit Cloud 시크릿** — 앱이 `os.getenv`로 키를 읽으므로, Streamlit Cloud의 secrets가 환경변수로 들어오는지 배포 후 사이드바로 확인이 필요합니다.
9. **gcloud 명령** — 교재에는 `gcloud run deploy --source .`까지만 나옵니다. `--allow-unauthenticated`, `--set-secrets` 옵션은 추가한 것으로 실행 검증하지 않았습니다.
10. **경로** — Day 교재는 `week15_2/project/`, 프로젝트 PDF는 `project/student/`를 씁니다. 이 폴더는 PDF를 따랐습니다. Day별 `concept/*.ipynb`, `example/*.py`는 프로젝트 파일 목록에 없어 만들지 않았습니다.
11. **`.venv` 포함** — 검증하면서 `project/student/.venv`를 만들었습니다. 제출·압축할 때는 빼세요(`.gitignore`·`.dockerignore`에 포함).

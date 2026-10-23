# INTEGRATION — 배포 가이드 + 트러블슈팅

> 원본(강사용) INTEGRATION.md는 제공되지 않아, D1~D4 교재 설명을 바탕으로 새로 작성했습니다.
> 클라우드 화면·메뉴 이름은 바뀔 수 있습니다(교재도 "2026년 기준, 변동 가능"). ⚠ 표시는 이 PC에서 실행 검증하지 못한 부분입니다.

## 배포 전 점검 (공통)
```bash
./run.sh                                         # 로컬에서 먼저 잘 도는지 (배포의 필수 전 단계)
python examples/example_01_config_check.py       # 모드·PORT·키 유무
python examples/example_02_deploy_readiness.py   # 배포 파일 6종 + .dockerignore의 .env
```
배포 3요소: **① 실행 방법**(`run.sh`, Dockerfile의 `CMD`) · **② 의존성**(`requirements.txt`) · **③ 환경변수**(`GEMINI_API_KEY`, `PORT`)

## (A) Google AI Studio 원클릭 배포 ⭐ 권장 ⚠
1. `aistudio.google.com` 접속(구글 계정) → **Build**에서 만든 앱 열기
2. 상단 **[Deploy]** → 올릴 Google Cloud 프로젝트 선택(결제 계정 연결 필요)
3. 잠시 후 `https://<서비스이름>-....run.app` URL 발급 → 이 URL을 제출

- AI Studio Deploy가 올리는 것은 **AI Studio Build에서 만든 앱**입니다. 이 폴더의 `app.py`(Streamlit)를 그대로 올리려면 (B) 또는 (C)를 쓰세요.
- 키는 배포 설정의 시크릿/환경변수 칸에 넣습니다. 화면·로그에 노출 금지.

## (B) Docker / Cloud Run ⚠
```bash
docker build -t ai-summary .
docker run -p 8080:8080 -e GEMINI_API_KEY ai-summary   # 키는 실행할 때 환경변수로(이미지에 넣지 않음)
# → http://localhost:8080 , 헬스체크 http://localhost:8080/_stcore/health
```
- `-e GEMINI_API_KEY`는 지금 터미널에 설정된 값을 그대로 넘깁니다. 키 없이 실행하면 mock으로 동작합니다.
- `--env-file .env`를 쓸 때는 `.env`에서 `PORT=` 줄을 지우세요. `PORT=8501`이 들어가면 컨테이너가 8501에서 열려 `-p 8080:8080`과 어긋납니다.

Cloud Run에 명령어로 올리기(gcloud CLI 설치·로그인 필요):
```bash
gcloud run deploy ai-summary --source . --allow-unauthenticated \
  --set-secrets GEMINI_API_KEY=<Secret Manager 시크릿 이름>:latest
```
- **`$PORT` 규약**: Cloud Run이 `PORT` 환경변수로 포트를 알려 주고, 앱은 그 포트로 리슨해야 합니다. Dockerfile의 `--server.port=${PORT}`가 이미 처리합니다.
- `--allow-unauthenticated`를 빼면 URL이 인증된 사용자만 접속 가능해집니다(사내용이면 고려).

## (C) Streamlit Community Cloud ⚠
1. 이 폴더를 GitHub 저장소에 올립니다(`.env`·`.venv`는 올리지 않기 → `.gitignore`에 추가).
2. Streamlit Cloud에서 저장소 연결, main file = `app.py`
3. 앱 설정의 **Secrets**에 `GEMINI_API_KEY = "..."` 입력
   - ⚠ 이 앱은 `os.getenv`로 키를 읽습니다. Streamlit Cloud가 최상위 secrets를 환경변수로도 넣어 주는지 배포 후 사이드바(🟢/🟡)로 확인하세요.

## (D) 키·비용·보안 🔒
| 챙길 것 | 할 일 |
|---|---|
| 키 | 환경변수/시크릿으로만 주입. `.env`는 커밋 금지(`.dockerignore`에 포함됨). 로그에 키 출력 금지 |
| 비용 | 배포 직후 **Google Cloud 결제 → 예산 및 알림(Budgets & alerts)** 에서 월 예산 + 50/90/100% 알림. 출력 길이는 `max_tokens=300`으로 상한 |
| 절약 | Cloud Run은 미사용 시 0으로 축소(scale-to-zero). 첫 접속이 잠깐 느린 건(cold start) 정상 |
| PII | 개인정보(PII)는 로그·프롬프트에 남기지 않기. 이름·전화·이메일은 `[치환]` 후 입력. 앱 로그는 길이·모드만 남김 |
| 데이터 | 큰 CSV는 통째로 넣지 말고 코드(pandas)로 집계 → 작은 요약만 앱에 입력 |

⚠ Google Cloud 예산은 **기본적으로 알림만 보내고 서비스를 자동으로 멈추지 않습니다**. 자동 차단까지 원하면 별도 설정(예: 예산 알림 → 결제 비활성화 자동화)이 필요합니다. 학습용이면 낮은 예산 + 알림으로 시작하세요.

## (E) 운영 계기판 3개
- **헬스**: `<URL>/_stcore/health` → `ok` (Streamlit 기본 제공)
- **로그**: Cloud Run 콘솔 Logs / 로컬은 터미널. `ERROR`부터 확인. 앱은 `[app] INFO 요약 요청 접수 (텍스트 N자, 모드=mock)`처럼 정황만 남김
- **비용**: 결제 화면의 예산·알림

## (F) 트러블슈팅
| 증상 | 원인 / 해결 |
|---|---|
| `container failed to start and listen on the port` | 포트 하드코딩. `--server.port=${PORT}` 유지 |
| `ModuleNotFoundError` | `requirements.txt`에 없는 패키지를 import함 → 목록에 추가 |
| `run.sh`가 `pip install -r requirements.txt`만 출력하고 끝남 | streamlit 미설치 → `bash env_set_up.sh` 먼저 |
| 키를 넣었는데 🟡 mock | 같은 터미널에서 `export GEMINI_API_KEY=...` 후 실행했는지 확인(`.env` 파일은 자동으로 읽지 않음) |
| 사이드바는 🟢인데 결과가 `[MOCK 요약]` | Gemini 호출 실패 → 터미널의 `[gemini_client] ERROR ...` 확인(키 오류·모델명·네트워크). 모델은 `GEMINI_MODEL`로 교체 |
| Windows에서 `bash` 없음 | Git Bash 또는 WSL 사용. 또는 `.venv\Scripts\activate` 후 `streamlit run app.py --server.port 8615` |
| `$'\r': command not found` | 스크립트 줄바꿈이 CRLF로 바뀜 → LF로 저장 |

배포가 어려우면 `./run.sh`로 로컬 실행해 제출해도 됩니다(완성·검증이 우선, 배포는 선택).

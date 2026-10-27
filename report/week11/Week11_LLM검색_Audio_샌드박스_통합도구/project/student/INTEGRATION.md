# INTEGRATION.md - D1~D4 교안 코드 ↔ 프로젝트 코드 연결표 + 트러블슈팅

이 문서는 "교안에서 본 코드가 프로젝트의 어디에 들어갔는지"를 짚어 줍니다.
왼쪽은 교안에 실제로 나온 내용, 오른쪽은 이 폴더의 파일·함수입니다.

## 1. 전체 구조 한눈에

```
app.py (화면)                           local_model.py (계산)                         cli_augment.py (선택)
─────────────────────                  ─────────────────────────────                ─────────────────────
탭1 🔎 검색+리랭크   ── 호출 ──▶  search_and_rerank()                                   augment()
                                   ├ bi_encoder_rank()    ← _load_embed_model()    ◀── USE_CLAUDE_CLI=1 /
                                   └ cross_encoder_rank() ← _load_rerank_model()        USE_CODEX_CLI=1 일 때만
탭2 🎙 음성 전사     ── 호출 ──▶  transcribe_audio()       ← _load_whisper()              해설 박스 추가
탭3 🤖 코드 샌드박스 ── 호출 ──▶  try_e2b_sandbox()  ── None(키 없음) ──▶ run_in_local_sandbox()
```

- `app.py`는 **화면만** 담당하고, 모델을 부르는 일은 전부 `local_model.py`에 있습니다.
- `local_model.py`는 Streamlit 없이도 동작합니다: `python local_model.py`로 자가 테스트(D2 핵심 실험 재현 + 샌드박스 3케이스)가 돌아갑니다.

## 2. D1 - LLM 아키텍처(토큰화·어텐션) → 개념적 기반

이 프로젝트에서 D1 내용을 직접 호출하는 함수는 없습니다. 대신 아래 모델들의 "엔진"이 D1에서 배운 구조입니다.

| 교안 내용 | 프로젝트에서 보이는 곳 |
|---|---|
| 문장은 토큰으로 잘린 뒤에야 계산이 시작된다 (D1 0장·1-3) | 임베딩·리랭커·Whisper 모두 입력을 토큰(Whisper는 소리를 로그멜 스펙트로그램)으로 바꾼 뒤 처리 |
| 셀프 어텐션: 문장 안 토큰들이 서로 관련도를 계산 (D1 2-2) | 크로스 인코더는 질문과 문서를 한 입력으로 묶어, 어텐션이 질문 토큰과 문서 토큰을 직접 비교 (D2 2-2) |
| `all-MiniLM-L6-v2`도 트랜스포머 구조, 생성이 아니라 요약 벡터가 목적 (D1 FAQ Q8) | `EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"` |
| 한국어는 GPT-2 기준 영어보다 토큰을 더 많이 쓴다 (D1 1-4) | 탭1·탭2에 한국어/영어를 각각 넣어 보며 차이를 관찰해 볼 수 있음 (단, 이 모델들의 토크나이저는 GPT-2가 아니므로 배율은 다름) |

## 3. D2 - 임베딩 모델과 ReRank → 탭1

| 교안 내용 | 프로젝트 코드 |
|---|---|
| `SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")`, 384차원 벡터 (D2 1-1) | `_load_embed_model()` |
| 크로스 인코더 `cross-encoder/ms-marco-MiniLM-L-6-v2` (D2 2-4) | `_load_rerank_model()` - `CrossEncoder(RERANK_MODEL_ID)` |
| `bi_encoder_rank()` - 질문·문서를 각각 `encode()` 후 `util.cos_sim()` (D2 코드 뜯어보기 ③) | `local_model.bi_encoder_rank()` (교안 코드와 같은 순서) |
| `cross_encoder_rank()` - `pairs = [(query, doc) for doc in documents]` 후 `predict()` (D2 코드 뜯어보기 ③) | `local_model.cross_encoder_rank()` (교안 코드와 같은 순서) |
| 핵심 실험: "환불 어떻게 하나요?" + FAQ 4문장 (D2 2-4) | 탭1 기본값 `SAMPLE_QUERY`, `SAMPLE_DOCUMENTS` |
| 검색-후-재정렬: 1단계 넓게, 2단계 정확하게 (D2 3-1) | 탭1이 두 순위표를 나란히 보여줌, 1위가 다르면 경고 문구 |
| 크로스 인코더 점수는 0~1이 아닌 원점수, 같은 질문 안에서 상대 비교용 (D2 FAQ Q9) | 탭1 캡션, `search_and_rerank()` 독스트링 |
| 리랭커도 완벽하지 않다 (D2 2-5 사례 A) | 탭1 캡션 |
| "모델 로드는 한 번" | `_load_embed_model()`·`_load_rerank_model()`의 `@lru_cache(maxsize=1)` |
| top-k를 몇으로 할까 (D2 3-1-보충) | **과제 "더 해보기"** - top_k 슬라이더 추가 |

**자가 테스트로 D2 수치 재현**: `python local_model.py`를 실행하면 D2 2-4 표와 같은 결과가 나오는지 확인할 수 있습니다.

| 순위 | 바이 인코더 (코사인 유사도) | 크로스 인코더 (리랭커 점수) |
|---|---|---|
| 1 | 환불 0.5617 | 환불 8.0181 |
| 2 | 날씨 0.4910 | 반품 7.8896 (환경에 따라 7.8897처럼 마지막 자리가 다를 수 있음) |
| 3 | 배송 0.2869 | 배송 7.3644 |
| 4 | 반품 0.2153 | 날씨 7.2902 |

D2 2-5 사례 B("주문한 물건이 아직 안 왔어요")의 문서 4개를 탭1에 붙여 넣으면 바이 인코더 1위(결제 수단)와 크로스 인코더 1위(배송 조회)가 갈리는 화면을 볼 수 있습니다.

## 4. D3 - Audio AI(ASR·TTS·STT) → 탭2

| 교안 내용 | 프로젝트 코드 |
|---|---|
| `model = whisper.load_model("tiny")` → `model.transcribe("audio.wav")` → `result["text"]`, `result["language"]` (D3 2-4) | `_load_whisper()` + `transcribe_audio()` (반환 dict의 `text`, `language`) |
| 최초 1회 약 72MB 다운로드, 이후 캐시에서 1초 미만 로드 (D3 2-4 정확성 안내) | `_load_whisper()`의 `@lru_cache(maxsize=1)` + 탭2 스피너 문구 |
| Whisper-tiny 파라미터 37,184,640개 (D3 2-3 표) | `WHISPER_MODEL_NAME = "tiny"` |
| 하나의 모델이 100개 언어 처리, 언어 자동 감지 (D3 2-3-1) | 탭2 "감지된 언어" 지표 |
| `FP16 is not supported on CPU; using FP32 instead` 경고는 정상 (D3 2-4 심화) | `transcribe(..., fp16=False)` - 처음부터 FP32로 계산하도록 지정해 경고를 끔 |
| ffmpeg로 오디오 변환, 16kHz 기준 (D3 1-4) | Whisper가 내부에서 ffmpeg를 불러 16kHz로 읽음 → ffmpeg 미설치 시 탭2가 오류 안내 |
| ASR이 흔히 틀리는 순간: 소음·전문용어·억양 (D3 3-5) | 탭2 캡션 "결과는 사람이 확인하세요" |
| `initial_prompt`로 전문용어 힌트 (D3 3-5-1) | `transcribe_audio(audio_path, initial_prompt=None)` 인자로 준비만 되어 있음 → **과제 "더 해보기"** - 탭2에 입력칸 추가 |
| 회의 녹음 속 개인정보·기밀 (D3 4-3) | 업로드 파일은 임시 폴더에 저장 → 전사 직후 삭제 |

> 참고: 단계 ④의 `Week11_Day3_example_02_tts_to_asr_roundtrip.py`는 D3 교안의 `../example/` 폴더 파일입니다(이 프로젝트 폴더에는 들어 있지 않습니다).

## 5. D4 - E2B·코드 실행 샌드박스 → 탭3

| 교안 내용 | 프로젝트 코드 |
|---|---|
| 가드 패턴: `os.getenv("E2B_API_KEY", "")`가 있으면 E2B, 없으면 로컬 대체 (D4 2-4) | `try_e2b_sandbox()`가 키 없으면 `None` → `app.py`가 `run_in_local_sandbox()` 호출 |
| `Sandbox.create()` → `run_code()` → `execution.logs` → `kill()` (D4 2-2) | `try_e2b_sandbox()` 본문 |
| `finally: sbx.kill()` - 무슨 일이 있었든 반드시 정리(에페메럴) (D4 2-5·2-8) | `try_e2b_sandbox()`의 `try/finally` |
| `Sandbox.create(allow_internet_access=False)` (D4 2-7·2-8) | `try_e2b_sandbox()`에서 사용 |
| API 키는 코드에 하드코딩하지 말 것 (D4 2-4 보안 한 줄) | 키는 환경변수에서만 읽음, `Dockerfile`에도 키를 넣지 않음 |
| `subprocess.run([sys.executable, "-c", ...], timeout=...)` (D4 3-2) | `run_in_local_sandbox()` |
| `resource.setrlimit(RLIMIT_AS / RLIMIT_CPU)`, `try/except`로 감싸 Windows에서도 안 죽게 (D4 3-3, FAQ Q3) | `run_in_local_sandbox()`의 자식 프로세스 시작 부분 |
| `run_locally_sandboxed()`의 반환 상태: 완료 / 시간초과(강제종료) / 오류 (D4 3-5) | 같은 상태 이름 사용(단, 이 프로젝트는 내장함수 제한이 없으므로 "오류(차단됨)" 대신 "오류") |
| `SAFE_BUILTINS`로 위험한 내장함수 제거 - 교육용, 완전한 보안 경계 아님 (D4 3-4) | **과제 "더 해보기"** (기본 코드에는 넣지 않음) |
| 샌드박스가 있어도 결과를 맹신하지 말 것 (D4 4-2) | 탭3 결과 아래 캡션 |
| 감사 추적: 무엇을·언제·얼마나 걸려서·어떤 상태로 (D4 4-1) | 실행 결과 dict에 `status`·`seconds`·`engine`이 들어 있음 → 표로 쌓는 것은 직접 확장해 볼 거리 |

**교안 `run_locally_sandboxed()`와 다른 점** (프로젝트 PDF의 함수 이름은 `run_in_local_sandbox()`):

- `-I`(격리 모드: 사용자 환경변수·현재 폴더 모듈을 읽지 않음)와 `-X utf8`(Windows에서 한글 출력 깨짐 방지)을 붙였습니다.
- 매 실행마다 새 임시 폴더를 작업 폴더로 쓰고, 끝나면 지웁니다(짧은 생명주기 흉내).
- 그래도 **같은 컴퓨터·같은 권한**으로 돌기 때문에 파일·네트워크 격리는 되지 않습니다. 실무에서는 E2B·Docker 같은 검증된 격리를 쓰세요(D4 3-1, FAQ Q2).

**E2B 키 상태별 동작**

| 상태 | `try_e2b_sandbox()` 반환 | 화면 |
|---|---|---|
| `E2B_API_KEY` 없음(기본) | `None` | "E2B_API_KEY가 없어 로컬 대체 샌드박스를 사용했습니다" + 로컬 실행 결과 |
| 키가 있고 정상 | 실행 결과 dict (`engine`: E2B 클라우드 샌드박스) | E2B 실행 결과 |
| 키가 틀림·네트워크 오류 | `status: 오류`, stderr에 `AuthenticationException` 등 | 오류 표시(로컬로 몰래 대신 실행하지 않음) |

## 6. 하이브리드 CLI (`cli_augment.py`)

| 상태 | `augment(task, summary)` 반환값 | 화면 |
|---|---|---|
| 플래그 모두 꺼짐(기본) | `{}` | 해설 박스 없음 |
| `USE_CLAUDE_CLI=1`, `claude` 설치·로그인됨 | `{"claude": "해설..."}` | "🤖 Claude CLI 해설" 박스 |
| `USE_CODEX_CLI=1`, `codex` 설치·로그인됨 | `{"codex": "해설..."}` | "🤖 Codex CLI 해설" 박스 |
| 플래그는 켰지만 CLI 없음/로그인 안 됨/60초 초과/오류 | 해당 키 없음 | 해설 박스 없음(앱은 정상) |

- 실행 명령: Claude는 `claude -p "<질문>"`, Codex는 `codex exec "<질문>"` (비대화형 실행).
- 두 경로는 서로 독립적입니다. 하나가 실패해도 다른 하나에는 영향이 없습니다.
- CLI에 보내는 것은 **결과 요약 텍스트**(순위표, 전사 결과, 코드 실행 출력 앞 500자)입니다. 오디오 파일 자체는 보내지 않지만, 전사 결과·문서 내용은 텍스트로 나가므로 민감 정보가 있으면 켜지 마세요.
- 대기 시간은 환경변수 `CLI_TIMEOUT_SEC`(기본 60초)로 바꿀 수 있습니다.

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 탭2 "전사에 실패했습니다 … FileNotFoundError" | ffmpeg 미설치 | macOS `brew install ffmpeg` / Ubuntu·Docker `apt-get install -y ffmpeg` / Windows `winget install Gyan.FFmpeg` 후 **터미널을 새로 열기** |
| `bash: command not found` (Windows) | bash가 없음 | Git Bash에서 실행하거나, 아래 "Windows PowerShell에서 직접 설치" 순서대로 |
| `source .venv/bin/activate` 파일 없음 (Windows) | Windows 가상환경은 `Scripts` 폴더 | Git Bash: `source .venv/Scripts/activate` / PowerShell: `.venv\Scripts\Activate.ps1` |
| `USE_CLAUDE_CLI=1 streamlit run app.py`가 PowerShell에서 오류 | PowerShell은 `변수=값 명령` 문법이 없음 | `$env:USE_CLAUDE_CLI="1"; streamlit run app.py` |
| `To support symlinks on Windows ...` 경고 | Hugging Face 캐시가 Windows에서 심볼릭 링크를 못 씀 | 무시해도 됨(모델은 정상 다운로드·로드) |
| `You are sending unauthenticated requests to the HF Hub` 경고 | Hugging Face 토큰 없이 다운로드 | 무시해도 됨(공개 모델이라 토큰 불필요) |
| `ModuleNotFoundError: sentence_transformers` 등 | 가상환경을 안 켰거나 설치 중단 | 가상환경 활성화 후 `env_set_up.sh` 다시 실행 |
| 탭1·탭2 첫 실행이 오래 걸림 | 모델 최초 다운로드 | 정상. 두 번째부터는 로컬 캐시에서 바로 로드 |
| 모델 다운로드가 실패 | 사내망이 외부 다운로드 차단 | 사내 IT 정책 확인, 다른 네트워크에서 한 번 받아 캐시 사용 |
| 탭1 두 순위가 항상 같음 | 문서가 너무 적거나 서로 비슷함 | 서로 다른 주제로 4개 이상 넣기(프로젝트 FAQ) |
| 탭3 `ModuleNotFoundError: pandas` 등 | 로컬 샌드박스는 앱과 같은 가상환경의 패키지만 쓸 수 있음 | `requirements.txt`에 있는 패키지(pandas·numpy 등)는 사용 가능, 그 외는 설치 필요 |
| 탭3 "E2B 호출 실패 - AuthenticationException" | `E2B_API_KEY` 값이 틀림 | e2b.dev 대시보드에서 키 확인, 또는 환경변수를 지워 로컬로 실행 |
| `USE_CLAUDE_CLI=1`인데 해설 박스가 없음 | CLI 미설치·미로그인 | 정상. `claude -p "안녕"`이 터미널에서 먼저 되는지 확인 |

### Windows PowerShell에서 직접 설치 (bash가 없을 때)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
ffmpeg -version
python -c "import local_model as lm; lm._load_embed_model(); print('검증 성공: 임베딩 모델 로드 완료')"
streamlit run app.py
```

(`env_set_up.sh`의 5단계를 그대로 옮긴 것입니다. `ffmpeg -version`이 오류면 위 트러블슈팅 첫 줄대로 설치하세요. 이 경우 `env_set_up.log`는 생기지 않으니 마지막 출력 화면을 캡처해 제출하세요.)

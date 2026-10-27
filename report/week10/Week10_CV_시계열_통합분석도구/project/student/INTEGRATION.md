# INTEGRATION.md - D1~D4 교안 코드 ↔ 프로젝트 코드 연결표 + 트러블슈팅

이 문서는 "교안에서 본 코드가 프로젝트의 어디에 들어갔는지"를 짚어 줍니다.
왼쪽은 교안에 실제로 나온 내용, 오른쪽은 이 폴더의 파일·함수입니다.

## 1. 전체 구조 한눈에

```
app.py (화면)                         local_model.py (계산)                 cli_augment.py (선택)
─────────────────────                ─────────────────────────            ─────────────────────
탭1 🖼 이미지 분류  ── 호출 ──▶  classify_image()  ← _load_vit()                augment()
탭2 🎨 이미지 생성  ── 호출 ──▶  generate_image()  ← _load_diffusion()   ◀── USE_CLAUDE_CLI=1 /
탭3 📈 시계열 예측  ── 호출 ──▶  load_sample_airpassengers()                    USE_CODEX_CLI=1 일 때만
                                series_from_csv()                             해설 박스 추가
                                forecast_timeseries()
```

- `app.py`는 **화면만** 담당하고, 모델을 부르는 일은 전부 `local_model.py`에 있습니다.
- `local_model.py`는 Streamlit 없이도 동작합니다: `python local_model.py`로 자가 테스트가 돌아갑니다.

## 2. D1 - 컴퓨터비전·ViT → 탭1

| 교안 내용 | 프로젝트 코드 |
|---|---|
| "이미지는 가로×세로×색상 숫자 배열" (D1 0장) | `classify_image()`가 numpy 배열(`skimage.data.astronaut()` 등)을 받으면 `Image.fromarray()`로 바꾸고, `convert("RGB")`로 3채널을 맞춤 |
| 224×224를 16×16 패치로 자르면 196개 (D1 2-2), 모델 이름의 `patch16-224` (D1 FAQ Q3) | `VIT_MODEL_ID = "WinKawaks/vit-tiny-patch16-224"`, 크기 맞춤은 `AutoImageProcessor`가 처리 |
| 사전학습 모델을 가져다 쓴다(전이학습) (D1 3-2) | `_load_vit()` - `from_pretrained()`로 다운로드·로드 |
| ViT-Tiny 약 570만 파라미터, CPU로도 충분히 빠름 (D1 4-1) | CPU에서 그대로 실행(`torch.no_grad()`) |
| 황금 흐름: 결과를 표로 모은다 (D1 4-2) | Top-5 결과를 `pd.DataFrame`(순위·라벨·확신도(%))으로 반환 → `st.dataframe` |
| 확신도가 낮으면 사람이 검수 (D1 4-2, 프로젝트 FAQ) | **과제 "더 해보기"** - 60% 미만 검수 표시 추가 |

**캐싱 포인트**: `_load_vit()` 위의 `@lru_cache(maxsize=1)` 덕분에 모델은 첫 호출에서 한 번만 내려받고 메모리에 올립니다. 두 번째 분류부터는 같은 객체를 재사용하므로 빠릅니다.

> 참고: 단계 ③에서 비교하라는 `Week10_Day1_example_02_vit_batch_classify.py`는 D1 교안의 `../example/` 폴더 파일입니다(이 프로젝트 폴더에는 들어 있지 않습니다).

## 3. D2 - 이미지 생성(Diffusion) → 탭2

| 교안 내용 | 프로젝트 코드 |
|---|---|
| 경량 증류 모델 `segmind/tiny-sd`, 디스크 약 1GB (D2 4-1) | `DIFFUSION_MODEL_ID = "segmind/tiny-sd"`, `_load_diffusion()` |
| `safety_checker=None` - 교육용이라 끔, 실서비스는 반드시 켜거나 필터 마련 (D2 4-6) | `_load_diffusion()`의 `safety_checker=None` + 주석 |
| `pipe(prompt, num_inference_steps=10, guidance_scale=7.0, generator=generator)` (D2 FAQ Q12) | `generate_image()`의 `pipe(...)` 호출 (`height`/`width`=256 추가) |
| 10스텝·256×256, seed=0 고정 실측 (D2 3-5) | 탭2 기본값: 스텝 10, seed 0, 크기 256, guidance 7.0 |
| 스텝 수: 1~4 거칢 / 10~30 균형 (D2 3-4) | 탭2 슬라이더 범위 4~30 |
| 같은 프롬프트+같은 시드+같은 설정 → 같은 결과 (D2 FAQ Q2) | `torch.Generator("cpu").manual_seed(seed)` |
| "모델 로드는 한 번, 생성은 여러 번" (D2 4-5) | `_load_diffusion()`의 `@lru_cache(maxsize=1)` |
| 좋은 프롬프트 예시 (D2 3-7) | 탭2 기본 프롬프트 `"a small cozy bookstore cafe, warm lighting, watercolor illustration"` |
| guidance scale 1.0/7.0/15.0 비교 (D2 3-5) | **과제 "더 해보기"** - `guidance_scale` 슬라이더 추가 |

## 4. D3 - 시계열 데이터 → 탭3 (데이터·시각화)

| 교안 내용 | 프로젝트 코드 |
|---|---|
| AirPassengers, 1949~1960 월별, 144개 (D3 0장·1-4) | `load_sample_airpassengers()` - `pd.date_range("1949-01-01", periods=144, freq="MS")` |
| 인터넷이 안 되면 백업 데이터로 자동 전환 (D3 실전 예제) | `get_rdataset` 실패 시 `_AIRPASSENGERS`(144개 값) 사용 |
| 날짜를 인덱스로, 시간 순 정렬 유지 (D3 1-2) | `series_from_csv()`의 `sort_index()` |
| 빈도 확인, 빠진 날짜 주의 (D3 1-4, 4-2b 체크리스트) | `series_from_csv()`가 `pd.infer_freq()`로 간격을 확인, 불규칙하면 오류 안내 |
| 9주차 `st.line_chart` 꺾은선 (D3 4-3) | 탭3의 `st.line_chart(실제값 + 예측값)` |
| `seasonal_decompose(passengers, model="multiplicative", period=12)` (D3 3-2) | **과제 "더 해보기"** - 추세·계절성·잔차 그래프 추가 |

## 5. D4 - 시계열 예측(Holt-Winters) → 탭3 (예측)

| 교안 내용 | 프로젝트 코드 |
|---|---|
| `ExponentialSmoothing(train, trend="add", seasonal="mul", seasonal_periods=12, initialization_method="estimated").fit()` (D4 1-3) | `forecast_timeseries()`의 모델 생성부(기본값 동일) |
| `params['smoothing_level' / 'smoothing_trend' / 'smoothing_seasonal']` (D4 1-3) | 반환 dict의 `alpha` / `beta` / `gamma` → 탭3 `st.metric` 3개 |
| alpha·beta·gamma가 1에 가깝다/0에 가깝다의 뜻 (D4 1-5) | 탭3 지표 아래 캡션 |
| 곱셈(mul) vs 덧셈(add) 계절성 (D4 1-3 심화) | 탭3 "계절성 형태" 선택 |
| `seasonal_periods`: 월별 12·일별 7·주별 52·분기별 4 (D4 FAQ Q6) | 탭3 "계절 주기" 선택 |
| 계절성 학습엔 최소 계절 주기의 1~2배 데이터 필요 (D4 4-1) | 데이터가 주기×2보다 짧으면 계절성 없이 예측하고 경고 |
| `mae()`, `mape()` (D4 4-2) | `local_model.py`의 `mae()`, `mape()` (자가 테스트에서 사용) |

**자가 테스트로 D4 수치 재현**: `python local_model.py`를 실행하면 132개월 학습 → 12개월 예측을 해서 D4 교안 1-3의 값(alpha 0.3762 / beta 0.0000 / gamma 0.6238, MAE 10.30, MAPE 2.21%)과 같은 결과가 나오는지 확인할 수 있습니다(라이브러리 버전에 따라 소수점 끝자리는 다를 수 있음).

## 6. 하이브리드 CLI (`cli_augment.py`)

| 상태 | `augment(task, summary)` 반환값 | 화면 |
|---|---|---|
| 플래그 모두 꺼짐(기본) | `{}` | 해설 박스 없음 |
| `USE_CLAUDE_CLI=1`, `claude` 설치·로그인됨 | `{"claude": "해설..."}` | "🤖 Claude CLI 해설" 박스 |
| `USE_CODEX_CLI=1`, `codex` 설치·로그인됨 | `{"codex": "해설..."}` | "🤖 Codex CLI 해설" 박스 |
| 플래그는 켰지만 CLI 없음/로그인 안 됨/60초 초과/오류 | 해당 키 없음 | 해설 박스 없음(앱은 정상) |

- 실행 명령: Claude는 `claude -p "<질문>"`, Codex는 `codex exec "<질문>"` (비대화형 실행).
- 두 경로는 서로 독립적입니다. 하나가 실패해도 다른 하나에는 영향이 없습니다.
- CLI에 보내는 것은 **결과 요약 텍스트(라벨·숫자)뿐**이며, 이미지·CSV 원본은 보내지 않습니다.
- 대기 시간은 환경변수 `CLI_TIMEOUT_SEC`(기본 60초)로 바꿀 수 있습니다.

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `bash: command not found` (Windows) | bash가 없음 | Git Bash에서 실행하거나, 아래 "Windows PowerShell에서 직접 설치" 순서대로 |
| `source .venv/bin/activate` 파일 없음 (Windows) | Windows 가상환경은 `Scripts` 폴더 | Git Bash: `source .venv/Scripts/activate` / PowerShell: `.venv\Scripts\Activate.ps1` |
| `USE_CLAUDE_CLI=1 streamlit run app.py`가 PowerShell에서 오류 | PowerShell은 `변수=값 명령` 문법이 없음 | `$env:USE_CLAUDE_CLI="1"; streamlit run app.py` |
| `OSError: [Errno 2] No such file or directory ... Long Path` (Windows) | 폴더 경로가 길어 Windows 경로 길이 제한(260자)에 걸림 | 프로젝트 폴더를 `C:\w10` 처럼 짧은 경로로 옮기거나, Windows "긴 경로 사용" 설정을 켬 |
| `ModuleNotFoundError: torch` 등 | 가상환경을 안 켰거나 설치 중단 | 가상환경 활성화 후 `env_set_up.sh` 다시 실행 |
| 탭1/탭2 첫 실행이 오래 걸림 | 모델 최초 다운로드(ViT 소용량, tiny-sd 약 1GB) | 정상. 두 번째부터는 로컬 캐시에서 바로 로드 |
| `ViTImageProcessor requires torchvision ... falling back` 경고 | torchvision 미설치(필수 아님) | 무시해도 됨. 분류 결과는 정상 |
| 모델 다운로드가 실패 | 사내망이 외부 다운로드 차단 (D2 FAQ Q8) | 사내 IT 정책 확인, 다른 네트워크에서 한 번 받아 캐시 사용 |
| 탭3 "날짜 간격이 일정하지 않습니다" | CSV에 빠진 날짜·중복 날짜 | 날짜를 빠짐없이 채우기(D3 1-4, FAQ Q5) |
| 탭3 "0 이하 값이 있어 … 덧셈(add)" 경고 | 곱셈 계절성은 0 이하 값을 처리 못함 | 정상 동작(자동으로 add 사용) |
| `USE_CLAUDE_CLI=1`인데 해설 박스가 없음 | CLI 미설치·미로그인 | 정상. `claude -p "안녕"`이 터미널에서 먼저 되는지 확인 |

### Windows PowerShell에서 직접 설치 (bash가 없을 때)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -c "import local_model as lm; lm._load_vit(); print('검증 성공: ViT-Tiny 모델 로드 완료')"
streamlit run app.py
```

(`env_set_up.sh`의 4단계를 그대로 옮긴 것입니다. 이 경우 `env_set_up.log`는 생기지 않으니 마지막 출력 화면을 캡처해 제출하세요.)

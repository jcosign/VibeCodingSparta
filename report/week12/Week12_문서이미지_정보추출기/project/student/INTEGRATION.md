# INTEGRATION.md - D1~D4 교안 코드 ↔ 프로젝트 코드 연결표 + 트러블슈팅

이 문서는 "교안에서 본 코드가 프로젝트의 어디에 들어갔는지"를 짚어 줍니다.
왼쪽은 교안에 실제로 나온 내용, 오른쪽은 이 폴더의 파일·함수입니다.

## 1. 전체 구조 한눈에

```
app.py (화면)                         extract.py (계산)                                   선택 경로
──────────────────────               ─────────────────────────────────                 ─────────────────────
탭1 🧾 이미지 추출   ── 호출 ──▶  image_extract(engine="local")                      ◀── gemini_client.ask_image()
                                   ├ ocr_image()  ← pytesseract (Tesseract 프로그램)       engine="gemini" + 키 있을 때만
                                   └ _parse_receipt_lines()  → JSON  → verify_receipt()
탭2 📄 PDF·문서 요약 ── 호출 ──▶  pdf_to_text()  ← pypdf
                                   summarize(engine="local")  → _local_summary()     ◀── cli_augment.augment()  (engine="cli")
                                                                                     ◀── gemini_client.ask()    (engine="gemini")
                                   unverified_numbers()  (요약 숫자 ↔ 원본 대조)
탭3 🌐 HTML 표 파싱  ── 호출 ──▶  html_tables() · html_text()  ← BeautifulSoup     (선택 경로 없음, 항상 로컬)
```

- `app.py`는 **화면만** 담당하고, 실제 추출·요약은 전부 `extract.py`에 있습니다.
- `extract.py`는 Streamlit 없이도 동작합니다: `python extract.py`로 PDF·HTML·이미지 추출 맛보기가 돌아갑니다.
- 선택 경로(cli·gemini)가 실패하면 결과의 `meta["fallback"]`에 이유가 적히고, 화면에 "ℹ️ … → 로컬 …로 대체" 안내가 뜹니다. `meta["mode"]`(`local`/`cli`/`gemini`)를 보면 실제로 쓰인 경로를 알 수 있습니다.

## 2. D1 - 컴퓨터 비전·멀티모달 AI → 🧾 이미지 탭의 개념적 기반

| 교안 내용 | 프로젝트에서 보이는 곳 |
|---|---|
| 컴퓨터에게 이미지는 픽셀(숫자) 격자, "본다"와 "이해한다"는 다르다 (D1 1-1·1-2) | Tesseract는 픽셀에서 **글자**를 읽고(OCR 원문), 그 글자의 **의미**(항목·수량·금액)는 `_parse_receipt_lines()` 정규식이 정함 |
| CNN을 직접 학습시키지 말고 사전학습 모델을 가져다 쓴다 (D1 2-3) | Tesseract도 이미 학습된 인식 엔진을 설치해서 쓰는 것. 이 프로젝트에서 모델을 학습시키는 코드는 없음 |
| `ask_image(prompt, image_bytes, mime="image/png")`, 키 없으면 mock (D1 3-3·3-4) | `gemini_client.ask_image()` - 교안과 같은 이름·인자·mock 결과(`"샘플상품", 2, 30000`) |
| `current_mode()` → "gemini" / "mock" (D1 3-4) | `gemini_client.current_mode()`, 사이드바 "AI 모드" 표시 |
| 이미지 속 PII는 올리기 전 가린다, 키는 환경변수로 (D1 4-3) | 탭1 캡션, 키는 `GEMINI_API_KEY`/`GOOGLE_API_KEY` 환경변수에서만 읽음 |

## 3. D2 - 이미지 → JSON 추출 → 🧾 이미지 탭

| 교안 내용 | 프로젝트 코드 |
|---|---|
| 길 ① 전통 CV vs 길 ② 멀티모달 AI (D2 1-1) | 이 프로젝트는 **기본 = 로컬 OCR**(Tesseract, 학습된 전통 엔진) + **선택 = Gemini 멀티모달**. 두 길을 같은 탭에서 엔진만 바꿔 비교 가능 |
| `make_sample_image()`가 그리는 가짜 영수증 (D2 1-4) | `sample_docs.make_sample_image()` - 같은 4줄(`RECEIPT (demo)`, apple 2 15000, banana 3 3000, `TOTAL: 39000`). 단, OCR이 읽도록 큰 글씨로 그림(아래 "교안과 다른 점") |
| 버튼 `🔎 정보 추출`, 결과를 `st.code(text, language="json")`으로 표시 (D2 1-4·3-4) | 탭1 그대로 |
| 기본 추출 프롬프트 "이 이미지(영수증/표)에서 항목·수량·금액을 JSON으로 추출해줘." (D3 3-3에 실린 `image_extract`) | `extract.DEFAULT_IMAGE_PROMPT` (engine="gemini"일 때 사용) |
| 출력 지정 4습관: 키 못 박기·모르면 null·숫자 정수·JSON만 (D2 2-3) | 로컬 경로는 코드가 직접 JSON을 만드므로 키가 항상 `항목`·`이름`·`수량`·`단가`·`금액`·`합계`로 고정, 못 읽은 합계는 `null`, 숫자는 콤마 없는 정수 |
| `safe_json()` - try/except로 깨진 JSON에도 앱이 안 죽게 (D2 3-2) | `extract.safe_json()` (교안 코드 그대로) |
| 코드펜스 벗기기 `loose_json()` (D2 3-4 심화) | `extract.loose_json()` - Gemini 응답 파싱이 실패하면 한 번 더 시도 |
| 파싱 후 표로: `pd.DataFrame(obj["항목"])` (D2 3-4) | 탭1 결과 표 |
| 부분의 합 = 전체 검산 (D2 4-2) | `extract.verify_receipt()` → 탭1 "✅ 검증 통과 / ⚠️ 불일치! → 사람 확인" |
| 여러 장 배치 처리 (D2 4-1) | **과제 "더 해보기"** - 여러 이미지 일괄 OCR |

**교안과 다른 점 (꼭 읽어 주세요)**

1. **`금액`의 뜻.** D2 2-2 예시 JSON은 apple의 `"금액": 15000`처럼 영수증의 `price`를 그대로 금액으로 적었는데, 그러면 15000 + 3000 = 18000이라 `TOTAL 39000`과 맞지 않습니다. D3 4-2는 같은 영수증을 `2 × 15000 + 3 × 3000 = 39000`으로 계산합니다. 이 프로젝트는 D3 쪽을 따라 `단가`(= price)와 `금액`(= 수량 × 단가, **코드가 계산**)을 따로 두었고, 그래서 검산이 39000 = 39000으로 통과합니다.
2. **샘플 이미지 크기.** D2는 260×110 PNG로 그렸다고 하지만, 같은 크기·작은 기본 글꼴로 그려 Tesseract로 읽어 보면 `qty`를 `aty`/`aly`로, `TOTAL: 39000`을 **`30000`**으로 잘못 읽었습니다(이 PC의 Tesseract 5.4.0 기준). 그래서 프로젝트 PDF의 "OCR 친화적으로 렌더링"대로 32px 글꼴로 크게 그립니다. 작은 이미지로 일부러 실험해 보면 D2 4-2 "AI(OCR)가 뽑은 숫자는 반드시 검증"을 눈으로 확인할 수 있습니다.

## 4. D3 - PDF 파싱·요약·검증 → 📄 PDF 탭

| 교안 내용 | 프로젝트 코드 |
|---|---|
| `pdf_to_text()` - `PdfReader` → 페이지별 `extract_text() or ""` → `"\n".join` (D3 1-2) | `extract.pdf_to_text()` (교안 코드 그대로) |
| 샘플 인보이스 텍스트·좌표 (`BT 31.18 738.48 Td (item: apple …) Tj ET`) (D3 1-2·1-3 심화) | `sample_invoice.pdf` - apple·banana·TOTAL 줄은 교안 좌표 그대로, `pdf_to_text()` 결과가 D3 1-2 출력과 같음 |
| 빈 결과 = 스캔본 신호 → 멀티모달(OCR)로 넘긴다 (D3 1-3·3-3) | 추출 텍스트가 비면 탭2가 "스캔본인 듯 → 🧾 이미지 추출 탭(OCR)으로" 경고. PDF 페이지를 이미지로 바꾸는 도구는 D3도 "별도 도구"라 했으므로 넣지 않음 |
| `summarize()` - 시스템 프롬프트 "너는 문서 요약가야. 핵심만 한국어 불릿 3개로 요약해." + `text[:4000]` + `ask()` (D3 2-1) | `summarize(engine="gemini")` 경로가 이 호출 그대로 (`extract.SUMMARY_SYSTEM`) |
| `ask(system, user, max_tokens=400)` - 키 없으면 `_mock_text()`, meta에 `mode`·`model`·토큰 수 (D3 2-1) | `gemini_client.ask()`. 단 mock 토큰 수는 글자 수 ÷ 4 어림값(실제 토크나이저 아님) |
| 버튼 `📝 AI 요약` (D3 3-3 You Try) | 탭2 그대로 |
| 요약에서 숫자는 "계산"이 아니라 "인용" (D3 2-3) | **로컬 요약은 원문 문장을 그대로 골라 오므로 숫자가 바뀌지 않음** |
| 금액·납기일 같은 핵심을 꼭 포함 (D3 2-3 좋은 요약 지시) | 로컬 점수에 `KEY_TERMS`(total·합계·총액·금액·납기·마감·기한) 가산점 +1.0, 숫자 있는 문장 +0.5 |
| 요약 숫자는 원본과 대조 (D3 4-1·4-2) | `extract.unverified_numbers()` → 탭2 "✅ 숫자 대조 통과 / ⚠️ 원본에 없는 숫자" |
| 청킹(`summarize_long`) (D3 2-3) | 넣지 않음. 로컬 요약은 외부 호출이 없어 토큰 한계가 없고, gemini 경로는 D3 `summarize()`처럼 앞 4000자만 씀 → 긴 PDF에 청킹 붙이기는 직접 해 볼 거리 |

**로컬 요약 점수 규칙** (`_local_summary`)

```
문장 점수 = (문장 속 단어들이 문서 전체에 나온 횟수의 평균)
          + 0.5 (숫자가 들어 있으면)
          + 1.0 (KEY_TERMS 단어가 들어 있으면)
→ 점수 상위 3문장을 원래 순서대로 "- " 불릿으로
```

샘플 PDF 결과: `item: apple …`, `item: banana …`, `TOTAL: 39000 KRW` (제목 줄과 note 줄은 탈락).

## 5. D4 - HTML 표 파싱·리포트 → 🌐 HTML 탭

| 교안 내용 | 프로젝트 코드 |
|---|---|
| `SAMPLE_HTML` - 카테고리/매출(만원)/주문수 표 (D4 1-1) | `sample_docs.SAMPLE_HTML` (같은 5행 + `<h2>2026년 6월 매출</h2>` + 문단 "의류가 매출 1위, 뷰티가 주문수 1위입니다."(D4 3-1)) |
| `html_tables()` - `find_all("table")` → `find_all("tr")` → `find_all(["th","td"])` + `get_text(strip=True)` (D4 1-2) | `extract.html_tables()` (교안 코드 그대로) |
| `html_text()` - `script`·`style`을 `decompose()` 후 `get_text(" ")` (D4 3-1) | `extract.html_text()` (교안 코드 그대로) → 탭3 "본문 텍스트" |
| `pd.DataFrame(t[1:], columns=t[0])` (D4 2-1) | 탭3, `examples/example_01_html_table.py` |
| 필요한 열만 `df[["카테고리","매출(만원)"]]` (D4 2-2) | 탭3 "리포트에 넣을 열" 선택 상자 |
| `pd.to_numeric`으로 문자열 숫자 → 숫자, 총매출 4648 (D4 2-3) | 탭3이 모든 칸이 숫자인 열을 자동 변환, 예제 01에서 4648 확인 |
| CSV는 `encoding="utf-8-sig"` (D4 2-3) | 탭3 `⬇️ CSV 다운로드` 버튼 |
| 버튼 `📊 표 파싱`, 표 없으면 `st.warning("표를 찾지 못했습니다.")` (D4 4-3·You Try) | 탭3 그대로 |
| robots.txt·요청 간격·약관 (D4 4-2) | 탭3 캡션. 이 앱은 URL을 긁지 않고 붙여 넣은 HTML만 다룸 |

## 6. 선택 경로 - CLI 다듬기 (`cli_augment.py`) · Gemini (`gemini_client.py`)

**CLI 다듬기** (탭2 엔진 `cli`)

| 상태 | 결과 | 화면 |
|---|---|---|
| 플래그 모두 꺼짐(기본) | 로컬 요약 | "ℹ️ CLI 결과 없음(…) → 로컬 요약" |
| `USE_CLAUDE_CLI=1`, `claude` 설치·로그인됨 | Claude가 다듬은 요약 (`mode: cli`) | 요약 + "비교: 로컬 요약(다듬기 전)" 펼치기 |
| `USE_CODEX_CLI=1`, `codex` 설치·로그인됨 | (Claude가 실패했거나 꺼져 있으면) Codex가 다듬은 요약 | 위와 같음 |
| CLI가 원문에 없는 숫자를 섞음 | 그 결과는 버리고 로컬 요약 | "ℹ️ CLI 결과에 원문에 없는 숫자가 있어 버림 → 로컬 요약 (claude: 원문에 없는 숫자 ['40000'])" |
| CLI 없음/로그인 안 됨/60초 초과/오류 | 로컬 요약 | "ℹ️ CLI 결과 없음(…)" |

- 실행 명령: Claude는 `claude -p "<요청>"`, Codex는 `codex exec "<요청>"` (비대화형 실행). 대기 시간은 `CLI_TIMEOUT_SEC`(기본 60초).
- CLI에 보내는 것은 **로컬 요약 불릿(최대 3문장)** 입니다. PDF 원문 전체는 보내지 않지만, 요약에 민감 정보가 있으면 켜지 마세요.

**Gemini** (탭1·탭2 엔진 `gemini`)

| 상태 | 결과 |
|---|---|
| `GEMINI_API_KEY`(또는 `GOOGLE_API_KEY`) 없음 | 로컬 결과 + "ℹ️ GEMINI_API_KEY 없음 → 로컬 …로 대체" |
| 키가 틀림·네트워크 오류·모델 이름 오류 | 로컬 결과 + "ℹ️ Gemini 호출 실패 → 로컬 …로 대체 (ClientError: 400 … API key not valid …)" |
| 키 정상 | Gemini 결과 (`mode: gemini`), 탭1은 `safe_json` → `loose_json` 순으로 파싱 |

- 모델 이름 기본값은 `gemini-flash-latest`(교안의 "최신 Gemini Flash 계열" 예시). 바뀌었으면 `GEMINI_MODEL` 환경변수로 지정하세요.
- `python gemini_client.py`의 mock 경로는 그대로 남아 있어 교안 D1~D3의 "모드: mock" 실습을 할 수 있습니다. 다만 **탭에서는 mock 결과를 보여 주지 않고** 로컬 결과로 대체합니다(프로젝트 PDF: "키 없으면 자동 로컬 대체").

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 사이드바 "로컬 OCR: 🔴 설치 안 됨", 탭1 "OCR 실패: TesseractNotFoundError" | Tesseract 프로그램 미설치 (pytesseract는 연결 라이브러리일 뿐) | macOS `brew install tesseract` / Ubuntu·Docker `apt-get install -y tesseract-ocr` / Windows `winget install UB-Mannheim.TesseractOCR` 후 앱을 다시 켜기 |
| Windows에서 설치했는데 `tesseract --version`이 안 됨 | 설치 폴더가 PATH에 없음 | 앱은 `C:\Program Files\Tesseract-OCR\tesseract.exe`를 자동으로 찾으므로 그대로 동작. 터미널에서도 쓰려면 PATH에 추가 |
| 한국어 영수증 글자가 깨짐 | 한국어 언어팩(kor) 없음 → `eng`로만 인식 | Ubuntu `apt-get install -y tesseract-ocr-kor`, macOS `brew install tesseract-lang`, Windows 설치 시 Korean 언어 데이터 선택. 설치되면 자동으로 `kor+eng` 사용(직접 지정: `OCR_LANG=kor+eng`) |
| OCR 원문은 나오는데 JSON `항목`이 비어 있음 | `_parse_receipt_lines()`는 샘플 형식(`item: … qty: … price: …`)만 읽음 | 정상. 내 영수증 형식에 맞게 정규식을 넓히는 것이 과제 "더 해보기" |
| 숫자를 잘못 읽음(예: 39000 → 30000) | 글자가 작거나 흐림 | 더 크게·선명하게 찍기. 그래서 "검산"과 "사람 확인"이 필요 (D2 4-2) |
| 탭2 "글자가 안 뽑혀요 → 스캔본" | 이미지로만 된 PDF | 페이지를 이미지로 저장해 탭1에 올리기 (D3 1-3) |
| 탭2 엔진 `gemini`인데 "Gemini 호출 실패 … API key not valid" | 키 값이 틀림 | AI Studio에서 키 확인, 또는 환경변수를 지워 로컬로 |
| 키가 맞는데도 "Gemini 호출 실패" 안내가 뜸 | 모델 이름이 바뀌었을 수 있음(괄호 안 오류 문구 확인) | AI Studio에서 현재 모델 이름을 확인해 `GEMINI_MODEL=<모델 이름>`으로 지정 |
| `USE_CLAUDE_CLI=1`인데 로컬 요약만 나옴 | CLI 미설치·미로그인 | 정상. `claude -p "안녕"`이 터미널에서 먼저 되는지 확인 |
| `bash: command not found` (Windows) | bash가 없음 | Git Bash에서 실행하거나, 아래 "Windows PowerShell에서 직접 설치" |
| `source .venv/bin/activate` 파일 없음 (Windows) | Windows 가상환경은 `Scripts` 폴더 | Git Bash: `source .venv/Scripts/activate` / PowerShell: `.venv\Scripts\Activate.ps1` |
| `USE_CLAUDE_CLI=1 streamlit run app.py`가 PowerShell에서 오류 | PowerShell은 `변수=값 명령` 문법이 없음 | `$env:USE_CLAUDE_CLI="1"; streamlit run app.py` |
| CSV를 엑셀에서 열면 한글이 깨짐 | 인코딩 | 앱의 다운로드 버튼은 이미 `utf-8-sig`. 직접 저장할 때도 `encoding="utf-8-sig"` (D4 FAQ) |
| `pip install` 중 "Windows Long Path support" 오류 | 폴더 경로가 너무 김 | 프로젝트를 짧은 경로(예: `C:\w12`)로 옮기거나 Windows 긴 경로 지원 켜기 |

### Windows PowerShell에서 직접 설치 (bash가 없을 때)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
winget install UB-Mannheim.TesseractOCR
python -c "import extract as ex; print('Tesseract:', ex.tesseract_version())"
python -m examples.example_02_pdf_and_image
streamlit run app.py
```

(`env_set_up.sh`의 4단계를 그대로 옮긴 것입니다. `Tesseract: None`이면 설치 후 터미널을 새로 여세요. 이 경우 `env_set_up.log`는 생기지 않으니 마지막 출력 화면을 캡처해 제출하세요.)

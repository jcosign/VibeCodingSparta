# Week12 토요일 프로젝트 — 문서·이미지 정보 추출기 (웹앱)

Week12 Day1~4 교안(컴퓨터 비전·멀티모달 / 이미지→JSON / PDF 파싱·요약 / HTML 표 파싱), OX 퀴즈, `Week12_Project_1.pdf`를 바탕으로 만든 과제 폴더입니다.

- `project/student/` — 학생 배포용. 프로젝트 PDF의 파일 목록(15개 항목)을 그대로 만들었습니다. PDF가 "컨테이너 검증 완료"된 앱을 전제로 하므로 앱은 바로 동작하는 상태이고, 과제는 실행·관찰·캡처 + "더 해보기" 확장입니다.
  - 과제 명세: `Week12_Project.md` (프로젝트 PDF 내용, 흐름도는 Mermaid로 옮김)
  - 교안 ↔ 코드 연결표·트러블슈팅: `INTEGRATION.md`
  - 따라하기: `과제안내_쉬운버전.md`

## 교안 내용을 그대로 옮긴 부분
- 함수 본문: `pdf_to_text()`(D3 1-2), `html_tables()`·`html_text()`(D4 1-2·3-1), `safe_json()`(D2 3-2), `loose_json()`(D2 3-4 심화)
- 함수 이름·인자·반환: `ask(system, user, max_tokens=400)`·`ask_image(prompt, image_bytes, mime="image/png")`·`current_mode()`·`_api_key()`·`_mock_text()`·`_mock_image()`·`_gemini_text()`·`_gemini_image()`(D1 3-3·3-4, D2 1-4, D3 2-1), `summarize()`·`image_extract()`가 `(텍스트, meta)` 반환(D2·D3), `_parse_receipt_lines()`(프로젝트 PDF 7장)
- mock 결과 `{"추출": {"항목": "샘플상품", "수량": 2, "금액": 30000}, "비고": "MOCK 결과 - …"}`, meta의 `mode`·`model: mock-gemini`(D1 3-4·D3 2-1), 키 환경변수 `GEMINI_API_KEY`/`GOOGLE_API_KEY`
- 샘플: 영수증 4줄(D2 1-4), `sample_invoice.pdf` 텍스트와 apple·banana·TOTAL 줄 좌표(D3 1-2 심화), `SAMPLE_HTML` 표와 본문 문장(D4 1-1·3-1)
- 요약 시스템 프롬프트·`text[:4000]`(D3 2-1), 기본 이미지 프롬프트(D3 3-3)
- 버튼 이름 `🔎 정보 추출`(D2)·`📝 AI 요약`(D3)·`📊 표 파싱`(D4), "표를 찾지 못했습니다." 경고, CSV `utf-8-sig`(D4)
- 3탭 구성·엔진 선택(이미지 local/gemini, PDF local/cli/gemini, HTML 항상 로컬)·"키 없으면 자동 로컬 대체"·`USE_CLAUDE_CLI`/`USE_CODEX_CLI`·Dockerfile의 `apt-get install -y tesseract-ocr`·`env_set_up.sh`의 Tesseract 확인과 OCR 검증(프로젝트 PDF 흐름도·1·2·4·5·7장)
- `python3 -m examples.example_01_html_table` 실행 형태(D4 마무리)

## 실행 검증 결과 (2026-10-27, Windows 11, Python 3.12)
설치 버전: streamlit 1.66.1, pandas 3.1.0, pypdf 6.21.2, beautifulsoup4 4.15.0, pillow 13.0.0, pytesseract 0.3.13, google-genai 2.33.0, Tesseract 5.4.0.20240606(`winget install UB-Mannheim.TesseractOCR`, 언어 eng·osd)
- ✅ `python extract.py` / `python -m examples.example_02_pdf_and_image` → 샘플 영수증 OCR 원문 4줄 정확, JSON 항목 2개, 검산 항목합 39000 = 합계 39000, `END OK`
- ✅ `sample_invoice.pdf` → `pdf_to_text()` 결과가 D3 1-2 출력과 같음(길이 173자), `"TOTAL" in t` True, D3 4-2 정규식으로 항목합 39000 = TOTAL 39000
- ✅ 로컬 요약 → `item: apple …` / `item: banana …` / `TOTAL: 39000 KRW` 3불릿, 숫자 대조 통과
- ✅ `python -m examples.example_01_html_table` → 표 4행, 총매출 4648만원(D4 2-3과 일치), 매출순 의류·가방·신발·뷰티, `END OK`
- ✅ Streamlit AppTest: 3탭 렌더, 탭1 OCR 원문·JSON·표·"검증 통과", 탭2 local/cli/gemini 세 엔진 모두 결과 + 대체 안내, 탭3 표·CSV 버튼, `<table>` 삭제 시 "표를 찾지 못했습니다.", 예외 없음
- ✅ 실제 서버 `/_stcore/health` → `ok`
- ✅ 가짜 `claude` 명령 + `USE_CLAUDE_CLI=1 USE_CODEX_CLI=1`: 숫자를 지킨 다듬기 → `mode: cli` 채택 / `TOTAL 40000`을 지어낸 다듬기 → 버리고 로컬 요약 + 이유 표시. Codex(미설치)는 조용히 skip
- ✅ 틀린 `GEMINI_API_KEY` → Google 서버가 `400 API key not valid` 응답 → 탭1·탭2 모두 로컬로 대체 + 이유 표시
- ✅ Tesseract 없음(경로를 틀리게 지정) → `TesseractNotFoundError`, 앱은 죽지 않고 설치 안내
- ✅ `env_set_up.sh`·`run.sh` LF 줄바꿈, `env_set_up.sh`의 OCR 검증 파이썬 블록 단독 실행 → "검증 성공: Tesseract 5.4.0.20240606 OCR로 샘플 영수증 2개 항목 인식"
- ❌ 미검증: `bash env_set_up.sh` 통째 실행(이 PC에 bash 없음 — 같은 단계를 PowerShell로 수행), `docker build`(Docker 없음), **정상 키로 Gemini 호출**(유효한 키 없음 → 기본 모델 이름 `gemini-flash-latest`가 지금 통하는지도 미확인), 실제 Claude/Codex CLI 응답(미설치), 한국어 OCR(kor 언어팩 미설치), 실제 사진 영수증

## 확인이 필요한 부분
1. **원본 코드 없음** — 프로젝트 PDF에는 파일 목록·흐름도·함수 이름만 있고 코드 본문은 없습니다. 교안 발췌 코드와 프로젝트 PDF 설명을 근거로 새로 작성했습니다. 강사용 원본이 있다면 대조가 필요합니다.
2. **`금액`의 정의가 D2와 다름** — D2 2-2 예시 JSON은 apple `"금액": 15000`(= price)인데, 그러면 항목합 18000 ≠ TOTAL 39000이 되어 D2 4-2 검산 코드가 "불일치"를 냅니다. D3 4-2의 계산(수량 × price)을 따라 `단가`와 `금액`(= 수량 × 단가, 코드 계산)을 분리했습니다.
3. **샘플 이미지 크기가 D2와 다름** — D2는 260×110 PNG라고 했지만, 그 크기·작은 글꼴로 그려 OCR하면 `qty`→`aty`/`aly`, `TOTAL: 39000`→`30000`으로 잘못 읽었습니다(실측). 프로젝트 PDF의 "OCR 친화적으로 렌더링"에 맞춰 32px 글꼴로 크게 그렸습니다. 이 오인식 사례는 수업에서 "숫자 검증" 예시로 쓸 수 있습니다.
4. **로컬 요약 규칙은 직접 정한 것** — 프로젝트 PDF는 "문장 점수를 매겨 핵심 문장만 고르는 방식"까지만 말합니다. 점수식(단어 빈도 평균 + 숫자 +0.5 + 금액·납기 키워드 +1.0, 상위 3문장)은 D3의 "금액·납기일 포함"·"숫자는 인용" 원칙에 맞춰 정했습니다.
5. **탭에서는 Gemini mock을 보여 주지 않음** — 교안 D1~D3은 "키 없으면 mock", 프로젝트 PDF는 "키 없으면 자동 로컬 대체"라서 탭은 로컬로 대체합니다. mock 경로는 `gemini_client.py`에 남아 있어 `python gemini_client.py`로 교안 실습은 그대로 됩니다.
6. **교안에 없어 추가한 것** — `verify_receipt()`·`unverified_numbers()`(D2 4-2·D3 4-2 검증을 함수로), CLI 다듬기 결과에 원문에 없는 숫자가 있으면 버리는 규칙, Windows 기본 설치 경로 자동 탐색, kor 언어팩 자동 감지·`OCR_LANG`·`GEMINI_MODEL`·`CLI_TIMEOUT_SEC` 환경변수, 탭3 열 선택·숫자 열 자동 변환·칸 개수 맞추기, 결과를 `st.session_state`에 보관(입력을 바꾸면 이전 결과 숨김), 스캔본 PDF 경고, 사이드바 엔진 상태.
7. **넣지 않은 것** — 스캔 PDF 페이지를 이미지로 바꾸는 기능(D3도 "별도 도구"), 청킹 `summarize_long`, 여러 이미지 일괄 OCR·영수증 정규식 확장(과제 "더 해보기"), 교안 concept/example 폴더의 `Week12_DayN_...` 파일(교안 소관).
8. **solution 없음** — 앱이 완성본으로 제공되는 구조라 별도 정답 파일은 만들지 않았습니다.

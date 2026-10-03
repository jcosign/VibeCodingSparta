# 과제 명세 (problem.md) — 데이터 분석 리포트 웹앱 만들기

> 이 파일을 **`env.md`와 함께** Claude Code(또는 Codex CLI)에 그대로 붙여넣으세요.
> "아래 problem.md와 env.md를 읽고, 순서대로 하나씩 만들어줘. 매 단계 실행해서 확인하고 진행해줘." 라고 요청하면 됩니다.

## 🎯 무엇을 만드나요
가짜 판매 데이터를 만들고 → 정리하고 → AI로 분석하고 → 보고서를 만들고 → API로 제공하는
**초보자용 웹앱(Streamlit)** 을 만듭니다. **API 키 없이 동작(mock)** 하는 것이 기본이며, 원하면 `claude`/`codex` CLI로 실제 분석도 되게 합니다.

## ✅ 이렇게 만들어 주세요 (6단계)

### STEP 1. 가짜 데이터 만들기 — `generate_data.py`
- numpy로 **판매 데이터 10,000개**(최소 1,000개)를 만든다. (faker 쓰지 말고 numpy만)
- 컬럼(숫자 위주): `order_id, date, region(지역), category(카테고리), quantity(수량), unit_price(단가), amount(금액=수량×단가), rating(1~5), age`
- **전처리 연습을 위해** 결측치·이상치(금액 폭탄)·단가 0·중복을 일부러 조금 섞는다. seed 고정.
- `data/raw_sales.csv`로 저장. 실행 시 생성 개수와 앞 3행을 출력.

### STEP 2. pandas로 전처리 → DB — `preprocess.py`
- 아직 AI에 넣지 않는다. **정리만** 한다: ① 중복 제거 ② 단가 0 이하 제거 ③ 결측치(rating/age) 중앙값으로 채우기 ④ 금액 이상치 **IQR 방식**으로 제거.
- 지역별·카테고리별 **요약표**(건수·총매출·평균평점)를 만든다.
- **SQLite DB**(`data/sales.db`)에 `sales_clean`, `summary_region`, `summary_category` 테이블로 저장. `clean_sales.csv`도 저장.

### STEP 3. AI로 분석 — `analyze.py`
- DB의 요약을 **작은 통계 텍스트**로 만들어 분석한다.
- 환경변수 `AI_MODE`로 3모드: `mock`(기본, 키 없이 통계 기반 분석문) / `claude`(`claude -p "..."`) / `codex`(`codex exec "..."`).
- **claude/codex가 없거나 실패하면 자동으로 mock으로 폴백**(수업이 멈추면 안 됨).
- 결과(인사이트·실행제안 또는 텍스트)를 `data/analysis.json`으로 저장.

### STEP 4. 보고서 만들기 — `report.py`
- **CSV**: 정리 데이터 + 지역/카테고리 요약(한글 그대로).
- **PDF**: matplotlib로 차트(카테고리·지역 매출 막대) + 핵심 숫자. (한글 폰트가 없으면 PDF 라벨은 영문으로 — 깨짐 방지)
- `reports/` 폴더에 저장.

### STEP 5. API 만들기 — `api.py` (+ 예제)
- **FastAPI**로 `GET /summary`, `GET /data?limit=`, `GET /analysis`, `GET /report.csv` 제공.
- 자동 문서 `/docs`가 열리게. `examples/api_client_example.py`로 requests 호출 예제도 만든다.

### STEP 6. 웹 UI + HTML 설명서 — `app.py`, `docs.html`
- **Streamlit** `app.py`: 사이드바 버튼으로 1)생성 2)전처리 3)AI분석 4)보고서를 순서대로 실행하고, 상단 지표·막대그래프·표·CSV/PDF 다운로드를 보여준다.
- **`docs.html`**: 위 모든 사용법을 담은 HTML 문서.

## 🧪 검증 (반드시 포함)
- `test_solution.py`를 만들어 6단계가 동작하는지 자동 확인:
  - 데이터 ≥1000행·결측치 존재 → 전처리 후 결측 0·단가>0·중복 0 → mock 분석 동작 → CSV·PDF 생성 → API 함수 응답.
- **만든 뒤 실제로 실행해서 통과("ALL PASS")를 확인**하고 알려줘.

## 📏 난이도·규칙 (초보자용)
- 파일은 **단계별로 하나씩**, 각 파일은 짧고 읽기 쉽게. 한글 주석을 충분히.
- 새 라이브러리 최소화(아래 env.md 목록 안에서). 어려운 개념(비동기·클래스 상속 등)은 피한다.
- 매 단계 **실행 → 확인 → 다음** 순서로 진행.

## 📦 제출물
- 위 파일들 + `reports/`의 CSV·PDF 결과 1세트 + 웹앱 화면 캡처 1장 + `test_solution.py` 통과 캡처.

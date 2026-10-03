# 실행 환경 명세 (env.md) — 로컬(내 PC) 기준

> `problem.md`와 함께 Claude Code/Codex에 붙여넣으세요. **모든 설치·실행은 내 컴퓨터(로컬)** 에서 합니다. (컨테이너·서버 없음)

## 운영체제 / 파이썬
- 내 PC (macOS / Windows / Linux 아무거나).
- Python **3.10 이상** 설치. 확인: `python3 --version`
- 작업 폴더: `educations/04_new_lectures/week06/project/` (완성 예시는 `solution/`).

## 1) 파이썬 라이브러리 설치 (로컬)
가상환경을 쓰면 깔끔합니다(선택):
```bash
python3 -m venv venv
source venv/bin/activate        # (Windows) venv\Scripts\activate
```
필요한 것만 설치:
```bash
pip install pandas numpy matplotlib streamlit fastapi uvicorn requests
# 또는:  pip install -r solution/requirements.txt
```
| 용도 | 패키지 |
| --- | --- |
| 데이터 | `pandas`, `numpy` |
| DB | `sqlite3` (파이썬 내장, 설치 불필요) |
| 차트·PDF | `matplotlib` |
| 웹 UI | `streamlit` |
| API | `fastapi`, `uvicorn` |
| HTTP 예제 | `requests` |
> `faker`는 쓰지 않습니다(numpy로 충분). 한글 폰트가 없는 PC도 있으니 **PDF 라벨은 영문**으로 하세요.

## 2) Claude CLI / Codex CLI 설치 (로컬, 선택)
AI 분석을 실제로 돌리려면 둘 중 하나를 로컬에 설치·로그인하세요. (안 해도 mock으로 동작)
```bash
# Claude Code CLI
npm install -g @anthropic-ai/claude-code      # 설치 후:  claude   로 로그인
# Codex CLI
npm install -g @openai/codex                  # 설치 후:  codex    로 로그인
```
사용:
```bash
AI_MODE=claude python3 analyze.py   # 로컬 Claude CLI 연동
AI_MODE=codex  python3 analyze.py   # 로컬 Codex CLI 연동
```
> **CLI가 없거나 로그인 안 됐으면 자동으로 mock으로 폴백**되게 만들 것(try/except + 타임아웃). 수업이 멈추면 안 됩니다.

## 3) 실행 방법 (로컬)
```bash
cd solution   # (또는 내가 만든 폴더)

# 단계별
python3 generate_data.py 10000
python3 preprocess.py
python3 analyze.py
python3 report.py

# 웹앱 (브라우저가 자동으로 열림: http://localhost:8501)
streamlit run app.py

# API (브라우저 문서: http://localhost:8600/docs)
uvicorn api:app --port 8600

# 검증
python3 test_solution.py      # "ALL PASS" 나오면 성공
```
> 로컬이라 **브라우저에서 바로** `localhost` 주소로 열립니다(포트포워딩 불필요).
> 포트가 겹치면 다른 번호 사용: `streamlit run app.py --server.port 8502`, `uvicorn api:app --port 8601`.

## 4) 결과물 위치
- 데이터·DB: `data/` (raw_sales.csv, sales.db, analysis.json)
- 보고서: `reports/` (clean_sales.csv, summary_*.csv, report.pdf)
- 폴더가 없으면 코드가 자동으로 만들게 하세요.

## 5) 비용
- 기본 **mock은 무료·무키**. claude/codex는 필요할 때만 소량 호출.

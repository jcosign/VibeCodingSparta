# 🧰 AI 업무 비서 대시보드

**이게 뭐야?** 매출 대시보드 + AI 요약 + 리뷰 분류를 한 화면(3탭)에 담은 Streamlit 앱입니다.

## 어떻게 켜?
```bash
pip install -r requirements.txt
./run.sh                          # http://localhost:8610
# bash가 없으면: streamlit run app.py --server.port 8610
```
검증: `python3 examples/example_01_integrated_report.py` → `END-TO-END OK`

## 뭘 볼 수 있어?
- 📊 **대시보드** - 총매출·총주문·1위 카테고리, 일별 추이, 카테고리/지역별 매출
- 🤖 **AI 요약** - 지표 다이제스트를 한 문단으로 요약 + 모드·토큰·비용
- 💬 **리뷰 분류** - 붙여넣은 리뷰를 긍정/부정/중립으로 분류 → 분포·표·CSV

## 키가 필요해?
아니요. 키가 없으면 **mock**(규칙 기반, 무료)으로 끝까지 동작합니다.
실제 AI는 `AI_MODE=anthropic` + `ANTHROPIC_API_KEY` (또는 `openai` + `OPENAI_API_KEY`)를 **환경변수로** 넣습니다.
키는 코드·파일·깃에 적지 않습니다(`.gitignore`에 `.env` 등록됨).

## 안 되면?
- 앱 안 뜸 → `pip install -r requirements.txt`
- 포트 충돌 → `--server.port 8611`
- AI 탭이 mock만 나옴 → 키/`AI_MODE` 확인. 키 없이도 정상(mock)입니다.
- 더 자세히: `INTEGRATION.md` 트러블슈팅

데이터(`data.py`)는 연습용 합성 데이터입니다. 실제 업무 데이터로 바꾸는 법은 `INTEGRATION.md` (C).

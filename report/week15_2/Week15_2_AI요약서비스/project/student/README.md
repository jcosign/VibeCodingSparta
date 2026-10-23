# AI 한 줄 요약 서비스
텍스트를 붙여넣으면 AI(Gemini)가 핵심을 1~5문장으로 요약합니다. 키가 없으면 mock(가짜 요약)으로 동작합니다.

## 실행
```bash
bash env_set_up.sh   # 최초 1회: .venv + 패키지 + 자동 검증
./run.sh             # http://localhost:8615 (키 없어도 mock으로 동작)
```

## 필요한 것
- Python 3.10 이상(권장 3.11~3.12), `pip install -r requirements.txt`
- (선택) `GEMINI_API_KEY` — 없으면 mock으로 동작. 키는 환경변수로만 넣고 코드·깃에 적지 않습니다.
- (선택) `GEMINI_MODEL` — 모델 이름 교체(기본 `gemini-2.5-flash`)

## 배포
`INTEGRATION.md` 참고(Google AI Studio 원클릭 권장 / Docker·Cloud Run / Streamlit Cloud).
배포가 어려우면 `./run.sh` 로컬 실행으로 제출합니다(완성·검증이 우선, 배포는 선택).

## 운영
- 헬스체크: `<앱 주소>/_stcore/health` → `ok`
- 로그: 터미널(로컬) 또는 Cloud Run Logs. 요청 길이·모드만 남기고 원문·키는 남기지 않습니다.
- 비용: 배포 직후 월 예산(billing cap)과 알림 설정.

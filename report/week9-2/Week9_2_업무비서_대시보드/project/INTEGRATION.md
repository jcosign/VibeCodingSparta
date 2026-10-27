# INTEGRATION — 확장 · 연동 가이드

(A) CLI 코딩 도구로 기능 추가 · (B) 실제 AI API 켜기 · (C) 내 데이터 연결 · (D) 배포(개념) · 트러블슈팅

---

## (A) CLI 코딩 도구로 기능 추가 (claude / codex)
```bash
cd project
claude        # 또는 codex  (나오려면 /exit 또는 Ctrl+C 두 번)
```
**좋은 지시 공식:** [어느 파일/화면] + [무엇을] + [데이터·조건 구체적으로] + [끝나면 어떻게 검증]

기간 필터 예시:
```
app.py 대시보드 탭에 '기간(날짜) 필터'를 추가해줘.
- data.py의 orders '날짜' 컬럼을 기준으로, 시작일~종료일을 고르는 날짜 슬라이더를 넣어줘.
- 슬라이더로 고른 기간에 맞춰 총매출·총주문·차트가 다시 계산되게 해줘.
- 다 하면 python3 examples/example_01_integrated_report.py 를 실행해서 오류 없는지 확인해줘.
```
CSV 버튼 예시:
```
app.py의 'AI 요약' 탭에서, 방금 만들어진 요약 문장을 CSV로 내려받는 버튼을 추가해줘.
- 리뷰 분류 탭의 st.download_button 방식과 똑같은 스타일로 해줘. (이미 있으니 참고해)
- 파일명은 ai_summary.csv, 인코딩은 utf-8-sig(엑셀 한글 안 깨지게)로 해줘.
- 끝나면 streamlit이 뜨는지 확인해줘.
```
❌ 나쁜 지시: "대시보드 좀 더 좋게 만들어줘", "다운로드 되게 해줘" (무엇을·어디에·어떻게가 없음)

**안전 3원칙:** ① 변경안(diff)을 읽고 승인 ② 바꾼 뒤 example_01로 즉시 검증 ③ 큰 변경 전 폴더 백업 또는 git 스냅샷.
이 폴더에 `.env`·키·개인정보 파일을 두지 마세요(도구가 폴더 안 파일을 읽습니다).

## (B) 실제 AI API 켜기
```bash
pip install anthropic                      # (OpenAI는 pip install openai)
export AI_MODE=anthropic
export ANTHROPIC_API_KEY=sk-...            # 환경변수로만! 코드·파일에 적지 않기
./run.sh
```
PowerShell:
```powershell
$env:AI_MODE="anthropic"; $env:ANTHROPIC_API_KEY="sk-..."
streamlit run app.py --server.port 8610
```
- 모드 판단 순서(`ai_client._auto_mode`): `AI_MODE` 값 → `ANTHROPIC_API_KEY` 있음 → `OPENAI_API_KEY` 있음 → 없으면 mock
- 기본 모델: `claude-haiku-4-5` / `gpt-4o-mini` (환경변수 `ANTHROPIC_MODEL`·`OPENAI_MODEL`로 교체)
- 호출이 실패하면(키 오류·네트워크·SDK 미설치) mock으로 대체되고, 모드 칸에 `mock(anthropic 실패: 오류이름)`이 보입니다.
- 비용 표시는 `ai_client._PRICE`의 **강의용 근사 단가**로 계산합니다. 실제 청구액은 각 회사 콘솔에서 확인하세요.
- 처음엔 **소량(5~10회)** 만 호출하고, 요약 속 숫자는 digest(원본)와 반드시 대조합니다.

## (C) 내 데이터 연결 (8주차 연결)
`data.py`의 함수가 **같은 컬럼의 DataFrame**을 돌려주면 `app.py`는 그대로 동작합니다.
- 주문: `주문번호 · 날짜 · 카테고리 · 지역 · 금액_만원`
- 리뷰: `카테고리 · 별점 · 리뷰`

CSV 예시:
```python
def orders_df():
    df = pd.read_csv("sales.csv")
    df["날짜"] = pd.to_datetime(df["날짜"]).dt.date
    return df
```
- 컬럼명이 다르면 `app.py`의 `'금액_만원'` 같은 이름을 내 데이터에 맞게 바꿉니다(CLI 도구에게 시켜도 됩니다).
- 8주차에 만든 API/DB에서 불러온다면, 그 결과를 위 컬럼의 DataFrame으로 바꿔 돌려주면 됩니다.
- 데이터가 무거워지거나 DB/API로 바꾸면 `app.py`에서 불러오는 함수에 `@st.cache_data`를 붙이세요.
- 개인정보가 있는 데이터는 AI에 보내기 전 `mask_pii()`로 치환하고, 원본 행이 아니라 **집계 요약**만 보냅니다.

## (D) 배포 (개념)
- 전달 3종 세트: `requirements.txt`(재료 목록) · `run.sh`(실행 버튼) · `README.md`(설명서)
- 재현성 사다리: requirements.txt → 가상환경(`python3 -m venv .venv`) → 컨테이너(OS·부품·설정을 통째로 담은 이미지를 클라우드에 올림)
- 키는 배포 플랫폼의 **시크릿**으로 넣고, `.env`는 전달·공유 대상에서 제외합니다.

전달 전 체크리스트:
- [ ] requirements.txt에 필요한 부품이 다 있다
- [ ] run.sh(또는 실행 방법)대로 하면 켜진다
- [ ] README에 켜는 법·기능·트러블슈팅이 있다
- [ ] example_01이 `END-TO-END OK`
- [ ] `.env`·API 키·개인정보 파일이 없다
- [ ] `__pycache__` 등 임시 파일을 지웠다

---

## 트러블슈팅
| 증상 | 해결 |
|---|---|
| 앱 안 뜸 / `streamlit: command not found` | `pip install -r requirements.txt` |
| 포트 충돌 | `streamlit run app.py --server.port 8611` |
| `./run.sh` 가 안 됨(Windows) | Git Bash/WSL에서 실행하거나 `streamlit run app.py --server.port 8610` |
| AI 탭이 mock만 나옴 | 키/`AI_MODE` 확인. 키 없이도 정상(mock) |
| `ModuleNotFoundError: No module named 'data'` | `app.py`·`data.py`가 같은 폴더인지, 터미널 위치가 `project`인지 확인 |
| `set_page_config` 관련 에러 | `set_page_config`를 다른 `st.` 명령보다 위로 |
| 탭 내용이 탭 밖에 그려짐 | `with tab1:` 아래 줄을 들여쓰기(공백 4칸) |
| `st.write(orders)`에 `<function ...>`이 뜸 | `orders = orders_df()` 처럼 괄호를 붙여 호출 |
| `print`가 화면에 안 보임 | `print`는 터미널에만 찍힘 → `st.write` 사용 |
| 한글 그래프 깨짐 | 라벨 영문 병기 |
| 엑셀에서 CSV 한글 깨짐 | `encode("utf-8-sig")`로 저장 |

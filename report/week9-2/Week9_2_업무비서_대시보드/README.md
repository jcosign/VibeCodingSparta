# Week09_02 토요일 프로젝트 — AI 업무 비서 대시보드 (통합 캡스톤)

Week09_02 Day1~4 교재, OX 퀴즈, `Week09_02_Project.pdf`를 바탕으로 만든 과제 폴더입니다.

- `project/` — 학생 배포용. 3탭 앱이 키 없이 돌아가는 상태이며, 과제(4단계 3~5번)를 붙일 위치에 `[과제 N단계]` 표시가 있습니다.
  - 과제 명세: `project/Week10_Project.md` (프로젝트 PDF 내용)
  - 따라하기: `project/과제안내_쉬운버전.md`
- `solution/app_solution.py` — 강사·채점용 예시 답안(기간·지역 필터, 경영진/실무진 톤, 카테고리별 부정 비율). **학생 배포 시 빼세요.**
  - 실행: `streamlit run solution/app_solution.py --server.port 8611` (Week9_2_업무비서_대시보드 폴더에서)

## 교재 코드를 그대로 옮긴 부분
- `requirements.txt` 전체(D4 3-2)
- `run.sh`의 의존성 확인·AI 모드 출력·`streamlit run app.py --server.port 8610` 줄(D4 3-3)
- `ai_client.py`: `_auto_mode()`(D3 1-2), `ask()`의 시그니처·try/except mock 폴백(D3 1-4), mock 요약 문구(D3 1-3), `_PRICE`·`_cost()`·기본 모델명(D3 2-2·2-3), `meta` 키 5개(D3 2-4), `safe_json()`·`mask_pii()`(D3 3-4·4-2)
- `app.py`: `set_page_config`·제목·부제·사이드바 문구(D2), `st.tabs` 3탭(D2), digest 계산식·AI 요약 system 프롬프트·`max_tokens=300`·모드/토큰/비용 지표·근거 데이터 expander(D3), 화면 구성(D1 와이어프레임)
- `data.py`: 함수 이름·인자(`orders_df(days=30, seed=42)`), 컬럼명, 시작일 2026-06-01, 카테고리 4종·지역 5종, `__main__` 자가 테스트(D1·D2·D4)
- `INTEGRATION.md`의 CLI 지시문 예시·안전 3원칙·트러블슈팅·전달 체크리스트(D2·D4)

## 실행 검증 결과 (2026-10-27, Windows 11, Python 3.12.10, streamlit 1.66.1, pandas 3.1.0, numpy 2.5.4)
- ✅ `python data.py` → orders 215행, reviews 120행, 총매출 3970만원, 평균 별점 3.25
- ✅ `examples/example_01_integrated_report.py` → `AI 모드: mock` … `토큰 in/out: 74/76 | 비용 $0.000000` → `END-TO-END OK`
- ✅ `examples/example_02_review_pipeline.py` → 감정 분포 {긍정 55, 부정 38, 중립 27}, 부정 비율 신발 39%·뷰티 35%·의류 32%·가방 21%, 별점 기준 일치율 100% → `END-TO-END OK`
- ✅ `max_tokens=60`으로 바꾸면 mock 출력이 60 토큰으로 잘림(D3 You Try 재현)
- ✅ `app.py`·`app_solution.py`: Streamlit AppTest로 3탭·지표·요약 버튼(모드/토큰/비용)·분류 버튼(긍정 비율·부정 건수)·rerun 후 요약 유지 확인, 예외 없음
- ✅ `app_solution.py`: 서울 필터 시 총매출 1,318만원 < 전체 3,970만원, 톤 변경 경고, 0건 필터에서도 앱 유지
- ✅ `AI_MODE=anthropic` + 가짜 키 → `mock(anthropic 실패: ModuleNotFoundError)`로 폴백(앱 안 죽음)
- ✅ 실제 서버 8610 포트 `/_stcore/health` → `ok`, `run.sh` LF 줄바꿈
- ❌ 미검증: `run.sh`를 bash로 직접 실행(이 PC에 bash 없음), 실제 Anthropic/OpenAI 응답(SDK 미설치·유효 키 없음), CLI 도구(claude/codex) 실습

## 확인이 필요한 부분
1. **원본 파일 없음** — 교재에 전체 코드가 나온 건 `requirements.txt`·`run.sh`뿐이고, 나머지는 교재에 발췌된 코드와 설명을 근거로 새로 작성했습니다. 강사용 원본이 있다면 대조가 필요합니다.
2. **숫자가 교재 예시와 다름** — 교재 출력 예시는 서로도 다릅니다(D1: 주문 약 180행·부정 비율 신발 40% 등 / D4: 총매출 4648만원·223건·평균별점 3.42, 부정 비율 의류 36%·가방 13% 등). 이 폴더의 합성 데이터는 215건·3970만원 등으로 나오며, 과제는 특정 숫자에 의존하지 않습니다. 학생 안내 시 "숫자는 교재와 다를 수 있음"을 알려 주세요.
3. **단가표(`_PRICE`)** — 교재 D3의 강의용 예시를 그대로 옮겼습니다(교재 스스로 "실제와 다를 수 있음"이라고 명시). 실제 단가로 쓰지 마세요.
4. **교재에 없어 추가한 것** — `classify()`의 단어 목록, mock 감정 분석의 주제 태깅, `current_mode()` 함수, mock이 `max_tokens`를 넘으면 잘라내는 동작(D3 You Try가 동작하도록), 결과를 `st.session_state`에 보관(다른 버튼으로 rerun돼도 결과 유지), 리뷰 입력창 기본값(샘플 15건), `run.sh`의 `.venv` 자동 활성화·`python` 대체 줄(Windows Git Bash 대비), `.gitignore`.
5. **파일명** — 프로젝트 PDF의 파일 목록과 Day 교재가 `project/Week10_Project.md`를 가리켜 그 이름을 그대로 썼습니다. Day 교재의 `concept/*.ipynb`는 프로젝트 파일 목록에 없어 만들지 않았습니다.
6. **FAQ 표기** — PDF의 `-server.port 8611`은 렌더링 과정에서 하이픈이 하나 빠진 것으로 보고 `--server.port 8611`로 적었습니다.
7. **mock의 톤 차이** — mock은 system 프롬프트를 쓰지 않으므로 4단계(경영진/실무진 톤)의 결과 차이는 실제 키를 켜야 보입니다. 과제안내에 적어 두었습니다.

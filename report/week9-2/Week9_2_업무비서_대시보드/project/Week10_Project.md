# 09_02주차 토요일 프로젝트 - AI 업무 비서 대시보드 (통합 캡스톤) 🧰

## 0. 한 줄 소개
매출을 **대시보드**로 보고, 지표를 **AI가 요약**하고, 리뷰를 **자동 분류**하는 나만의 업무 비서. 키 없이 즉시 실행.

## 🗺 전체 흐름
하나의 데이터(`data.py`)가 3개의 탭으로 갈라져 각각 결과를 냅니다.

```
data.py  (합성 매출·리뷰 데이터: orders_df() · reviews_df())
   │
app.py   (Streamlit 앱, 3탭)
   ├─ 📊 탭1 대시보드 → 지표: 총매출·총주문·1위 카테고리(st.metric) → 차트: 일별 추이 · 카테고리/지역별 매출
   ├─ 🤖 탭2 AI 요약  → 지표 다이제스트(digest) 문장 만들기 → AI 호출 ai_client.ask() (mock·anthropic·openai)
   │                   → 한 문단 요약 + 모드·토큰·비용 표시
   └─ 💬 탭3 리뷰 분류 → 리뷰 붙여넣기(text_area) → classify()로 감정 분류(긍정/부정/중립)
                       → 분포 차트 · 표 · CSV 내려받기
```

## 1. 이 프로젝트가 캡스톤인 이유
| 주차 | 배운 것 | 이 앱에서 |
|---|---|---|
| 5 | LLM·프롬프트·시스템프롬프트 | AI 요약의 system 프롬프트 |
| 6 | API·토큰·비용·JSON | `ai_client` (mock/anthropic/openai) + 토큰·비용 표시 |
| 7 | Agent·도구 | (확장) 요약→분류→저장을 이어붙이는 감각 |
| 8 | DB·API 서비스 | `data.py`를 API/DB로 교체(INTEGRATION) |
| 9 | Streamlit·대시보드·분류 | 📊 대시보드 · 💬 리뷰 분류 |

## 2. 화면(3탭)
- 📊 **대시보드** - 총매출·총주문·1위 카테고리 지표 + 일별 추이 + 카테고리/지역별 매출.
- 🤖 **AI 요약** - 지표 다이제스트를 AI가 한 문단 요약(모드·토큰·비용 표시).
- 💬 **리뷰 분류** - 리뷰 붙여넣기 → 감정 분포·표·CSV.

## 3. 성공 기준 ✅
- [ ] `streamlit run app.py` 오류 없이 뜬다(3탭 모두 동작).
- [ ] 대시보드에 지표·차트가 보인다.
- [ ] AI 요약 버튼이 요약(최소 mock)과 토큰/비용을 보여준다.
- [ ] 리뷰 분류가 분포·표·CSV를 만든다.
- [ ] (선택) `AI_MODE`+키로 실제 AI 요약, 또는 CLI로 기능 1개 추가.

## 4. 단계별 (5시간)
1. (30분) `./run.sh`로 실행, 3탭 둘러보기.
2. (50분) `data.py` · `app.py` 읽기, `example_01/02` 실행.
3. (60분) 대시보드에 필터(기간/지역) 추가.
4. (60분) AI 요약 프롬프트 다듬기(경영진용/실무진용 톤).
5. (40분) 리뷰 분류 결과에 카테고리별 부정 비율 추가(example_02 참고).
6. (40분, 선택) 실제 키 켜기 또는 CLI로 기능 추가.

## 5. 제출물
`app.py`(수정본), 3탭 화면 캡처, AI 요약 결과 캡처, 분류 CSV, "다음에 더 붙이고 싶은 기능" 메모.

## 6. FAQ
- 앱 안 뜸 → `pip install -r requirements.txt`
- AI가 mock만 → 키/`AI_MODE` 확인(키가 없으면 mock이 정상)
- 포트 충돌 → `--server.port 8611`
- 한글 그래프 깨짐 → 라벨 영문 병기

## 7. 더 해보기
부정 리뷰만 필터해 AI에게 "개선 액션 3가지" 요청 · 8주차 API로 데이터 교체 · 로그인/기간 비교 · 배포(개념).

## 파일
```
project/
├ Week10_Project.md    ← 이 문서(과제 명세)
├ 과제안내_쉬운버전.md  ← 단계별 따라하기
├ README.md            ← 처음 받은 사람용 안내
├ app.py               ← 3탭 앱 (여러분이 고칠 파일)
├ ai_client.py         ← mock/anthropic/openai 호출기 + classify·safe_json·mask_pii
├ data.py              ← 합성 주문·리뷰 데이터
├ requirements.txt
├ run.sh               ← 실행 버튼 (포트 8610)
├ INTEGRATION.md       ← CLI 확장·실제 API·데이터 연결·배포·트러블슈팅
└ examples/
   ├ example_01_integrated_report.py  ← 집계→AI 요약 검증 (END-TO-END OK)
   └ example_02_review_pipeline.py    ← 리뷰 분류→카테고리별 부정 비율
```

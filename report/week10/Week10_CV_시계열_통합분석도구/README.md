# Week10 토요일 프로젝트 — Computer Vision·시계열 통합 분석 도구 (웹앱)

Week10 Day1~4 교안(ViT·Diffusion·시계열 분석·시계열 예측), OX 퀴즈, `Week10_Project.pdf`를 바탕으로 만든 과제 폴더입니다.

- `project/student/` — 학생 배포용. 프로젝트 PDF의 파일 목록(10개)을 그대로 만들었습니다. PDF가 app.py·local_model.py를 "완성본"으로 규정하므로 앱은 바로 동작하는 상태이고, 과제는 실행·관찰·해석·캡처 + "더 해보기" 확장입니다.
  - 과제 명세: `Week10_Project.md` (프로젝트 PDF 내용)
  - 교안 ↔ 코드 연결표·트러블슈팅: `INTEGRATION.md`
  - 따라하기: `과제안내_쉬운버전.md`

## 교안 내용을 그대로 옮긴 부분
- 모델 ID: `WinKawaks/vit-tiny-patch16-224`(프로젝트 PDF), `segmind/tiny-sd`(D2·프로젝트 PDF)
- 함수 이름: `classify_image()`·`_load_vit()`·`generate_image()`·`_load_diffusion()`·`load_sample_airpassengers()`·`forecast_timeseries()`·`augment()`(프로젝트 PDF 3장)
- `pipe(prompt, num_inference_steps=10, guidance_scale=7.0, generator=generator)`, `safety_checker=None`, 256×256·seed 0, 기본 프롬프트(D2)
- `get_rdataset("AirPassengers", "datasets")` + `date_range("1949-01-01", freq="MS")`(D4 1-1), 오프라인 백업 데이터 전환(D3 실전 예제)
- `ExponentialSmoothing(trend="add", seasonal="mul", seasonal_periods=12, initialization_method="estimated")`, `smoothing_level/trend/seasonal`(D4 1-3), `mae()`·`mape()`(D4 4-2), seasonal_periods 표(D4 FAQ Q6)
- 탭 구성·버튼 이름("이미지 생성하기", "예측 실행")·스텝 슬라이더 4~30·"🤖 Claude CLI 해설" 박스·CLI 없을 때 조용히 skip(프로젝트 PDF 4·5·7장)

## 실행 검증 결과 (2026-10-27, Windows 11, Python 3.12, CPU)
설치 버전: streamlit 1.66.1, torch 2.14.1+cpu, transformers 5.21.0, diffusers 0.42.0, accelerate 1.15.0, statsmodels 0.15.0, scikit-image 0.26.0, pandas 3.1.0, numpy 2.5.4, pillow 13.0.0
- ✅ `python local_model.py` → alpha 0.3762 / beta 0.0000 / gamma 0.6238, **MAE 10.30 / MAPE 2.21%** — D4 교안 1-3 수치와 일치
- ✅ 내장 백업 AirPassengers 144개 값 = `get_rdataset` 원본과 완전히 일치, 평균 280.3(D4 4-1 표와 일치)
- ✅ ViT-Tiny 로드 → "검증 성공: ViT-Tiny 모델 로드 완료". 샘플 분류 1위: chelsea → Egyptian cat 73.87%, coffee → espresso 96.47%, astronaut → oxygen mask 20.85%(낮은 확신도 = 검수 필요 사례로 활용 가능)
- ✅ tiny-sd 생성 256×256: 4스텝 6.7초 / 10스텝 13.3초 / 30스텝 35.6초, 같은 seed → 동일 이미지, 다른 seed → 다른 이미지, 10스텝 평균 밝기 133.0(D2 4-5 표의 bookstore_cafe 133.0과 일치)
- ✅ CSV 처리: 월별 36개 정상 예측, 10개(주기×2 미만) → 계절성 없이 예측+안내, 0 이하 값 → add로 전환+안내, 일별 period 7 정상, 빠진 날짜 → 오류 안내
- ✅ Streamlit AppTest: 3탭 렌더, 탭1 Top-5 표, 탭2 이미지 생성, 탭3 지표 3개+표 12행, 예외 없음
- ✅ 가짜 `claude` 명령 + `USE_CLAUDE_CLI=1 USE_CODEX_CLI=1` → Claude 해설 박스만 표시, Codex(미설치)는 조용히 skip. 플래그 없을 때 `augment()` → `{}`
- ✅ 실제 서버 `/_stcore/health` → `ok`, `env_set_up.sh` LF 줄바꿈
- ❌ 미검증: `bash env_set_up.sh` 직접 실행(이 PC에 bash 없음 — 같은 4단계를 PowerShell로 수행해 확인), `docker build`(Docker 없음), 실제 Claude/Codex CLI 응답(미설치)

## 확인이 필요한 부분
1. **원본 코드 없음** — 프로젝트 PDF에는 파일 목록·함수 이름·모델 ID만 있고 코드 본문은 없습니다. 교안 발췌 코드와 설명을 근거로 새로 작성했습니다. 강사용 원본이 있다면 대조가 필요합니다.
2. **생성 속도** — 교안은 "CPU 10스텝 약 2초"인데 이 PC에서는 약 13초였습니다. CPU 성능 차이로 보이며, 쉬운버전 안내에는 "몇 초~십수 초"로 적었습니다(Week10_Project.md는 PDF 원문 유지).
3. **CLI 명령** — 교안에 CLI 호출 명령은 나오지 않아, 각 도구의 비대화형 실행 방식(`claude -p`, `codex exec`)을 사용했습니다.
4. **교안에 없어 추가한 것** — `series_from_csv()`(CSV 정렬·빈도 확인), 짧은 데이터/0 이하 값 자동 처리, 탭3 계절 주기·계절성 형태 선택과 "샘플 CSV 내려받기" 버튼, 결과를 `st.session_state`에 보관(입력을 바꾸면 이전 결과 숨김), `CLI_TIMEOUT_SEC`, requirements의 `accelerate`, Windows용 경로·PowerShell 안내.
5. **D1 예제 파일** — 단계 ③의 `Week10_Day1_example_02_vit_batch_classify.py`는 교안 example 폴더 소관이라 만들지 않았습니다.
6. **solution 없음** — PDF가 앱을 완성본으로 제공하는 구조라 별도 정답 파일은 만들지 않았습니다. "더 해보기" 예시 답안이 필요하면 요청해 주세요.

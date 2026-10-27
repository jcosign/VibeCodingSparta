# Week11 토요일 프로젝트 — LLM 검색·Audio·에이전트 실행환경 통합 도구 (웹앱)

Week11 Day1~4 교안(토큰화·어텐션 / 임베딩·ReRank / Audio AI / E2B 샌드박스), OX 퀴즈, `Week11_Project.pdf`를 바탕으로 만든 과제 폴더입니다.

- `project/student/` — 학생 배포용. 프로젝트 PDF의 파일 목록(10개)을 그대로 만들었습니다. PDF가 app.py·local_model.py를 "완성본"으로 규정하므로 앱은 바로 동작하는 상태이고, 과제는 실행·관찰·해석·캡처 + "더 해보기" 확장입니다.
  - 과제 명세: `Week11_Project.md` (프로젝트 PDF 내용)
  - 교안 ↔ 코드 연결표·트러블슈팅: `INTEGRATION.md`
  - 따라하기: `과제안내_쉬운버전.md`

## 교안 내용을 그대로 옮긴 부분
- 모델 ID: `sentence-transformers/all-MiniLM-L6-v2`, `cross-encoder/ms-marco-MiniLM-L-6-v2`(D2·프로젝트 PDF), Whisper `tiny`(D3·프로젝트 PDF)
- 함수 이름: `search_and_rerank()`·`_load_embed_model()`·`_load_rerank_model()`·`transcribe_audio()`·`_load_whisper()`·`run_in_local_sandbox()`·`try_e2b_sandbox()`·`augment()`(프로젝트 PDF 3장·FAQ)
- `bi_encoder_rank()`·`cross_encoder_rank()` 본문(D2 코드 뜯어보기 ③), 기본 질문·FAQ 4문장(D2 2-4)
- `whisper.load_model("tiny")` → `transcribe()` → `text`·`language`(D3 2-4), `initial_prompt` 인자(D3 3-5-1)
- E2B 가드 패턴·`Sandbox.create(allow_internet_access=False)`·`run_code()`·`finally: kill()`(D4 2-4·2-7·2-8), `subprocess.run(timeout=)`·`resource.setrlimit`·상태 이름(D4 3-2·3-3·3-5)
- 탭 구성·버튼 이름("검색 실행", "전사 실행", "코드 실행")·업로드 형식 wav/mp3/m4a/aiff·"로컬 대체 샌드박스를 사용했습니다" 안내·"🤖 Claude CLI 해설" 박스·CLI 없을 때 조용히 skip·`env_set_up.sh` 4단계 ffmpeg 확인과 "검증 성공: 임베딩 모델 로드 완료"(프로젝트 PDF 2·4·5·7장)

## 실행 검증 결과 (2026-10-27, Windows 11, Python 3.12, CPU)
설치 버전: streamlit 1.66.1, torch 2.14.1+cpu, transformers 5.21.0, sentence-transformers 6.2.0, openai-whisper 20250625, e2b-code-interpreter 2.11.5, pandas 3.1.0, numpy 2.5.4
- ✅ `python local_model.py` → 바이 인코더 0.5617 / 0.4910 / 0.2869 / 0.2153, 크로스 인코더 8.0181 / 7.8897 / 7.3644 / 7.2902 — D2 2-4 표와 일치(반품 점수만 교안 7.8896과 넷째 자리 반올림 차이)
- ✅ D2 2-5 사례 B 문서로 탭1 실행 → 바이 0.7242/0.7023/0.6739/0.6400, 크로스 8.4563/7.9390/7.8227/7.7085 — 교안과 일치, 1위 불일치 경고 표시
- ✅ Whisper-tiny 파라미터 37,184,640개, 지원 언어 100개 — D3 2-3·2-3-1과 일치
- ✅ 탭2 전사(Windows 음성합성으로 만든 wav, 테스트용 ffmpeg 사용): 영어 3문장 모두 `en` 감지, "three o'clock" → "3 o'clock"(D3 2-4와 같은 현상). 한국어 문장 `ko` 감지, "연차는 사내" → "연찰은 사회"로 오인식(실습 관찰거리로 활용 가능). 전사 0.6~0.9초
- ✅ ffmpeg가 없을 때 → `FileNotFoundError`, 탭2가 설치 안내 표시(앱은 죽지 않음)
- ✅ 탭3: 정상 → 완료 `1~100 합계: 5050` / `while True: pass`·2초 → 시간초과(강제종료) 2.02초 / `1/0` → 오류 + ZeroDivisionError / 샌드박스 안에서 pandas 사용 가능
- ✅ `E2B_API_KEY` 없음 → `None` → 로컬 대체 + 안내 문구. 틀린 키 → `AuthenticationException` 오류 표시(로컬로 몰래 실행하지 않음)
- ✅ Streamlit AppTest: 3탭 렌더, 탭1 두 표, 탭2 전사 결과·지표 2개, 탭3 상태·stdout·stderr, 예외 없음
- ✅ 가짜 `claude` 명령 + `USE_CLAUDE_CLI=1 USE_CODEX_CLI=1` → Claude 해설 박스만 표시, Codex(미설치)는 조용히 skip. 플래그 없을 때 `augment()` → `{}`
- ✅ 실제 서버 `/_stcore/health` → `ok`, `env_set_up.sh` LF 줄바꿈, `winget` ID `Gyan.FFmpeg` 존재 확인
- ❌ 미검증: `bash env_set_up.sh` 직접 실행(이 PC에 bash 없음 — 같은 단계를 PowerShell로 수행해 확인), `docker build`(Docker 없음), 실제 E2B 클라우드 실행(유효한 API 키 없음), 실제 Claude/Codex CLI 응답(미설치), macOS `say`로 만든 음성(Windows라 SAPI 음성으로 대체)

## 확인이 필요한 부분
1. **원본 코드 없음** — 프로젝트 PDF에는 파일 목록·함수 이름·모델 ID만 있고 코드 본문은 없습니다. 교안 발췌 코드와 설명을 근거로 새로 작성했습니다. 강사용 원본이 있다면 대조가 필요합니다.
2. **D3 전문용어 오류 재현 안 됨** — D3 교안은 macOS `say` 음성으로 "Speech Recognition" → "Speed Track Ignition" 오류를 재현했지만, 이 PC의 Windows 음성(Zira)으로 만든 파일은 처음부터 정확히 인식했습니다. 음성 엔진이 달라 결과가 다른 것으로 보이며, 안내 문서에는 이 오류가 "반드시 나온다"고 쓰지 않았습니다.
3. **E2B SDK 버전** — 교안은 `e2b-code-interpreter 2.4.1` 기준, 설치된 것은 2.11.5입니다. 사용한 API(`create`·`run_code`·`kill`·`allow_internet_access`·`logs.stdout/stderr`·`error`)는 두 버전 모두 존재하지만, 키 없을 때 에러 문구가 조금 다릅니다("Team tab" → "API Keys tab").
4. **교안에 없어 추가한 것** — `run_in_local_sandbox()`의 `-I`·`-X utf8` 플래그와 실행마다 새 임시 폴더, `try_e2b_sandbox()`의 실행 `timeout`과 오류 시 dict 반환, `transcribe_audio()`의 `fp16=False`(CPU FP16 경고 끔)와 전사 시간, 업로드 파일 임시 저장 후 삭제, 탭3 시간 제한 슬라이더(1~30초), 탭1 1위 불일치 경고, 결과를 `st.session_state`에 보관(입력을 바꾸면 이전 결과 숨김), `CLI_TIMEOUT_SEC`, Windows용 ffmpeg 설치 명령·PowerShell 안내.
5. **"더 해보기" 항목은 넣지 않음** — top_k 슬라이더, 탭2 `initial_prompt` 입력칸, `SAFE_BUILTINS`는 과제로 남겼습니다(`transcribe_audio()`는 `initial_prompt` 인자만 받을 수 있게 준비).
6. **D3·D4 예제 파일** — 단계 ③·④·더 해보기의 `Week11_Day2_example_02_...`·`Week11_Day3_example_02_...`·`Week11_Day4_example_02_...`는 교안 example 폴더 소관이라 만들지 않았습니다.
7. **solution 없음** — PDF가 앱을 완성본으로 제공하는 구조라 별도 정답 파일은 만들지 않았습니다. "더 해보기" 예시 답안이 필요하면 요청해 주세요.

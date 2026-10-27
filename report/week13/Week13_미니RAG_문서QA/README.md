# Week13 토요일 프로젝트 — 미니 RAG 문서 Q&A (웹앱)

Week13 Day1~4 교안(LLM 한계·RAG 배경 / 임베딩·코사인 유사도 / VectorDB(Chroma) / 청킹·출처 기반 답변)과 `Week13_Project.pdf`를 바탕으로 만든 과제 폴더입니다.

- `project/student/` — 학생 배포용. 프로젝트 PDF의 파일 목록(15개 항목)을 그대로 만들었습니다. 앱은 바로 동작하는 완성본이고, 과제는 실행·관찰·캡처 + "더 해보기" 확장입니다.
  - 과제 명세: `Week13_Project.md` (프로젝트 PDF 내용, 흐름도는 Mermaid로 옮김)
  - 교안 ↔ 코드 연결표·실측 비교·트러블슈팅: `INTEGRATION.md`
  - 따라하기: `과제안내_쉬운버전.md`
  - `.venv/` — 검증에 쓴 가상환경(약 1.5GB). 배포할 때는 빼고 `env_set_up.sh`로 다시 만들면 됩니다.
- `검증/` — 학생 폴더 밖에 둔 검증 도구. `compare_embeddings.py`(임베딩 방식별 실측), `test_app.py`(Streamlit AppTest), `fake_cli/`(외부 호출 없이 CLI 경로를 시험하는 가짜 `claude`).

## 교안 내용을 그대로 옮긴 부분
- 함수 본문: `chunk()`(D4 1-3), `cosine()`(D2 3-2), `MiniRAG.__init__()`·`add()`·`build()`·`search()`(D3 2-2~3-6), `answer()`의 흐름·답변 형식·반환 `(답변, hits)`(D3 3-5·D4 3-2)
- `docs.py` DOCS 중 4건(반품정책·배송기간·포인트적립·환불처리) 본문(D1 3-2·D3 2-1), `docs.py`의 `__main__`(D4 1-3 You Try)
- 예제: `max(cands, key=lambda c: cosine(q, embed(c)))`·"배송이 느려요" 순위(D2 3-3), 정답 표 정확도 코드(D3 4-3)
- 프로젝트 PDF: 파일 목록, 모델 `intfloat/multilingual-e5-small`·384차원, `_load_model()` 전역 캐시, `USE_CLAUDE_CLI`/`USE_CODEX_CLI`·미설치 시 조용히 skip, 박스 제목 "🤖 Claude CLI가 다듬은 답변", `env_set_up.sh`의 "검증 성공: 임베딩 모델 로드 완료", k 조절

## 실행 검증 결과 (2026-10-27, Windows 11, Python 3.12.10)
설치 버전: torch 2.14.1(CPU), sentence-transformers 6.2.0, transformers 5.21.0, chromadb 1.5.9, streamlit 1.66.1, pandas 3.1.0
- ✅ `python docs.py` → 문서 수 8, 청크 3개
- ✅ `python embed.py` → 벡터 길이 384, 소수점 실수 벡터(앞 5칸 `0.0243, -0.0166, -0.0708, -0.0937, 0.0924`). 모델 파일 `model.safetensors` 448.8MB(PDF의 "약 450MB"와 일치)
- ✅ `python rag.py` → `Chroma: True`, "반품하고 싶어요" 근거 1위 반품정책(0.8657), "돈을 다시 돌려받고 싶어요" 1위 환불처리(0.8235)
- ✅ Chroma를 막은 폴백 실행 → `Chroma: False`, 점수까지 Chroma와 동일
- ✅ `examples/example_01` → `END OK`, `examples/example_02` → 정답 표 6/6, "우리 회사 주가" → "관련 문서를 찾지 못했어요.", `END OK`
- ✅ 임베딩 비교(질문 12개): 해시 8/12, all-MiniLM-L6-v2 4/12(“배송 얼마나 걸려요?” → 배송기간 8위로 꼴찌 — PDF FAQ의 주장 재현), multilingual-e5-small 11/12
- ✅ Streamlit AppTest: 답변·근거 표, k=3 변경, 임계값 미달 시 경고, 예시 버튼, 예외 없음
- ✅ 가짜 `claude` + `USE_CLAUDE_CLI=1 USE_CODEX_CLI=1`: Claude 박스 표시, 미설치 Codex는 조용히 skip / 근거에 없는 "14일"을 쓴 답 → 숫자 경고 표시
- ✅ 실제 서버 `streamlit run app.py` → `/_stcore/health` `ok`
- ✅ `env_set_up.sh`의 두 파이썬 검증 블록 단독 실행 → "검증 성공: 임베딩 모델 로드 완료", "Chroma 확인: 1.5.9". `env_set_up.sh`·`run.sh`는 LF 줄바꿈·BOM 없음
- ❌ 미검증: `bash env_set_up.sh` 통째 실행(이 PC에 bash 없음 — 같은 단계를 PowerShell로 수행했고 `env_set_up.log`는 만들지 않음), `docker build`(Docker 없음), 실제 Claude/Codex CLI 응답(미설치. 특히 Windows npm `.cmd` 래퍼에 여러 줄 프롬프트를 인자로 넘기는 동작은 실제 CLI로 확인하지 못함), macOS/Linux

## 확인이 필요한 부분
1. **원본 코드 없음** — 프로젝트 PDF에는 파일 목록·흐름도·성공 기준만 있고 `app.py`·`embed.py`·`cli_augment.py` 본문은 없습니다. 교안 발췌와 PDF 설명을 근거로 새로 작성했습니다. 강사용 원본이 있다면 대조가 필요합니다.
2. **DOCS 4건은 새로 작성** — 교환방법·회원등급·쿠폰사용·고객센터 본문은 교안에 없습니다. 회원등급의 할인율(실버 5%·골드 10%·VIP 15%)만 D4 2-2 예시에서 가져왔고, 나머지(VIP 기준 50만 원, 교환 7일, 쿠폰 1장, 상담 시간 등)는 제가 정한 가짜 샘플입니다. 문서 순서는 D1 3-2 발췌 순서(반품→배송→포인트→환불)를 따랐습니다.
3. **임계값 `MIN_SCORE = 0.80` 추가** — 교안 `answer()`는 `if not hits`만 검사하는데 `search()`는 항상 k개를 돌려줘서 "못 찾았다"가 사실상 나오지 않습니다. D4 부록 FAQ의 "임계값"을 넣었지만, **실측상 답 있는 질문(0.81~0.90)과 답 없는 질문(0.78~0.87)의 점수가 겹쳐** 5개 중 1개만 걸러집니다. "해외 배송도 되나요?"는 배송기간 문서가 그대로 나옵니다(INTEGRATION.md §4). 또 교안과 달리 "못 찾았다"일 때도 근거 목록은 비우지 않고 돌려줍니다(사람이 점수를 볼 수 있게).
4. **교안과 실측이 다른 부분** —
   - D2 3-4 "실무 의미 임베딩이라면 '느려요 vs 빨라요'를 낮게 매긴다" → e5-small 실측은 "배송이 빨라요" 0.931 > "배송 지연 불만" 0.909로 **역시 구별하지 못함**.
   - D1·D3·D4 교안의 `rag.py` 예시 출력 점수(0.71/0.42, 0.42/0.19 등)는 해시 임베딩 기준이라 이번 모델 점수(0.82~0.87)와 다릅니다.
   - D4 1-3의 `chunk(…, 20)` 예시 출력 첫 조각 "구매 후 7일 이내 미개봉 상품은 무료"는 21글자라 size=20으로는 나올 수 없습니다. 실제 출력은 `'구매 후 7일 이내 미개봉 상품은 무'`.
5. **PDF FAQ 문구 수정** — "multilingual-e5-small은 매번 정답 문서를 1위로 찾았다"는 이 폴더의 실측(11/12, 교환방법 질문 1개 오답)과 달라 숫자로 바꿨습니다. "MiniLM에서 배송기간 꼴찌", "약 450MB"는 실측으로 확인되어 그대로 두었습니다.
6. **교안에 없어 추가한 것** — e5 접두어(`query: `/`passage: `, 실측 11/12 vs 접두어 동일 10/12), `MiniRAG.uses_chroma`, CLI 답변의 숫자 대조 경고(`unverified_numbers`), 사이드바 임계값 슬라이더·지식베이스 보기·예시 질문 버튼, `EMBED_MODEL`·`CLI_TIMEOUT_SEC` 환경변수, Dockerfile의 CPU 전용 torch 설치와 빌드 시 모델 사전 다운로드(미검증).
7. **넣지 않은 것** — 겹침 청킹 `chunk_overlap`(D4 2-2 개념 코드, 과제 "더 해보기"), 긴 문서 청킹 색인, 교안 concept/example 폴더의 `Week13_DayN_...` 파일(교안 소관), solution 파일(앱이 완성본으로 제공되는 구조).

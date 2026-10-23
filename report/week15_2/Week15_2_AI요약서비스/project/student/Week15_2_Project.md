# Week15_2_Project — 배포용 AI 요약 서비스 ✍️ (end-to-end)

> 작고 깔끔한 AI 앱을 만들어 실제로 배포까지. Google AI Studio 원클릭 배포 또는 Dockerfile.
> 난이도: 중 · 웹 UI: Streamlit · 배포: AI Studio/Cloud Run/Docker

## 0. 한 줄 소개
텍스트를 붙여넣으면 AI가 요약하는 한 기능 앱 → **누구나 접속하는 URL**로 배포.

## 1. 왜 '한 기능' 앱인가
배포를 처음 배울 땐 기능이 작아야 좋습니다. 요약 하나에 집중해 **개발→배포→운영** 전 과정을 경험합니다.

## 2. D1~D4 연결
| Day | 프로젝트 |
|---|---|
| D1 앱 구조·배포 개념 | 배포 옵션 비교, 배포 3요소(run.sh·requirements.txt·환경변수) |
| D2 AI Studio로 앱 만들기 | Build(Vibe Coding) → 결과물이 `app.py` |
| D3 원클릭 Cloud Run 배포 | Deploy + `$PORT` 규약 + 키·비용 |
| D4 운영·로컬 백업 | 로그·헬스(`/_stcore/health`)·재현성·`./run.sh` |

## 3. 성공 기준 ✅
- [ ] `bash env_set_up.sh` 실행이 끝까지 오류 없이 완료된다(로그 끝부분에 mock 응답 출력이 보인다).
- [ ] `./run.sh` (또는 `streamlit run app.py`)로 로컬 실행(요약 동작). ← 1순위
- [ ] `docker build` 성공(또는 AI Studio 배포 URL 발급).
- [ ] 키는 환경변수로, 비용 상한 설정.

## 4. 실행 & 배포
```bash
cd project/student && bash env_set_up.sh   # 환경 설정 + 자동 검증
source .venv/bin/activate                  # (Windows는 .venv\Scripts\activate)
./run.sh                                   # 로컬 실행 → http://localhost:8615
docker build -t ai-summary .               # 컨테이너 이미지
```
배포: `INTEGRATION.md` 참고(AI Studio 원클릭 권장).

## 5. 제출물
로컬 실행 캡처, **배포 URL(또는 docker build 로그)**, 환경변수/비용 설정 캡처, README.

## 6. 더 해보기
요약 대상 확장(URL·PDF), 사용량 로그, 커스텀 도메인.

## 파일
```
project/student/
├── Week15_2_Project.md   ← (이 문서) 프로젝트 소개
├── README.md             ← 앱 README(뭐하는 앱·실행·필요한 것·배포) — 제출용
├── INTEGRATION.md        ← 배포 가이드(AI Studio·Cloud Run·Docker·Streamlit Cloud) + 트러블슈팅
├── 과제안내_쉬운버전.md   ← 비전공자용 아주 쉬운 안내
├── app.py                ← Streamlit 앱
├── gemini_client.py      ← Gemini 공용 호출기(mock 우선)
├── requirements.txt      ← 패키지 목록
├── env_set_up.sh         ← 환경 자동 설정 + 검증 스크립트
├── run.sh                ← 로컬 실행 스크립트(PORT 환경변수 대응)
├── Dockerfile            ← 컨테이너 배포용
├── .dockerignore
├── .env.example          ← 환경변수 예시(.env로 복사해 사용)
└── examples/             ← example_01_config_check.py, example_02_deploy_readiness.py
```

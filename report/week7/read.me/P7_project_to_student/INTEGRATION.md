# 연동 가이드 — DB 교체 · CLI · (선택) AI API

## (A) TinyDB → MongoDB 교체
이 프로젝트는 서버 없이 배우도록 **TinyDB(문서형 DB)** 를 씁니다. 개념(컬렉션·문서·쿼리)은 MongoDB와 같습니다.
```python
# store.py를 MongoDB로 바꾸는 개념(요지)
from pymongo import MongoClient
db = MongoClient("mongodb://localhost:27017").shop
db.orders.insert_many(docs)                 # Create
db.orders.find({"category":"의류"})          # Read/Query (TinyDB search와 같은 개념)
```
- `pip install pymongo`, MongoDB 서버(또는 Atlas) 필요. 컨테이너 실습은 TinyDB로 충분.

## (B) CLI로 엔드포인트 확장 — claude / codex
```bash
cd <프로젝트 폴더>
claude    # 또는 codex
```
예: *"api.py에 '지역별 매출' 집계 엔드포인트 `/stats/region`을 추가하고, store.py에 함수도 만들어줘. TestClient로 되는지 확인까지."*
- 수정 후 `python3 examples/example_02_api_testclient.py`로 직접 검증.

## (C) (선택) AI로 통계 요약
`/stats` 결과를 6주차 `ai_client` 패턴으로 AI에게 넘겨 "한 줄 요약"을 만들 수 있습니다(mock 우선, 키 있으면 실제).

## 트러블슈팅
- 포트 충돌: `uvicorn api:app --port 8001`, `streamlit run app.py --server.port 8605`.
- 프론트가 API를 못 찾으면 → 자동으로 store 직접 읽기("직접(store)" 표시)로 실습은 계속됩니다.

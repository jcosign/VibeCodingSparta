# 연동 가이드 — 분류기 교체 · CLI · (선택) AI API

## (A) 규칙 기반 → HuggingFace 교체
기본은 **규칙 기반**(키·모델 불필요, 컨테이너 즉시 실행). 실제 모델을 쓰려면:
```bash
pip install transformers torch    # 모델 다운로드(용량 큼, 네트워크 필요)
CLF_MODE=hf streamlit run app.py  # HuggingFace 파이프라인 사용
```
- `classifier.py`의 `classify_hf()`가 `pipeline("sentiment-analysis")`를 씁니다. 실패 시 자동으로 규칙 기반 대체.
- 더 정확히: 한국어 감정 모델(예: `beomi/KcELECTRA`류)로 `pipeline(model=...)` 지정.

## (B) LLM API로 분류(6주차 방식)
`ai_client` 패턴으로 LLM에게 JSON 분류를 시킬 수도 있습니다(mock 우선, 키 있으면 실제). 규칙/HF/LLM 셋 다 "분류기"입니다.

## (C) CLI(claude/codex)로 대시보드 확장
`claude`/`codex`에게 "카테고리별 긍/부정 비율 그래프 탭을 추가해줘. 규칙 기반 유지하고 streamlit 실행 확인까지." 처럼 시켜보세요.

## 트러블슈팅
- 앱 안 뜸 → `pip install -r requirements.txt`. 포트 충돌 → `--server.port 8607`.
- HF가 느리거나 실패 → 자동으로 규칙 기반으로 떨어집니다(정상).

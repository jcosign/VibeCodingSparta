#!/usr/bin/env bash
# env_set_up.sh - 환경 자동 설정
#   1) 가상환경(.venv) 생성  2) requirements.txt 설치
#   3) 임베딩 모델 검증(최초 1회 모델 다운로드 → 실제 벡터 생성)  4) Chroma 확인
# 모든 출력은 env_set_up.log 에도 함께 저장됩니다.
set -euo pipefail
cd "$(dirname "$0")"

LOG=env_set_up.log
exec > >(tee "$LOG") 2>&1

PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
echo "사용할 파이썬: $("$PY" --version 2>&1)"

echo "[1/4] 가상환경(.venv) 생성"
[ -d .venv ] || "$PY" -m venv .venv
# macOS/Linux는 .venv/bin, Windows(Git Bash)는 .venv/Scripts
if [ -f .venv/bin/activate ]; then source .venv/bin/activate; else source .venv/Scripts/activate; fi
python -m pip install --upgrade pip

echo "[2/4] requirements.txt 설치 (torch 포함이라 처음엔 몇 분 걸릴 수 있습니다)"
python -m pip install -r requirements.txt

echo "[3/4] 임베딩 모델 검증 (최초 1회는 모델 약 450MB 다운로드)"
python - <<'EOF'
from embed import MODEL_NAME, DIM, embed
v = embed("배송이 너무 느려요")
assert len(v) == DIM, f"벡터 길이가 {len(v)}입니다(기대: {DIM})"
print("모델:", MODEL_NAME, "| 벡터 길이:", len(v), "| 앞 3칸:", [round(x, 4) for x in v[:3]])
print("검증 성공: 임베딩 모델 로드 완료")
EOF

echo "[4/4] Chroma 확인"
python - <<'EOF'
try:
    import chromadb
    print("Chroma 확인:", chromadb.__version__)
except ImportError:
    print("⚠️ chromadb가 없습니다 → rag.py가 순수 파이썬 코사인 검색으로 자동 대체합니다(실습은 그대로 진행 가능).")
EOF

echo ""
echo "다음 단계:"
echo "  source .venv/bin/activate   (Windows Git Bash: source .venv/Scripts/activate)"
echo "  python3 embed.py && python3 rag.py"
echo "  streamlit run app.py"

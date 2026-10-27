#!/usr/bin/env bash
# env_set_up.sh - 환경 자동 설정
#   1) 가상환경(.venv) 생성  2) PyTorch(CPU 전용) 설치  3) requirements.txt 설치  4) ViT-Tiny 모델 로드 검증
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

echo "[2/4] PyTorch(CPU 전용) 설치 - GPU용보다 용량이 작습니다"
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu

echo "[3/4] requirements.txt 설치"
python -m pip install -r requirements.txt

echo "[4/4] ViT-Tiny 모델 로드 검증 (최초 1회 모델 다운로드)"
python -c "import local_model as lm; lm._load_vit(); print('검증 성공: ViT-Tiny 모델 로드 완료')"

echo ""
echo "다음 단계:"
echo "  source .venv/bin/activate   (Windows Git Bash: source .venv/Scripts/activate)"
echo "  streamlit run app.py"

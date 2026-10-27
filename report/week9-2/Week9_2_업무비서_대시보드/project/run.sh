#!/usr/bin/env bash
set -e; cd "$(dirname "$0")"
# 가상환경(.venv)이 있으면 자동으로 켠다 (Windows Git Bash는 .venv/Scripts)
if [ -f .venv/bin/activate ]; then source .venv/bin/activate
elif [ -f .venv/Scripts/activate ]; then source .venv/Scripts/activate; fi
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
"$PY" -c "import streamlit,pandas,numpy" 2>/dev/null || { echo "pip install -r requirements.txt"; exit 1; }
echo "AI 모드: ${AI_MODE:-auto(키 없으면 mock)}"
streamlit run app.py --server.port 8610

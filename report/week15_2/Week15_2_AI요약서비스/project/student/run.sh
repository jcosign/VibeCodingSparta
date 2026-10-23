#!/usr/bin/env bash
# 로컬 실행 스크립트 (로컬 백업 경로). PORT 환경변수를 존중 → 로컬은 8615, Cloud Run은 플랫폼이 준 포트.
set -e; cd "$(dirname "$0")"
# 가상환경이 있으면 자동으로 켠다(env_set_up.sh 로 만든 .venv)
if [ -f .venv/bin/activate ]; then source .venv/bin/activate
elif [ -f .venv/Scripts/activate ]; then source .venv/Scripts/activate; fi
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
"$PY" -c "import streamlit" 2>/dev/null || { echo "pip install -r requirements.txt"; exit 1; }
# 로컬/배포 공통: PORT 환경변수를 존중(Cloud Run 호환). export 해서 앱 사이드바에도 실제 포트가 보이게 함.
export PORT="${PORT:-8615}"
streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0

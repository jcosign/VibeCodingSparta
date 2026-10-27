#!/usr/bin/env bash
# run.sh - 빠른 실행 스크립트 (env_set_up.sh를 먼저 한 번 실행해 두세요)
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "가상환경(.venv)이 없습니다. 먼저 'bash env_set_up.sh'를 실행하세요."
  exit 1
fi
if [ -f .venv/bin/activate ]; then source .venv/bin/activate; else source .venv/Scripts/activate; fi
streamlit run app.py "$@"

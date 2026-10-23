#!/usr/bin/env bash
# 빠른 실행: 가상환경이 있으면 자동으로 켜고 Streamlit 실행
cd "$(dirname "$0")"
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
elif [ -f .venv/Scripts/activate ]; then
  source .venv/Scripts/activate
else
  echo "가상환경(.venv)이 없습니다. 먼저 bash env_set_up.sh 를 실행하세요."
fi
exec streamlit run app.py "$@"

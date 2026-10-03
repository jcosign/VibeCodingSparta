#!/usr/bin/env bash
set -euo pipefail

export AI_MODE="${1:-${AI_MODE:-mock}}"
exec streamlit run app.py --server.port "${PORT:-8601}"


#!/usr/bin/env sh
set -eu
streamlit run app.py --server.port "${PORT:-8606}"

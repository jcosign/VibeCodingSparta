#!/usr/bin/env bash
# 최초 1회: 가상환경(.venv) + 패키지 설치 + 자동 검증(키 없이 mock 응답 출력)
# 전체 출력은 env_set_up.log 에도 저장됩니다(제출 시 참고).
set -euo pipefail
cd "$(dirname "$0")"
exec > >(tee env_set_up.log) 2>&1

echo "== [1/4] Python 확인 (3.10 이상 필요, Dockerfile은 3.11)"
PY=""
for c in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.10 이상이 필요합니다(권장 3.11~3.12). 설치 후 다시 실행하세요."; exit 1
fi
"$PY" --version

echo "== [2/4] 가상환경(.venv) 생성"
[ -d .venv ] || "$PY" -m venv .venv
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate          # Linux / macOS / 컨테이너
else
  source .venv/Scripts/activate      # Windows(Git Bash)
fi
python -m pip install --upgrade pip

echo "== [3/4] 패키지 설치 (requirements.txt)"
python -m pip install -r requirements.txt

echo "== [4/4] 자동 검증"
python examples/example_01_config_check.py
python examples/example_02_deploy_readiness.py
echo "-- mock 응답 확인 (키를 일부러 비우고 호출)"
GEMINI_API_KEY= GOOGLE_API_KEY= python - <<'EOF'
from gemini_client import ask, current_mode
assert current_mode() == "mock"
text, meta = ask(system="너는 요약가야. 3문장으로 요약해.",
                 user="이번 분기 매출은 4,648만 원입니다. 1위 카테고리는 의류입니다. 주문은 223건입니다.")
print("mock 응답:", text)
print("메타:", meta)
EOF

echo "완료! 실행: ./run.sh  → 브라우저에서 http://localhost:8615"

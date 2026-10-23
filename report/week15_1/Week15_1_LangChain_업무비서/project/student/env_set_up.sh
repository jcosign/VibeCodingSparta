#!/usr/bin/env bash
# 최초 1회: venv + torch(CPU/GPU 자동감지) + 나머지 패키지 + 로컬 LLM 검증
# 전체 출력은 env_set_up.log 에도 저장됩니다(제출물).
set -euo pipefail
cd "$(dirname "$0")"
exec > >(tee env_set_up.log) 2>&1

echo "== [1/4] Python 확인"
# 패키지 설치 파일이 갖춰진 버전을 먼저 고른다(3.12에서 검증됨. 너무 최신 버전은 일부 패키지 빌드 실패 가능)
PY=""
for c in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9 이상이 필요합니다(권장 3.12). 설치 후 다시 실행하세요."; exit 1
fi
"$PY" --version
if "$PY" -c "import sys; sys.exit(0 if sys.version_info >= (3, 14) else 1)"; then
  echo "⚠ 매우 최신 Python입니다. 패키지 설치가 실패하면 Python 3.12로 다시 시도하세요."
fi

echo "== [2/4] 가상환경(.venv) 생성"
[ -d .venv ] || "$PY" -m venv .venv
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate          # Linux / macOS / 컨테이너
else
  source .venv/Scripts/activate      # Windows(Git Bash)
fi
python -m pip install --upgrade pip

echo "== [3/4] torch 설치 (CPU/GPU 자동감지)"
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  echo "GPU 감지 → PyPI 기본 torch 설치"
  python -m pip install torch
elif [ "$(uname -s)" = "Darwin" ]; then
  echo "macOS → PyPI 기본 torch 설치"
  python -m pip install torch
else
  echo "GPU 없음 → CPU 전용 torch 설치"
  python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
fi
python -m pip install -r requirements.txt

echo "== [4/4] 로컬 LLM 검증 (첫 실행 시 모델 다운로드)"
if ! python - <<'EOF'
from llm import LOCAL_MODEL, local_generate
print("로컬 모델:", LOCAL_MODEL)
print("검증 성공: 로컬 LLM 응답 =", local_generate("한 문장으로 자기소개를 해줘.", max_new_tokens=64))
EOF
then
  echo "검증 실패: 네트워크(모델 다운로드)·디스크·메모리를 확인하세요."
  echo "※ 실패해도 앱은 API 키 또는 mock으로 폴백해 동작합니다."
  exit 1
fi

echo "완료! 실행: source .venv/bin/activate && streamlit run app.py   (또는 bash run.sh)"

"""Demonstrate the optional text-generation backend and its explicit fallback."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_backend import complete


result = complete("이번 주 에이전트 프로젝트의 핵심을 한 문장으로 요약해줘.")
print(f"모드: {result['mode']}")
if result["fallback"]:
    print(f"폴백 사유: {result['fallback']}")
print(result["text"])


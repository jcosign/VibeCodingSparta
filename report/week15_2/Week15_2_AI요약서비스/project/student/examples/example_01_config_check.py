"""배포 전 설정 점검: 모드·PORT·키 유무 (키 '값'은 절대 출력하지 않음)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from gemini_client import GEMINI_MODEL, _api_key, current_mode  # noqa: E402

print("모드:", current_mode())
print("모델:", GEMINI_MODEL if current_mode() == "gemini" else "mock-gemini")
print("PORT:", os.getenv("PORT", "(없음 → run.sh는 8615, Dockerfile은 8080)"))
print("GEMINI_API_KEY:", "있음" if _api_key() else "없음 → mock으로 동작")

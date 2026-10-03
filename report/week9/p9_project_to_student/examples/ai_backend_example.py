"""예제 3: AI_MODE에 설정된 백엔드에 질문합니다."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_backend import ask


if __name__ == "__main__":
    print(ask("이번 주 매출과 리뷰 감정을 간단히 요약해 주세요."))

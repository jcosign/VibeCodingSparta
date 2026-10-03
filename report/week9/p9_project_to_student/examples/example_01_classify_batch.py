"""예제 1: 여러 리뷰를 분류하고 감정별 개수를 출력합니다."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from classifier import classify


REVIEWS = (
    "배송이 빠르고 품질도 좋아요.",
    "제품이 고장 나서 실망스럽습니다.",
    "오늘 상품을 받아서 사용해 보고 있어요.",
)


def main() -> None:
    results = [(review, classify(review)) for review in REVIEWS]
    for review, sentiment in results:
        print(f"{sentiment}: {review}")

    for sentiment in ("긍정", "부정", "중립"):
        count = sum(label == sentiment for _, label in results)
        print(f"{sentiment}: {count}건")


if __name__ == "__main__":
    main()

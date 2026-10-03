"""고정된 seed로 매출과 리뷰 예시 데이터를 만듭니다."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd


SEED = 20261003
CATEGORIES = ("의류", "식품", "전자", "생활용품")
PRODUCTS = {
    "의류": ("티셔츠", "청바지", "운동화", "재킷"),
    "식품": ("커피", "과일", "간식", "쌀"),
    "전자": ("이어폰", "키보드", "마우스", "충전기"),
    "생활용품": ("텀블러", "수건", "세제", "수납함"),
}

_REVIEW_TEMPLATES = (
    ("배송이 빠르고 품질도 좋아요.", "긍정"),
    ("가격 대비 만족스럽고 추천합니다.", "긍정"),
    ("포장이 꼼꼼해서 선물하기 좋았어요.", "긍정"),
    ("기대보다 훨씬 예쁘고 편리합니다.", "긍정"),
    ("정말 잘 샀어요. 다음에 또 구매할게요.", "긍정"),
    ("사용하기 편하고 성능이 훌륭해요.", "긍정"),
    ("배송이 너무 늦고 포장도 엉망이에요.", "부정"),
    ("제품이 고장 나서 실망스럽습니다.", "부정"),
    ("가격은 비싼데 품질이 별로예요.", "부정"),
    ("설명과 다르고 다시는 구매하지 않을래요.", "부정"),
    ("불량품이 왔어요. 환불하고 싶습니다.", "부정"),
    ("생각보다 불편하고 추천하고 싶지 않아요.", "부정"),
    ("오늘 상품을 받아서 사용해 보고 있어요.", "중립"),
    ("색상은 화면에서 본 것과 비슷합니다.", "중립"),
    ("크기는 보통이고 구성품은 설명과 같습니다.", "중립"),
    ("아직 오래 써보지 않아 잘 모르겠어요.", "중립"),
    ("주문한 제품과 색상을 확인했습니다.", "중립"),
    ("포장은 무난했고 배송은 예정일에 도착했어요.", "중립"),
)


def sales_df() -> pd.DataFrame:
    """반복 실행해도 같은 180건의 합성 매출 데이터를 반환합니다."""
    rng = np.random.default_rng(SEED)
    first_day = date(2026, 1, 1)
    rows: list[dict[str, object]] = []

    for order_id in range(1, 181):
        category = str(rng.choice(CATEGORIES))
        product = str(rng.choice(PRODUCTS[category]))
        quantity = int(rng.integers(1, 6))
        unit_price = int(rng.integers(5, 151)) * 1_000
        order_date = first_day + timedelta(days=int(rng.integers(0, 90)))
        rows.append(
            {
                "주문번호": order_id,
                "날짜": pd.Timestamp(order_date),
                "카테고리": category,
                "상품": product,
                "수량": quantity,
                "단가": unit_price,
                "매출": quantity * unit_price,
            }
        )

    return pd.DataFrame(rows)


def reviews_df() -> pd.DataFrame:
    """고정된 seed로 만든 36건의 합성 리뷰 예시를 반환합니다."""
    rng = np.random.default_rng(SEED + 1)
    first_day = date(2026, 1, 1)
    rows: list[dict[str, object]] = []

    for review_id in range(1, 37):
        review, sentiment = _REVIEW_TEMPLATES[(review_id - 1) % len(_REVIEW_TEMPLATES)]
        category = str(rng.choice(CATEGORIES))
        review_date = first_day + timedelta(days=int(rng.integers(0, 90)))
        rows.append(
            {
                "리뷰번호": review_id,
                "날짜": pd.Timestamp(review_date),
                "카테고리": category,
                "리뷰": review,
                "예시감정": sentiment,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    sales = sales_df()
    reviews = reviews_df()
    print(f"매출 데이터: {len(sales)}건, 총매출 {sales['매출'].sum():,}원")
    print(f"리뷰 데이터: {len(reviews)}건")


if __name__ == "__main__":
    main()

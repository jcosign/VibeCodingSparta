"""data.py - 연습용 합성 데이터(주문·리뷰). 실제 업무 데이터로 바꿀 자리입니다.

- orders_df()  : 일자 x 카테고리 x 지역 주문 데이터 (2026-06-01부터 30일)
                 컬럼: 주문번호 · 날짜 · 카테고리 · 지역 · 금액_만원
- reviews_df() : 리뷰 120행. 컬럼: 카테고리 · 별점 · 리뷰(텍스트)
- daily_sales(): 일별 매출 합계 (대시보드 꺾은선 차트용)

직접 실행하면(python3 data.py) 자가 테스트로 요약 숫자를 출력합니다.
import 하면 조용히 함수만 제공합니다(if __name__ == "__main__").
"""
import numpy as np
import pandas as pd

CATEGORIES = ["의류", "가방", "신발", "뷰티"]
REGIONS = ["서울", "경기", "부산", "대구", "광주"]

# 합성 데이터의 '성격'만 정하는 값 - 카테고리별 평균 주문 금액(만원), 지역별 주문 비중
_CAT_PRICE = {"의류": 24, "가방": 20, "신발": 18, "뷰티": 12}
_REGION_W = [0.35, 0.25, 0.15, 0.13, 0.12]

_POS = ["배송 빨라 좋아요", "품질이 좋아요", "재구매 의사 있어요", "디자인이 예뻐요",
        "가격 대비 만족해요", "포장이 꼼꼼해서 좋아요", "사이즈 딱 맞고 좋아요"]
_NEG = ["불량이 와서 환불했어요", "배송이 너무 느려요", "사진과 달라서 별로예요",
        "마감이 별로예요", "냄새가 나서 실망했어요", "사이즈가 안 맞아 교환했어요"]
_NEU = ["보통이에요", "그냥 그래요", "무난합니다", "가격만큼 해요", "평범해요"]


def orders_df(days=30, seed=42):
    """일자 x 카테고리 x 지역 주문 데이터."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-06-01")
    rows, no = [], 1
    for d in range(days):
        date = (start + pd.Timedelta(days=d)).date()
        for _ in range(int(rng.integers(4, 11))):          # 하루 4~10건
            cat = CATEGORIES[int(rng.integers(0, len(CATEGORIES)))]
            region = REGIONS[int(rng.choice(len(REGIONS), p=_REGION_W))]
            amount = max(1, int(rng.normal(_CAT_PRICE[cat], 6)))
            rows.append({"주문번호": f"O{no:04d}", "날짜": date,
                         "카테고리": cat, "지역": region, "금액_만원": amount})
            no += 1
    return pd.DataFrame(rows)


def reviews_df(n=120, seed=7):
    """카테고리 · 별점 · 리뷰(텍스트) 데이터."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        cat = CATEGORIES[int(rng.integers(0, len(CATEGORIES)))]
        kind = rng.choice(["pos", "neg", "neu"], p=[0.5, 0.3, 0.2])
        if kind == "pos":
            text, star = _POS[int(rng.integers(0, len(_POS)))], int(rng.integers(4, 6))
        elif kind == "neg":
            text, star = _NEG[int(rng.integers(0, len(_NEG)))], int(rng.integers(1, 3))
        else:
            text, star = _NEU[int(rng.integers(0, len(_NEU)))], 3
        rows.append({"카테고리": cat, "별점": star, "리뷰": text})
    return pd.DataFrame(rows)


def daily_sales(orders=None):
    """일별 매출 합계(만원). index = 날짜."""
    o = orders if orders is not None else orders_df()
    return o.groupby("날짜")["금액_만원"].sum()


if __name__ == "__main__":
    o = orders_df()
    r = reviews_df()
    print("orders:", o.shape, "| reviews:", r.shape)
    print("총매출:", int(o["금액_만원"].sum()), "만원 | 총주문:", len(o), "건")
    print("평균 별점:", round(r["별점"].mean(), 2))
    print("카테고리별 매출(만원):")
    print(o.groupby("카테고리")["금액_만원"].sum().sort_values(ascending=False).to_string())

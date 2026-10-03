"""예제 2: 매출 데이터를 간단히 집계합니다."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data


def main() -> None:
    sales = data.sales_df()
    daily_sales = sales.groupby(sales["날짜"].dt.date)["매출"].sum()
    category_sales = sales.groupby("카테고리")["매출"].sum().sort_values(ascending=False)
    print(f"주문 수: {len(sales)}건")
    print(f"총매출: {sales['매출'].sum():,}원")
    print(f"일평균 매출: {daily_sales.mean():,.0f}원")
    print(f"카테고리별 매출:\n{category_sales.to_string()}")


if __name__ == "__main__":
    main()

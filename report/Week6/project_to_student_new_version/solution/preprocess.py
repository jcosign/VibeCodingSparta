"""판매 데이터를 정리하고 요약표와 SQLite 데이터베이스를 만듭니다."""

from pathlib import Path
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"


def preprocess():
    raw_path = DATA_DIR / "raw_sales.csv"
    if not raw_path.exists():
        raise FileNotFoundError("먼저 generate_data.py를 실행해 주세요.")

    sales = pd.read_csv(raw_path)
    sales = sales.drop_duplicates().copy()
    sales = sales[sales["unit_price"] > 0].copy()

    for column in ["rating", "age"]:
        sales[column] = sales[column].fillna(sales[column].median())

    first_quartile = sales["amount"].quantile(0.25)
    third_quartile = sales["amount"].quantile(0.75)
    iqr = third_quartile - first_quartile
    lower_limit = first_quartile - 1.5 * iqr
    upper_limit = third_quartile + 1.5 * iqr
    sales = sales[sales["amount"].between(lower_limit, upper_limit)].copy()

    summary_columns = {
        "order_id": "count",
        "amount": "sum",
        "net_amount": "sum",
        "rating": "mean",
        "discount_rate": "mean",
    }
    region_summary = sales.groupby("region").agg(summary_columns).rename(
        columns={
            "order_id": "count",
            "amount": "total_sales",
            "net_amount": "total_net_sales",
            "rating": "average_rating",
            "discount_rate": "average_discount_rate",
        }
    ).reset_index()
    category_summary = sales.groupby("category").agg(summary_columns).rename(
        columns={
            "order_id": "count",
            "amount": "total_sales",
            "net_amount": "total_net_sales",
            "rating": "average_rating",
            "discount_rate": "average_discount_rate",
        }
    ).reset_index()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sales.to_csv(REPORT_DIR / "clean_sales.csv", index=False, encoding="utf-8-sig")
    region_summary.to_csv(REPORT_DIR / "summary_region.csv", index=False, encoding="utf-8-sig")
    category_summary.to_csv(REPORT_DIR / "summary_category.csv", index=False, encoding="utf-8-sig")

    database_path = DATA_DIR / "sales.db"
    with sqlite3.connect(database_path) as connection:
        sales.to_sql("sales_clean", connection, if_exists="replace", index=False)
        region_summary.to_sql("summary_region", connection, if_exists="replace", index=False)
        category_summary.to_sql("summary_category", connection, if_exists="replace", index=False)

    print(f"전처리 완료: {len(sales):,}행")
    print(f"DB 저장 위치: {database_path}")
    print("지역별 요약:")
    print(region_summary.to_string(index=False))
    print("카테고리별 요약:")
    print(category_summary.to_string(index=False))
    return sales, region_summary, category_summary


if __name__ == "__main__":
    preprocess()

"""요약 CSV와 영문 라벨 PDF 보고서를 생성합니다."""

from pathlib import Path
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"


def create_report():
    database_path = DATA_DIR / "sales.db"
    if not database_path.exists():
        raise FileNotFoundError("먼저 preprocess.py를 실행해 주세요.")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        sales = pd.read_sql_query("SELECT * FROM sales_clean", connection)
        region = pd.read_sql_query("SELECT * FROM summary_region", connection)
        category = pd.read_sql_query("SELECT * FROM summary_category", connection)

    sales.to_csv(REPORT_DIR / "clean_sales.csv", index=False, encoding="utf-8-sig")
    region.to_csv(REPORT_DIR / "summary_region.csv", index=False, encoding="utf-8-sig")
    category.to_csv(REPORT_DIR / "summary_category.csv", index=False, encoding="utf-8-sig")

    figure, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    axes[0].bar([f"Region {i + 1}" for i in range(len(region))], region["total_sales"])
    axes[0].set_title("Sales by Region")
    axes[0].set_ylabel("Sales (KRW)")
    axes[0].tick_params(axis="x", rotation=25)

    category_labels = [f"Category {i + 1}" for i in range(len(category))]
    positions = range(len(category))
    bar_width = 0.38
    axes[1].bar(
        [position - bar_width / 2 for position in positions],
        category["total_sales"],
        width=bar_width,
        label="Gross",
    )
    axes[1].bar(
        [position + bar_width / 2 for position in positions],
        category["total_net_sales"],
        width=bar_width,
        label="Net",
    )
    axes[1].set_xticks(list(positions), category_labels)
    axes[1].set_title("Gross and Net Sales by Category")
    axes[1].set_ylabel("Sales (KRW)")
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].legend()

    axes[2].bar(category_labels, category["average_discount_rate"] * 100)
    axes[2].set_title("Average Discount Rate by Category")
    axes[2].set_ylabel("Discount (%)")
    axes[2].tick_params(axis="x", rotation=25)

    figure.suptitle("Sales Analysis Report", fontsize=15)
    figure.text(
        0.5,
        0.91,
        f"Orders: {len(sales):,} | Total sales: {sales['amount'].sum():,} KRW | "
        f"Net sales: {sales['net_amount'].sum():,.0f} KRW | "
        f"Average discount: {sales['discount_rate'].mean() * 100:.1f}%",
        ha="center",
        fontsize=9,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.84))
    pdf_path = REPORT_DIR / "report.pdf"
    figure.savefig(pdf_path)
    plt.close(figure)

    print(f"CSV 및 PDF 보고서 저장 완료: {REPORT_DIR}")
    return {"clean_sales": sales, "region": region, "category": category, "pdf": pdf_path}


if __name__ == "__main__":
    create_report()

"""판매 분석 프로젝트의 주요 단계를 자동으로 확인합니다."""

import json
import os
import sqlite3

import pandas as pd
from streamlit.testing.v1 import AppTest

import analyze
import api
import generate_data
import preprocess
import report


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    raw = generate_data.generate_data(10_000)
    raw_path = generate_data.DATA_DIR / "raw_sales.csv"
    check(len(raw) >= 1_000, "원본 데이터가 1,000행보다 적습니다.")
    check(raw.isna().any().any(), "원본 데이터에 결측치가 없습니다.")
    check(raw_path.exists(), "원본 CSV가 생성되지 않았습니다.")
    check(raw["discount_rate"].between(0, 0.30).all(), "할인율 범위가 올바르지 않습니다.")
    raw_net = raw["amount"] * (1 - raw["discount_rate"])
    check((raw["net_amount"] - raw_net).abs().max() < 0.01, "원본 할인 후 금액 계산이 맞지 않습니다.")

    clean, region, category = preprocess.preprocess()
    check(not clean.isna().any().any(), "전처리 후 결측치가 남아 있습니다.")
    check((clean["unit_price"] > 0).all(), "단가가 0 이하인 행이 남아 있습니다.")
    check(not clean.duplicated().any(), "중복 행이 남아 있습니다.")
    check((clean["amount"] > 0).all(), "금액 이상치 또는 0 이하 금액이 남아 있습니다.")
    clean_net = clean["amount"] * (1 - clean["discount_rate"])
    check((clean["net_amount"] - clean_net).abs().max() < 0.01, "전처리 후 할인 금액 계산이 맞지 않습니다.")
    summary_columns = {"total_net_sales", "average_discount_rate"}
    check(summary_columns.issubset(region.columns), "지역별 요약에 할인율 정보가 없습니다.")
    check(summary_columns.issubset(category.columns), "카테고리별 요약에 할인율 정보가 없습니다.")
    with sqlite3.connect(generate_data.DATA_DIR / "sales.db") as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    check({"sales_clean", "summary_region", "summary_category"}.issubset(tables), "DB 테이블이 누락됐습니다.")

    os.environ["AI_MODE"] = "mock"
    analysis_result = analyze.analyze()
    check(analysis_result["mode"] == "mock", "mock 분석이 실행되지 않았습니다.")
    analysis_path = generate_data.DATA_DIR / "analysis.json"
    check(json.loads(analysis_path.read_text(encoding="utf-8")), "분석 JSON이 비어 있습니다.")

    report_result = report.create_report()
    check((generate_data.BASE_DIR / "reports" / "clean_sales.csv").exists(), "정리 CSV가 없습니다.")
    check(report_result["pdf"].exists() and report_result["pdf"].stat().st_size > 0, "PDF가 생성되지 않았습니다.")
    check(pd.read_csv(generate_data.BASE_DIR / "reports" / "summary_region.csv").shape[0] > 0, "지역 요약 CSV가 비어 있습니다.")

    summary_response = api.summary_endpoint()
    data_response = api.data_endpoint(limit=5)
    top_response = api.top_endpoint(category="전자제품", limit=5)
    analysis_response = api.analysis_endpoint()
    report_response = api.report_csv_endpoint()
    check(len(summary_response["region"]) > 0, "API 요약 응답이 비어 있습니다.")
    check("average_discount_rate" in summary_response["region"][0], "API 요약에 할인율이 없습니다.")
    check(len(data_response) == 5, "API 데이터 응답 건수가 맞지 않습니다.")
    check("discount_rate" in data_response[0], "API 데이터에 할인율이 없습니다.")
    check(len(top_response) == 5, "카테고리 상위 응답 건수가 맞지 않습니다.")
    check(all(row["category"] == "전자제품" for row in top_response), "상위 응답에 다른 카테고리가 포함됐습니다.")
    top_net_sales = [row["net_amount"] for row in top_response]
    check(top_net_sales == sorted(top_net_sales, reverse=True), "상위 응답이 할인 후 매출순이 아닙니다.")
    check(analysis_response["mode"] == "mock", "API 분석 응답이 맞지 않습니다.")
    check(report_response.path.name == "clean_sales.csv", "API CSV 응답 파일이 맞지 않습니다.")
    report_csv = pd.read_csv(report_response.path)
    check({"discount_rate", "net_amount"}.issubset(report_csv.columns), "보고서 CSV에 할인 정보가 없습니다.")

    app_test = AppTest.from_file(str(generate_data.BASE_DIR / "app.py")).run()
    check(len(app_test.multiselect) == 1, "카테고리 필터 위젯이 없습니다.")
    app_test.multiselect[0].set_value(["전자제품"]).run()
    visible_sales = app_test.dataframe[0].value
    check(set(visible_sales["category"]) == {"전자제품"}, "카테고리 필터가 표에 적용되지 않습니다.")
    print("ALL PASS")


if __name__ == "__main__":
    main()

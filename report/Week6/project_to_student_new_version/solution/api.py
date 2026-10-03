"""전처리된 판매 데이터와 분석 결과를 제공하는 FastAPI 앱입니다."""

from pathlib import Path
import json
import sqlite3

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
app = FastAPI(title="Sales Analysis API", description="판매 분석 결과를 조회합니다.")


def get_summary():
    database_path = DATA_DIR / "sales.db"
    if not database_path.exists():
        raise HTTPException(status_code=404, detail="먼저 데이터를 전처리해 주세요.")
    with sqlite3.connect(database_path) as connection:
        region = pd.read_sql_query("SELECT * FROM summary_region", connection)
        category = pd.read_sql_query("SELECT * FROM summary_category", connection)
    return {"region": region.to_dict(orient="records"), "category": category.to_dict(orient="records")}


def get_data(limit=100):
    database_path = DATA_DIR / "sales.db"
    if not database_path.exists():
        raise HTTPException(status_code=404, detail="먼저 데이터를 전처리해 주세요.")
    with sqlite3.connect(database_path) as connection:
        data = pd.read_sql_query("SELECT * FROM sales_clean LIMIT ?", connection, params=(limit,))
    return data.to_dict(orient="records")


def get_top(category, limit=10):
    database_path = DATA_DIR / "sales.db"
    if not database_path.exists():
        raise HTTPException(status_code=404, detail="먼저 데이터를 전처리해 주세요.")
    with sqlite3.connect(database_path) as connection:
        data = pd.read_sql_query(
            "SELECT * FROM sales_clean WHERE category = ? "
            "ORDER BY net_amount DESC, amount DESC LIMIT ?",
            connection,
            params=(category, limit),
        )
    return data.to_dict(orient="records")


def get_analysis():
    analysis_path = DATA_DIR / "analysis.json"
    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="먼저 analyze.py를 실행해 주세요.")
    return json.loads(analysis_path.read_text(encoding="utf-8"))


@app.get("/summary")
def summary_endpoint():
    return get_summary()


@app.get("/data")
def data_endpoint(limit: int = Query(default=100, ge=1, le=1000)):
    return get_data(limit)


@app.get("/top")
def top_endpoint(
    category: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    category = category.strip()
    if not category:
        raise HTTPException(status_code=422, detail="category를 입력해 주세요.")
    return get_top(category, limit)


@app.get("/analysis")
def analysis_endpoint():
    return get_analysis()


@app.get("/report.csv")
def report_csv_endpoint():
    report_path = REPORT_DIR / "clean_sales.csv"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="먼저 report.py를 실행해 주세요.")
    return FileResponse(report_path, media_type="text/csv", filename="clean_sales.csv")

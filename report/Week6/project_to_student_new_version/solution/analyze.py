"""DB 요약을 바탕으로 mock 또는 로컬 AI CLI 분석을 실행합니다."""

from pathlib import Path
import json
import os
import sqlite3
import subprocess

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_statistics():
    database_path = DATA_DIR / "sales.db"
    if not database_path.exists():
        raise FileNotFoundError("먼저 preprocess.py를 실행해 주세요.")

    with sqlite3.connect(database_path) as connection:
        region = pd.read_sql_query("SELECT * FROM summary_region", connection)
        category = pd.read_sql_query("SELECT * FROM summary_category", connection)

    return "지역별 요약:\n" + region.to_string(index=False) + "\n\n카테고리별 요약:\n" + category.to_string(index=False), region, category


def make_mock_analysis(region, category):
    best_region = region.loc[region["total_sales"].idxmax()]
    best_category = category.loc[category["total_sales"].idxmax()]
    return {
        "mode": "mock",
        "insights": [
            f"매출이 가장 높은 지역은 {best_region['region']}입니다.",
            f"매출이 가장 높은 카테고리는 {best_category['category']}입니다.",
        ],
        "recommendations": [
            f"{best_region['region']} 지역의 판매 전략을 분석해 다른 지역에 적용해 보세요.",
            f"{best_category['category']} 카테고리의 재고와 프로모션을 점검하세요.",
        ],
        "text": (
            f"최고 매출 지역: {best_region['region']} "
            f"({best_region['total_sales']:,.0f}원), 최고 매출 카테고리: "
            f"{best_category['category']} ({best_category['total_sales']:,.0f}원)."
        ),
    }


def run_cli_analysis(mode, statistics):
    prompt = (
        "다음 판매 통계를 한국어로 분석하세요. 핵심 인사이트와 실행 제안을 포함하세요.\n\n"
        + statistics
    )
    command = ["claude", "-p", prompt] if mode == "claude" else ["codex", "exec", prompt]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=45,
        check=True,
        encoding="utf-8",
    )
    text = result.stdout.strip()
    if not text:
        raise RuntimeError("AI CLI가 빈 응답을 반환했습니다.")
    return {"mode": mode, "insights": [], "recommendations": [], "text": text}


def analyze():
    statistics, region, category = load_statistics()
    requested_mode = os.getenv("AI_MODE", "mock").lower()
    if requested_mode not in {"mock", "claude", "codex"}:
        requested_mode = "mock"

    if requested_mode == "mock":
        result = make_mock_analysis(region, category)
    else:
        try:
            result = run_cli_analysis(requested_mode, statistics)
        except (OSError, subprocess.SubprocessError, RuntimeError) as error:
            print(f"{requested_mode} 분석 실패, mock으로 전환합니다: {error}")
            result = make_mock_analysis(region, category)
            result["fallback_reason"] = str(error)

    output_path = DATA_DIR / "analysis.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    analyze()

"""데이터 생성부터 보고서 다운로드까지 제공하는 Streamlit 대시보드입니다."""

import sqlite3

import pandas as pd
import streamlit as st

import analyze
import generate_data
import preprocess
import report


st.set_page_config(page_title="판매 분석 리포트", page_icon="📊", layout="wide")
st.title("판매 분석 리포트")
st.caption("데이터 생성 → 전처리 → AI 분석 → 보고서")

with st.sidebar:
    st.header("실행 단계")
    row_count = st.number_input("생성 데이터 수", min_value=1_000, max_value=100_000, value=10_000, step=1_000)
    if st.button("1. 데이터 생성", use_container_width=True):
        with st.spinner("판매 데이터를 만드는 중입니다..."):
            generate_data.generate_data(int(row_count))
        st.success("데이터 생성을 완료했습니다.")
    if st.button("2. 전처리", use_container_width=True):
        with st.spinner("데이터를 정리하고 DB에 저장하는 중입니다..."):
            preprocess.preprocess()
        st.success("전처리를 완료했습니다.")
    if st.button("3. AI 분석", use_container_width=True):
        with st.spinner("요약 통계를 분석하는 중입니다..."):
            analyze.analyze()
        st.success("분석을 완료했습니다.")
    if st.button("4. 보고서 만들기", use_container_width=True):
        with st.spinner("CSV와 PDF를 만드는 중입니다..."):
            report.create_report()
        st.success("보고서를 만들었습니다.")


database_path = generate_data.DATA_DIR / "sales.db"
if not database_path.exists():
    st.info("사이드바에서 1. 데이터 생성과 2. 전처리를 먼저 실행해 주세요.")
    st.stop()

with sqlite3.connect(database_path) as connection:
    sales = pd.read_sql_query("SELECT * FROM sales_clean", connection)

categories = sorted(sales["category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "카테고리 필터",
    options=categories,
    default=categories,
)
sales = sales[sales["category"].isin(selected_categories)].copy()
if sales.empty:
    st.info("카테고리를 하나 이상 선택해 주세요.")
    st.stop()

region = sales.groupby("region", as_index=False).agg(
    total_sales=("amount", "sum"),
    total_net_sales=("net_amount", "sum"),
)
category = sales.groupby("category", as_index=False).agg(
    total_sales=("amount", "sum"),
    total_net_sales=("net_amount", "sum"),
    average_discount_rate=("discount_rate", "mean"),
)

metric_columns = st.columns(5)
metric_columns[0].metric("정리된 주문", f"{len(sales):,}건")
metric_columns[1].metric("총매출", f"{sales['amount'].sum() / 100_000_000:.1f}억")
metric_columns[2].metric("할인 후 매출", f"{sales['net_amount'].sum() / 100_000_000:.1f}억")
metric_columns[3].metric("평균 할인율", f"{sales['discount_rate'].mean() * 100:.1f}%")
metric_columns[4].metric("평균 평점", f"{sales['rating'].mean():.2f} / 5")

left, right = st.columns(2)
with left:
    st.subheader("지역별 매출")
    st.bar_chart(region.set_index("region")["total_sales"])
with right:
    st.subheader("카테고리별 총매출·할인 후 매출")
    st.bar_chart(category.set_index("category")[["total_sales", "total_net_sales"]])

st.subheader("카테고리별 평균 할인율")
st.bar_chart(category.set_index("category")["average_discount_rate"] * 100)

st.subheader("정리된 판매 데이터")
st.dataframe(sales.head(100), use_container_width=True, hide_index=True)

analysis_path = generate_data.DATA_DIR / "analysis.json"
if analysis_path.exists():
    st.subheader("전체 데이터 분석 결과")
    import json

    analysis_result = json.loads(analysis_path.read_text(encoding="utf-8"))
    st.write(analysis_result.get("text", ""))
    for insight in analysis_result.get("insights", []):
        st.write(f"- {insight}")
    for recommendation in analysis_result.get("recommendations", []):
        st.write(f"제안: {recommendation}")

st.subheader("다운로드")
clean_csv = generate_data.BASE_DIR / "reports" / "clean_sales.csv"
pdf_file = generate_data.BASE_DIR / "reports" / "report.pdf"
download_columns = st.columns(2)
if clean_csv.exists():
    download_columns[0].download_button(
        "선택 데이터 CSV 다운로드",
        sales.to_csv(index=False).encode("utf-8-sig"),
        file_name="clean_sales_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )
if pdf_file.exists():
    download_columns[1].download_button(
        "전체 데이터 PDF 다운로드",
        pdf_file.read_bytes(),
        file_name="report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

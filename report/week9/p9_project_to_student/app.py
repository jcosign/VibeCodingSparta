"""합성 매출 대시보드와 리뷰 분류기를 제공하는 Streamlit 앱."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

import data
from classifier import LABELS, classify


def _render_sales_tab() -> None:
    sales = data.sales_df()
    min_date = sales["날짜"].min().date()
    max_date = sales["날짜"].max().date()

    with st.sidebar:
        st.header("매출 조회 조건")
        categories = st.multiselect(
            "카테고리",
            options=list(data.CATEGORIES),
            default=list(data.CATEGORIES),
        )
        selected_dates = st.date_input(
            "조회 기간",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered = sales[
            sales["날짜"].dt.date.between(start_date, end_date)
            & sales["카테고리"].isin(categories)
        ]
    else:
        st.info("조회 시작일과 종료일을 모두 선택해 주세요.")
        return

    total_sales = int(filtered["매출"].sum())
    day_count = filtered["날짜"].dt.date.nunique()
    average_sales = round(total_sales / day_count) if day_count else 0
    category_sales = filtered.groupby("카테고리")["매출"].sum().sort_values(ascending=False)
    top_category = str(category_sales.index[0]) if not category_sales.empty else "-"

    metric_total, metric_average, metric_top = st.columns(3)
    metric_total.metric("총매출", f"{total_sales:,}원")
    metric_average.metric("일평균 매출", f"{average_sales:,}원")
    metric_top.metric("1위 카테고리", top_category)

    if filtered.empty:
        st.info("선택한 조건에 해당하는 매출 데이터가 없습니다.")
        return

    daily_sales = (
        filtered.groupby(filtered["날짜"].dt.date)["매출"]
        .sum()
        .rename("매출")
        .to_frame()
    )
    st.subheader("일별 매출 추이")
    st.line_chart(daily_sales)

    st.subheader("카테고리별 매출")
    st.bar_chart(category_sales.rename("매출").to_frame())
    with st.expander("매출 데이터 보기"):
        st.dataframe(filtered, use_container_width=True, hide_index=True)


def _render_reviews_tab() -> None:
    st.caption("리뷰를 한 줄에 하나씩 입력하세요. 기본 분류 방식은 키워드 규칙입니다.")
    with st.form("review_classification_form"):
        review_text = st.text_area(
            "분류할 리뷰",
            placeholder="배송이 빠르고 품질도 좋아요.\n제품이 고장 나서 실망스럽습니다.",
            height=160,
        )
        submitted = st.form_submit_button("분류하기", type="primary")

    if submitted:
        reviews = [line.strip() for line in review_text.splitlines() if line.strip()]
        st.session_state["classified_reviews"] = [
            {"리뷰": review, "감정": classify(review)}
            for review in reviews
        ]

    results = st.session_state.get("classified_reviews", [])
    if not results:
        if submitted:
            st.info("분류할 리뷰를 한 줄 이상 입력해 주세요.")
        return

    results_df = pd.DataFrame(results)
    counts = results_df["감정"].value_counts().reindex(LABELS, fill_value=0)
    positive_count = int(counts["긍정"])
    negative_count = int(counts["부정"])
    metric_positive, metric_negative = st.columns(2)
    metric_positive.metric("긍정 리뷰", f"{positive_count}건")
    metric_negative.metric("부정 리뷰", f"{negative_count}건")

    st.subheader("감정 분포")
    st.bar_chart(counts.rename("리뷰 수").to_frame())
    st.subheader("분류 결과")
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    csv_data = results_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "결과 CSV 다운로드",
        data=csv_data,
        file_name=f"리뷰_분류결과_{date.today().isoformat()}.csv",
        mime="text/csv",
    )


def main() -> None:
    st.set_page_config(page_title="매출 대시보드 & 리뷰 분류", page_icon="📊", layout="wide")
    st.title("매출 대시보드 & 리뷰 분류기")
    st.caption("고정 seed의 합성 데이터를 사용합니다. 새로고침해도 데이터가 바뀌지 않습니다.")

    sales_tab, reviews_tab = st.tabs(["📈 매출 대시보드", "💬 리뷰 분류"])
    with sales_tab:
        _render_sales_tab()
    with reviews_tab:
        _render_reviews_tab()


if __name__ == "__main__":
    main()

"""Streamlit dashboard for the Week 08 order service."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

import store


API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 3


def _api_data(
    params: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    orders_response = requests.get(
        f"{API_URL}/orders",
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    orders_response.raise_for_status()
    stats_response = requests.get(
        f"{API_URL}/stats",
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    stats_response.raise_for_status()
    region_stats_response = requests.get(
        f"{API_URL}/stats/region",
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    region_stats_response.raise_for_status()
    return (
        orders_response.json(),
        stats_response.json(),
        region_stats_response.json(),
    )


def _store_data(
    params: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    filters = {
        "category": params.get("category"),
        "region": params.get("region"),
        "status": params.get("status"),
    }
    return (
        store.list_orders(**filters),
        store.stats(**filters),
        store.stats_by_region(
            category=filters["category"],
            region=filters["region"],
            status=filters["status"],
        ),
    )


def main() -> None:
    st.set_page_config(page_title="주문 조회 대시보드", page_icon="📦", layout="wide")
    st.title("주문 조회 대시보드")
    st.caption("주문 데이터를 조건별로 조회하고 매출을 확인합니다.")

    with st.sidebar:
        st.header("조회 조건")
        category = st.selectbox("카테고리", ["전체", *store.CATEGORIES])
        region = st.selectbox("지역", ["전체", *store.REGIONS])
        order_status = st.selectbox("상태", ["전체", *store.STATUSES])

    params = {
        key: value
        for key, value in (
            ("category", category),
            ("region", region),
            ("status", order_status),
        )
        if value != "전체"
    }
    params.update(limit="500", sort_by="id", sort_order="asc")

    try:
        orders, summary, region_summary = _api_data(params)
        st.success("데이터 연결: API")
    except (requests.ConnectionError, requests.Timeout):
        orders, summary, region_summary = _store_data(params)
        st.info("백엔드에 연결할 수 없어 직접(store) 조회 중입니다.")
    except requests.HTTPError as error:
        st.error(f"API 요청이 실패했습니다: {error}")
        st.stop()

    metric_orders, metric_sales = st.columns(2)
    metric_orders.metric("주문 수", f"{summary['total_orders']:,}건")
    metric_sales.metric("총매출", f"{summary['total_sales']:,}원")

    left, right = st.columns((3, 2))
    with left:
        st.subheader("주문 목록")
        if orders:
            st.dataframe(orders, use_container_width=True, hide_index=True)
        else:
            st.info("조건에 맞는 주문이 없습니다.")

    with right:
        st.subheader("카테고리별 매출")
        category_sales = summary["category_sales"]
        if category_sales:
            st.bar_chart(category_sales)
        else:
            st.info("표시할 매출 데이터가 없습니다.")

        st.subheader("지역별 매출")
        region_sales = region_summary["region_sales"]
        if region_sales:
            st.bar_chart(region_sales)
        else:
            st.info("표시할 지역별 매출 데이터가 없습니다.")


if __name__ == "__main__":
    main()

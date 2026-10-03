"""Exercise the order API without starting a web server."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
from tinydb import Query, TinyDB

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from api import app
from store import DB_PATH


def main() -> None:
    client = TestClient(app)

    default_page_response = client.get("/orders")
    assert default_page_response.status_code == 200, default_page_response.text
    default_page = default_page_response.json()
    assert len(default_page) == 20
    assert [order["id"] for order in default_page] == list(range(1, 21))
    print("GET /orders (default limit=20, offset=0, sort_by=id, sort_order=asc): OK")

    page_response = client.get(
        "/orders",
        params={"limit": 5, "offset": 2},
    )
    assert page_response.status_code == 200, page_response.text
    page = page_response.json()
    assert [order["id"] for order in page] == [3, 4, 5, 6, 7]
    print("GET /orders?limit=5&offset=2: OK (IDs 3–7)")

    descending_response = client.get(
        "/orders",
        params={"limit": 5, "sort_by": "total", "sort_order": "desc"},
    )
    assert descending_response.status_code == 200, descending_response.text
    descending_orders = descending_response.json()
    assert [order["total"] for order in descending_orders] == sorted(
        (order["total"] for order in descending_orders),
        reverse=True,
    )
    print("GET /orders?sort_by=total&sort_order=desc: OK")

    invalid_page_response = client.get("/orders", params={"limit": 0})
    assert invalid_page_response.status_code == 422, invalid_page_response.text
    print("GET /orders?limit=0: OK (422 validation)")

    orders_response = client.get("/orders", params={"limit": 500})
    assert orders_response.status_code == 200, orders_response.text
    orders = orders_response.json()
    assert len(orders) == 60, f"Expected 60 seeded orders, got {len(orders)}"
    print(f"GET /orders: OK ({len(orders)} orders)")

    region_response = client.get("/orders", params={"region": "서울"})
    assert region_response.status_code == 200, region_response.text
    seoul_orders = region_response.json()
    assert seoul_orders, "Expected at least one Seoul order"
    assert all(order["region"] == "서울" for order in seoul_orders)
    print(f"GET /orders?region=서울: OK ({len(seoul_orders)} orders)")

    detail_response = client.get("/orders/1")
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["id"] == 1
    print("GET /orders/1: OK")

    missing_response = client.get("/orders/99999")
    assert missing_response.status_code == 404, missing_response.text
    print("GET /orders/99999: OK (404)")

    stats_response = client.get("/stats")
    assert stats_response.status_code == 200, stats_response.text
    summary = stats_response.json()
    assert summary["total_orders"] == len(orders)
    assert summary["total_sales"] == sum(order["total"] for order in orders)
    print(
        "GET /stats: OK "
        f"({summary['total_orders']} orders, {summary['total_sales']} total sales)"
    )

    region_stats_response = client.get("/stats/region")
    assert region_stats_response.status_code == 200, region_stats_response.text
    region_summary = region_stats_response.json()
    assert region_summary["total_orders"] == len(orders)
    assert region_summary["total_sales"] == sum(
        order["total"] for order in orders
    )
    assert sum(region_summary["region_counts"].values()) == len(orders)
    assert sum(region_summary["region_sales"].values()) == region_summary["total_sales"]
    print(
        "GET /stats/region: OK "
        f"({region_summary['region_sales']})"
    )

    month_stats_response = client.get("/stats/month")
    assert month_stats_response.status_code == 200, month_stats_response.text
    month_summary = month_stats_response.json()
    assert month_summary["total_orders"] == len(orders)
    assert month_summary["total_sales"] == sum(
        order["total"] for order in orders
    )
    assert sum(month_summary["month_counts"].values()) == len(orders)
    assert sum(month_summary["month_sales"].values()) == month_summary["total_sales"]
    assert list(month_summary["month_sales"]) == sorted(month_summary["month_sales"])
    print(f"GET /stats/month: OK ({month_summary['month_sales']})")

    filtered_month_response = client.get(
        "/stats/month",
        params={"category": "의류", "region": "서울"},
    )
    assert filtered_month_response.status_code == 200, filtered_month_response.text
    filtered_month_summary = filtered_month_response.json()
    filtered_orders = [
        order
        for order in orders
        if order["category"] == "의류" and order["region"] == "서울"
    ]
    assert filtered_month_summary["total_orders"] == len(filtered_orders)
    assert filtered_month_summary["total_sales"] == sum(
        order["total"] for order in filtered_orders
    )
    print("GET /stats/month?category=의류&region=서울: OK")

    filtered_region_response = client.get(
        "/stats/region",
        params={"region": "서울"},
    )
    assert filtered_region_response.status_code == 200, filtered_region_response.text
    assert filtered_region_response.json()["region_counts"] == {"서울": 17}
    print("GET /stats/region?region=서울: OK")

    created_order_id: int | None = None
    try:
        create_response = client.post(
            "/orders",
            json={
                "customer": "Test Customer",
                "product": "Test Product",
                "category": "전자",
                "region": "서울",
                "quantity": 2,
                "unit_price": 1000,
            },
        )
        assert create_response.status_code == 201, create_response.text
        created_order = create_response.json()
        created_order_id = created_order["id"]
        assert created_order["total"] == 2000
        print(f"POST /orders: OK (created order {created_order_id})")
    finally:
        if created_order_id is not None:
            with TinyDB(DB_PATH) as db:
                db.remove(Query().id == created_order_id)

    print("END-TO-END OK")


if __name__ == "__main__":
    main()

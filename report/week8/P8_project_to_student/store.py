"""TinyDB-backed order storage for the Week 08 project."""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal

from tinydb import TinyDB


SortField = Literal["id", "order_date", "total", "category", "region"]
SortOrder = Literal["asc", "desc"]

DB_PATH = Path(__file__).with_name("orders.json")
SEED = 202608
CATEGORIES = ("의류", "식품", "전자", "생활용품")
REGIONS = ("서울", "부산", "인천", "대구", "광주")
STATUSES = ("완료", "취소")
PRODUCTS = {
    "의류": ("티셔츠", "청바지", "운동화", "재킷"),
    "식품": ("커피", "과일", "간식", "쌀"),
    "전자": ("이어폰", "키보드", "마우스", "충전기"),
    "생활용품": ("텀블러", "수건", "세제", "수납함"),
}


def _seed_orders() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    first_day = date(2026, 1, 1)
    orders: list[dict[str, Any]] = []

    for order_id in range(1, 61):
        category = rng.choice(CATEGORIES)
        quantity = rng.randint(1, 5)
        unit_price = rng.randrange(5_000, 150_001, 1_000)
        orders.append(
            {
                "id": order_id,
                "customer": f"고객{rng.randint(1, 25):02d}",
                "product": rng.choice(PRODUCTS[category]),
                "category": category,
                "region": rng.choice(REGIONS),
                "quantity": quantity,
                "unit_price": unit_price,
                "total": quantity * unit_price,
                "status": rng.choices(STATUSES, weights=(9, 1))[0],
                "order_date": (first_day + timedelta(days=rng.randrange(180))).isoformat(),
            }
        )

    return orders


def ensure_seeded() -> None:
    """Add deterministic sample orders only when the database is empty."""
    with TinyDB(DB_PATH) as db:
        if not db:
            db.insert_multiple(_seed_orders())


def list_orders(
    category: str | None = None,
    region: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    sort_by: SortField = "id",
    sort_order: SortOrder = "asc",
) -> list[dict[str, Any]]:
    """Return filtered orders sorted and sliced to the requested page."""
    # 고른 조건에 맞는 주문만 남기고, 필요한 구간만 잘라서 돌려줍니다.
    ensure_seeded()
    with TinyDB(DB_PATH) as db:
        orders = db.all()

    if category:
        orders = [order for order in orders if order.get("category") == category]
    if region:
        orders = [order for order in orders if order.get("region") == region]
    if status:
        orders = [order for order in orders if order.get("status") == status]
    orders.sort(key=lambda order: order.get(sort_by), reverse=sort_order == "desc")

    start = max(offset, 0)
    return orders[start:] if limit is None else orders[start : start + limit]


def get_order(order_id: int) -> dict[str, Any] | None:
    """Return one order by its public numeric ID, or None if absent."""
    ensure_seeded()
    with TinyDB(DB_PATH) as db:
        matches = db.search(lambda order: order.get("id") == order_id)
    return matches[0] if matches else None


def add_order(order: dict[str, Any]) -> dict[str, Any]:
    """Insert an order and return the stored document."""
    ensure_seeded()
    with TinyDB(DB_PATH) as db:
        next_id = max((item.get("id", 0) for item in db.all()), default=0) + 1
        stored = dict(order)
        stored["id"] = next_id
        stored["total"] = stored["quantity"] * stored["unit_price"]
        db.insert(stored)
    return stored


def stats(
    category: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Aggregate order count and sales overall and by category."""
    # 조건에 맞는 주문을 모아 전체 개수와 매출, 종류별 매출을 계산합니다.
    orders = list_orders(category=category, region=region, status=status)
    category_sales: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for order in orders:
        name = order["category"]
        category_sales[name] = category_sales.get(name, 0) + order["total"]
        category_counts[name] = category_counts.get(name, 0) + 1

    return {
        "total_orders": len(orders),
        "total_sales": sum(order["total"] for order in orders),
        "category_sales": category_sales,
        "category_counts": category_counts,
    }


def stats_by_region(
    category: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Aggregate order counts and sales overall and by region."""
    orders = list_orders(category=category, region=region, status=status)
    region_sales: dict[str, int] = {}
    region_counts: dict[str, int] = {}
    for order in orders:
        name = order["region"]
        region_sales[name] = region_sales.get(name, 0) + order["total"]
        region_counts[name] = region_counts.get(name, 0) + 1

    return {
        "total_orders": len(orders),
        "total_sales": sum(order["total"] for order in orders),
        "region_sales": region_sales,
        "region_counts": region_counts,
    }


def stats_by_month(
    category: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Aggregate order counts and sales overall and by calendar month."""
    orders = list_orders(category=category, region=region, status=status)
    month_sales: dict[str, int] = {}
    month_counts: dict[str, int] = {}
    for order in orders:
        month = order["order_date"][:7]
        month_sales[month] = month_sales.get(month, 0) + order["total"]
        month_counts[month] = month_counts.get(month, 0) + 1

    return {
        "total_orders": len(orders),
        "total_sales": sum(order["total"] for order in orders),
        "month_sales": dict(sorted(month_sales.items())),
        "month_counts": dict(sorted(month_counts.items())),
    }


def main() -> None:
    ensure_seeded()
    print(f"seed {len(list_orders())}건")
    print(f"의류 주문 수: {len(list_orders(category='의류'))}")
    print(f"order 1: {get_order(1)}")
    print(f"stats: {stats()}")


if __name__ == "__main__":
    main()

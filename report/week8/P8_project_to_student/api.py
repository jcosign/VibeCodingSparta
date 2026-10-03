"""FastAPI endpoints for the Week 08 order service."""

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from store import SortField, SortOrder, add_order, get_order, list_orders
from store import stats as get_stats
from store import stats_by_month, stats_by_region


Category = Literal["의류", "식품", "전자", "생활용품"]
Region = Literal["서울", "부산", "인천", "대구", "광주"]
OrderStatus = Literal["완료", "취소"]

app = FastAPI(
    title="주문 조회 API",
    description="교육용 주문 데이터 조회·추가·집계 API",
    version="1.0.0",
)


class OrderCreate(BaseModel):
    customer: str = Field(min_length=1, max_length=80)
    product: str = Field(min_length=1, max_length=100)
    category: Category
    region: Region
    quantity: int = Field(gt=0, le=10_000)
    unit_price: int = Field(gt=0, le=100_000_000)
    status: OrderStatus = "완료"
    order_date: date = Field(default_factory=date.today)


@app.get("/orders")
def read_orders(
    category: Category | None = None,
    region: Region | None = None,
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_by: SortField = "id",
    sort_order: SortOrder = "asc",
) -> list[dict]:
    """List orders, optionally filtered by category, region, or status."""
    return list_orders(
        category=category,
        region=region,
        status=status_filter,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@app.get("/orders/{order_id}")
def read_order(order_id: int) -> dict:
    """Return an order by ID, or 404 when it does not exist."""
    order = get_order(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return order


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate) -> dict:
    """Validate and store a new order."""
    return add_order(order.model_dump(mode="json"))


@app.get("/stats")
def read_stats(
    category: Category | None = None,
    region: Region | None = None,
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
) -> dict:
    """Return order count and sales totals, optionally filtered."""
    return get_stats(category=category, region=region, status=status_filter)


@app.get("/stats/region")
def read_region_stats(
    category: Category | None = None,
    region: Region | None = None,
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
) -> dict:
    """Return order count and sales totals grouped by region."""
    return stats_by_region(
        category=category,
        region=region,
        status=status_filter,
    )


@app.get("/stats/month")
def read_month_stats(
    category: Category | None = None,
    region: Region | None = None,
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
) -> dict:
    """Return order count and sales totals grouped by calendar month."""
    return stats_by_month(category=category, region=region, status=status_filter)

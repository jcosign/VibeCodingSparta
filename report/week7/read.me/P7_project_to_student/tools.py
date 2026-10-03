"""Deterministic demo data and callable tools for the Week 7 agent."""

import ast
import math
import operator
import random
from typing import Any, Callable


CATEGORIES = ("의류", "신발", "가방", "액세서리", "뷰티")


def _make_sales_data() -> list[dict[str, Any]]:
    rng = random.Random(7)
    return [
        {
            "category": category,
            "revenue": rng.randint(100, 500),
            "orders": rng.randint(10, 80),
        }
        for category in CATEGORIES
    ]


SALES_DATA = _make_sales_data()


def lookup_sales(category: str) -> dict[str, Any]:
    """Return revenue and order count for an exact category name."""
    item = next((row for row in SALES_DATA if row["category"] == category.strip()), None)
    if item is None:
        raise ValueError(f"카테고리를 찾을 수 없습니다. 사용 가능: {', '.join(CATEGORIES)}")
    return dict(item)


def total_sales() -> dict[str, int]:
    """Return total revenue and order count across all demo categories."""
    return {
        "revenue": sum(row["revenue"] for row in SALES_DATA),
        "orders": sum(row["orders"] for row in SALES_DATA),
    }


_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _evaluate_expression(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate_expression(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if abs(node.value) > 1_000_000_000_000 or (
            isinstance(node.value, float) and not math.isfinite(node.value)
        ):
            raise ValueError("계산 결과가 허용 범위를 넘었습니다.")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_expression(node.left)
        right = _evaluate_expression(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 8:
            raise ValueError("거듭제곱 지수는 -8부터 8까지만 사용할 수 있습니다.")
        result = _BINARY_OPERATORS[type(node.op)](left, right)
        if abs(result) > 1_000_000_000_000:
            raise ValueError("계산 결과가 허용 범위를 넘었습니다.")
        return result
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_expression(node.operand))
    raise ValueError("숫자와 +, -, *, /, //, %, ** 연산만 사용할 수 있습니다.")


def calc(expression: str) -> dict[str, float | int]:
    """Safely evaluate a basic arithmetic expression without using eval."""
    if len(expression) > 128:
        raise ValueError("수식은 128자 이내로 입력해 주세요.")
    try:
        result = _evaluate_expression(ast.parse(expression, mode="eval"))
    except (SyntaxError, ZeroDivisionError) as error:
        raise ValueError(f"계산할 수 없는 수식입니다: {error}") from error
    return {"expression": expression, "result": result}


def avg_order(category: str) -> dict[str, Any]:
    """Calculate average revenue per order (만원/주문) for one category."""
    sales = lookup_sales(category)
    return {
        "category": sales["category"],
        "revenue": sales["revenue"],
        "orders": sales["orders"],
        "average": round(sales["revenue"] / sales["orders"], 2),
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "calc",
        "desc": "숫자 사칙연산 수식의 정확한 결과를 계산합니다.",
        "parameters": {"expression": "계산할 수식, 예: 306+231"},
        "requires_approval": False,
        "function": calc,
    },
    {
        "name": "lookup_sales",
        "desc": "카테고리 한 곳의 매출(만원)과 주문 수를 조회합니다.",
        "parameters": {"category": f"정확한 카테고리명: {', '.join(CATEGORIES)}"},
        "requires_approval": False,
        "function": lookup_sales,
    },
    {
        "name": "total_sales",
        "desc": "모든 카테고리의 총매출(만원)과 총주문 수를 계산합니다.",
        "parameters": {},
        "requires_approval": False,
        "function": total_sales,
    },
    {
        "name": "avg_order",
        "desc": "카테고리별 매출을 주문 수로 나눠 주문당 평균 매출(만원/주문)을 계산합니다.",
        "parameters": {"category": f"정확한 카테고리명: {', '.join(CATEGORIES)}"},
        "requires_approval": True,
        "function": avg_order,
    },
]

TOOL_BY_NAME = {tool["name"]: tool for tool in TOOLS}

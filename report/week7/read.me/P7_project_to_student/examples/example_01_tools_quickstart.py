"""Call the project's tools directly without starting the web app."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import avg_order, calc, lookup_sales, total_sales


for name, result in (
    ("calc", calc("306+231")),
    ("lookup_sales", lookup_sales("의류")),
    ("total_sales", total_sales()),
    ("avg_order", avg_order("의류")),
):
    print(f"{name}: {result}")


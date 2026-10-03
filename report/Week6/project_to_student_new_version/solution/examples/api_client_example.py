"""실행 중인 FastAPI 서버에서 데이터를 받아오는 예제입니다."""

import requests


BASE_URL = "http://localhost:8600"

summary = requests.get(f"{BASE_URL}/summary", timeout=10)
summary.raise_for_status()
print("요약:", summary.json())

sales = requests.get(f"{BASE_URL}/data", params={"limit": 5}, timeout=10)
sales.raise_for_status()
print("판매 데이터 5건:", sales.json())

top_sales = requests.get(
	f"{BASE_URL}/top",
	params={"category": "전자제품", "limit": 5},
	timeout=10,
)
top_sales.raise_for_status()
print("전자제품 상위 5건:", top_sales.json())

analysis = requests.get(f"{BASE_URL}/analysis", timeout=10)
analysis.raise_for_status()
print("분석:", analysis.json())

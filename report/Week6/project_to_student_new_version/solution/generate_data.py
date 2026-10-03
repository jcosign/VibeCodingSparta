"""numpy를 이용해 연습용 판매 데이터를 생성합니다."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def generate_data(row_count=10_000, seed=42):
    """결측치와 이상치가 일부 포함된 판매 데이터프레임을 만듭니다."""
    if row_count < 1_000:
        raise ValueError("생성 개수는 1,000개 이상이어야 합니다.")

    rng = np.random.default_rng(seed)
    dates = pd.Timestamp("2025-01-01") + pd.to_timedelta(
        rng.integers(0, 365, size=row_count), unit="D"
    )
    data = pd.DataFrame(
        {
            "order_id": np.arange(1, row_count + 1),
            "date": dates.strftime("%Y-%m-%d"),
            "region": rng.choice(["서울", "부산", "대구", "광주", "제주"], row_count),
            "category": rng.choice(["전자제품", "식품", "의류", "생활용품"], row_count),
            "quantity": rng.integers(1, 8, size=row_count),
            "unit_price": rng.integers(5_000, 150_001, size=row_count),
            "discount_rate": rng.choice([0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30], row_count),
            "rating": rng.integers(1, 6, size=row_count).astype(float),
            "age": rng.integers(18, 71, size=row_count).astype(float),
        }
    )
    data["amount"] = data["quantity"] * data["unit_price"]

    # 전처리 실습용 오류 데이터를 고정된 seed로 섞습니다.
    sample_size = max(1, row_count // 100)
    selected = rng.choice(row_count, size=sample_size, replace=False)
    data.loc[selected[: sample_size // 2], "rating"] = np.nan
    data.loc[selected[sample_size // 2 :], "age"] = np.nan

    zero_indexes = rng.choice(row_count, size=max(1, row_count // 200), replace=False)
    data.loc[zero_indexes, "unit_price"] = 0
    data.loc[zero_indexes, "amount"] = 0

    outlier_indexes = rng.choice(row_count, size=max(1, row_count // 500), replace=False)
    data.loc[outlier_indexes, "unit_price"] = 10_000_000
    data.loc[outlier_indexes, "amount"] = (
        data.loc[outlier_indexes, "quantity"] * data.loc[outlier_indexes, "unit_price"]
    )
    data["discount_amount"] = (data["amount"] * data["discount_rate"]).round(2)
    data["net_amount"] = (data["amount"] - data["discount_amount"]).round(2)

    duplicate_count = max(1, row_count // 100)
    duplicates = data.sample(n=duplicate_count, random_state=seed)
    data = pd.concat([data, duplicates], ignore_index=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / "raw_sales.csv"
    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"생성 행 수: {len(data):,}개 (중복 포함)")
    print(f"저장 위치: {output_path}")
    print(data.head(3).to_string(index=False))
    return data


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    generate_data(count)

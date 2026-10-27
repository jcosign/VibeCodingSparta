"""example_02 - 리뷰 분류 → 감정 분포 → 카테고리별 부정 비율 → 표본 검수 (키 불필요).

실행(project 폴더에서): python3 examples/example_02_review_pipeline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_client import classify
from data import reviews_df

df = reviews_df()
df["감정"] = df["리뷰"].map(classify)                       # 규칙 기반 분류

dist = df["감정"].value_counts()
print("감정 분포:", {k: int(dist.get(k, 0)) for k in ["긍정", "부정", "중립"]})

# 실행 가능 지표: 카테고리별 부정 비율 (높은 카테고리부터 점검)
neg = df.groupby("카테고리")["감정"].apply(lambda s: (s == "부정").mean()).sort_values(ascending=False)
print("카테고리별 부정 비율:", {k: f"{v:.0%}" for k, v in neg.items()})

# 표본 검수: 전수 대신 무작위 몇 건을 사람이 눈으로 확인
print("표본 검수(무작위 5건):")
print(df.sample(5, random_state=0)[["카테고리", "별점", "리뷰", "감정"]].to_string(index=False))

# 상식 대조: 별점(1~2=부정, 3=중립, 4~5=긍정)과 분류 결과가 얼마나 맞나
star_label = df["별점"].map(lambda s: "부정" if s <= 2 else ("중립" if s == 3 else "긍정"))
print(f"별점 기준 일치율: {(star_label == df['감정']).mean():.0%}")

assert int(dist.sum()) == len(df)
print("END-TO-END OK")

"""example_01 - HTML 표 → DataFrame → 필요한 열 → 숫자 변환 → 정렬 (D4 블록 A·B, 키 불필요).

실행(프로젝트 폴더에서):  python -m examples.example_01_html_table
"""
import pandas as pd

from extract import html_tables
from sample_docs import SAMPLE_HTML

t = html_tables(SAMPLE_HTML)[0]                       # 첫 번째 표 (행들의 리스트)
df = pd.DataFrame(t[1:], columns=t[0])                # 첫 행(t[0])은 '열 이름', 나머지(t[1:])는 데이터
print(df.to_string(index=False))

df["매출(만원)"] = pd.to_numeric(df["매출(만원)"])     # 글자 → 숫자
print("\n총매출:", df["매출(만원)"].sum(), "만원")

report = df[["카테고리", "매출(만원)"]].sort_values("매출(만원)", ascending=False)   # 필요한 열만, 매출 높은 순
print(report.to_string(index=False))
print("END OK")

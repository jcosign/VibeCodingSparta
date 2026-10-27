"""example_01 - 집계 → AI 요약 → 토큰/비용 → END-TO-END OK (키 불필요).

실행(project 폴더에서): python3 examples/example_01_integrated_report.py
앱을 고친 뒤 '끝까지 도는지' 확인하는 검증 스크립트로 씁니다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # project 폴더의 data.py·ai_client.py 사용

from ai_client import ask, current_mode
from data import orders_df, reviews_df

orders, reviews = orders_df(), reviews_df()

# ① Python으로 집계 (원본 행 → 몇 줄)
cat = orders.groupby("카테고리")["금액_만원"].sum().sort_values(ascending=False)
digest = (f"총매출 {int(orders['금액_만원'].sum())}만원, 총주문 {len(orders)}건, "
          f"1위 카테고리 {cat.index[0]}({int(cat.iloc[0])}만원), 평균별점 {reviews['별점'].mean():.2f}")

print("AI 모드:", current_mode())
print("지표:", digest)

# ② 집계 요약만 AI에게 (max_tokens 작게)
text, meta = ask(system="너는 데이터 분석 리포터야. 주어진 지표를 경영진용 한국어 한 문단으로 요약해.",
                 user=digest, task="summary", max_tokens=200)
if meta["mode"] != current_mode():
    print("(참고) 실제 모드:", meta["mode"])
print("요약:", text)
print(f"토큰 in/out: {meta['input_tokens']}/{meta['output_tokens']} | 비용 ${meta['cost_usd']:.6f}")

# ③ 사람이 숫자 검증 - 요약(참고)의 숫자를 위 '지표:'(원본)와 대조하세요.
assert text.strip(), "요약이 비었습니다"
assert len(orders) > 0 and len(reviews) > 0
print("END-TO-END OK")

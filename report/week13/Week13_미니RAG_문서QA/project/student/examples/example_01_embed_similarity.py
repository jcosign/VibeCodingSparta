"""example_01_embed_similarity.py - 실제 임베딩으로 '가장 비슷한 문장' 찾기 (D2 3-3).

실행(project/student 폴더에서): python3 examples/example_01_embed_similarity.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # embed.py를 찾도록

from embed import cosine, embed

# D2 3-4: 해시 임베딩은 글자가 많이 겹치는 '배송이 빨라요'를 1위로 꼽았습니다. 실제 모델은?
# (실측: multilingual-e5-small도 '배송이 빨라요'를 가장 높게 매깁니다. 작은 임베딩 모델은 '배송'이라는
#  주제는 잘 잡지만 '느리다/빠르다' 같은 반대 뜻 구별은 약할 수 있습니다 - INTEGRATION.md 참고)
q = embed("배송이 너무 느려요")
print('질문: "배송이 너무 느려요"')
for s in ["배송 지연 불만", "가격이 저렴해요", "배송이 빨라요"]:
    print(f"  {cosine(q, embed(s)):+.3f}  {s}")

# D2 3-3: max로 가장 비슷한 후보 하나 뽑기
q = embed("환불하고 싶어요")
cands = ["환불 절차 안내", "포인트 적립", "교환 방법"]
best = max(cands, key=lambda c: cosine(q, embed(c)))
print("\n가장 비슷:", best)
print("END OK")

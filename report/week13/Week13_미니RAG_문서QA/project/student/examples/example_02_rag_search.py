"""example_02_rag_search.py - 색인 → 검색 → 출처와 함께 답 + 정답 표로 검색 품질 확인 (D3 4-3, D4 3-4).

실행(project/student 폴더에서): python3 examples/example_02_rag_search.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # rag.py를 찾도록

from rag import MiniRAG

rag = MiniRAG()
print("색인 문서 수:", rag.build(), "| Chroma:", rag.uses_chroma)

# D3 4-3: "이 질문엔 이 문서가 나와야 한다" 정답 표로 검색 정확도를 숫자로
tests = [
    ("반품하고 싶어요", "반품정책"),
    ("배송 얼마나 걸려요?", "배송기간"),
    ("포인트 어떻게 쌓나요", "포인트적립"),
    ("환불 언제 돼요?", "환불처리"),           # D1 3-5 You Try
    ("쿠폰 두 장 같이 써도 돼요?", "쿠폰사용"),
    ("VIP 되려면요?", "회원등급"),
]
hit = 0
for q, expected in tests:
    top_title, _, score = rag.search(q, 1)[0]
    ok = top_title == expected
    hit += ok
    print(f"{'✅' if ok else '⚠️'} '{q}' → {top_title} ({score}) (기대: {expected})")
print(f"정확도: {hit}/{len(tests)}")

# D4 3-4: 지식베이스에 없는 질문 → 지어내지 않고 "못 찾았다"
for q in ["해외 배송도 되나요?", "우리 회사 주가 얼마예요?"]:
    ans, hits = rag.answer(q)
    print(f"\nQ: {q}\n  1위 근거: {hits[0][0]} ({hits[0][2]})\n  답: {ans}")
print("END OK")

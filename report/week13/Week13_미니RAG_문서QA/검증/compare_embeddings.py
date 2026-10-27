"""compare_embeddings.py - 임베딩 방식별 검색 품질 실측 (INTEGRATION.md '실측 비교'의 근거).

비교 대상
  A. hash      : D2 교안의 문자 1·2-그램 해싱 임베딩(512칸). _norm/_bucket 본문은 교안에 없어
                 "소문자·공백 정리" / "md5 결정적 해시 % dim"으로 구현했습니다.
  B. minilm    : sentence-transformers/all-MiniLM-L6-v2 (접두어 없음)
  C. e5        : intfloat/multilingual-e5-small, 질문 'query: ' / 문서 'passage: ' (student/embed.py 방식)
  D. e5-same   : intfloat/multilingual-e5-small, 질문·문서 모두 'query: '

실행(project/student/.venv 파이썬으로):
  project/student/.venv/Scripts/python.exe 검증/compare_embeddings.py
"""
import hashlib
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project", "student"))
from docs import DOCS  # noqa: E402

# 정답이 있는 질문(질문, 정답 문서)
TESTS = [
    ("반품하고 싶어요", "반품정책"),
    ("배송 얼마나 걸려요?", "배송기간"),
    ("포인트 어떻게 쌓나요", "포인트적립"),
    ("돈을 다시 돌려받고 싶어요", "환불처리"),
    ("물건 돌려보내고 싶어요", "반품정책"),
    ("언제 도착해요?", "배송기간"),
    ("환불 언제 돼요?", "환불처리"),
    ("쿠폰 두 장 같이 써도 돼요?", "쿠폰사용"),
    ("VIP 되려면요?", "회원등급"),
    ("주말에도 배송되나요?", "배송기간"),
    ("사이즈가 안 맞아서 다른 걸로 바꾸고 싶어요", "교환방법"),
    ("상담원이랑 통화하고 싶어요", "고객센터"),
]
# 지식베이스에 답이 없는 질문(임계값 측정용)
NO_ANSWER = ["해외 배송도 되나요?", "우리 회사 주가 얼마예요?", "이 상품 언제 재입고돼요?",
             "오늘 날씨 어때?", "환불 수수료 얼마예요?"]


def hash_embed(text, dim=512):
    v = [0.0] * dim
    t = text.lower().strip().replace(" ", "")
    grams = list(t) + [t[i:i+2] for i in range(len(t) - 1)]
    for g in (grams or [t]):
        v[int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16) % dim] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def st_embedder(name, q_prefix, d_prefix):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(name, device="cpu")
    return (lambda t: m.encode(q_prefix + t, normalize_embeddings=True).tolist(),
            lambda t: m.encode(d_prefix + t, normalize_embeddings=True).tolist())


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def evaluate(label, q_emb, d_emb):
    dvecs = [(t, d_emb(x)) for t, x in DOCS]
    print(f"\n=== {label} ===")
    hit, correct_scores = 0, []
    for q, exp in TESTS:
        qv = q_emb(q)
        ranked = sorted(((t, round(dot(qv, v), 4)) for t, v in dvecs), key=lambda z: -z[1])
        rank = [t for t, _ in ranked].index(exp) + 1
        hit += rank == 1
        correct_scores.append(ranked[0][1])
        print(f"  {'O' if rank == 1 else 'X'} {q!r:<34} 1위={ranked[0][0]}({ranked[0][1]}) "
              f"정답 '{exp}' 순위={rank}/{len(DOCS)}")
    print(f"  top-1 정확도: {hit}/{len(TESTS)}")
    no_scores = []
    for q in NO_ANSWER:
        qv = q_emb(q)
        best = max(((t, round(dot(qv, v), 4)) for t, v in dvecs), key=lambda z: z[1])
        no_scores.append(best[1])
        print(f"  (답 없음) {q!r:<28} 1위={best[0]}({best[1]})")
    print(f"  정답 질문 1위 점수 범위: {min(correct_scores)} ~ {max(correct_scores)}")
    print(f"  답 없는 질문 1위 점수 범위: {min(no_scores)} ~ {max(no_scores)}")


if __name__ == "__main__":
    evaluate("A. hash (D2 문자 n-그램, 512칸)", hash_embed, hash_embed)
    evaluate("B. all-MiniLM-L6-v2", *st_embedder("sentence-transformers/all-MiniLM-L6-v2", "", ""))
    evaluate("C. multilingual-e5-small (query:/passage:)",
             *st_embedder("intfloat/multilingual-e5-small", "query: ", "passage: "))
    evaluate("D. multilingual-e5-small (query:/query:)",
             *st_embedder("intfloat/multilingual-e5-small", "query: ", "query: "))

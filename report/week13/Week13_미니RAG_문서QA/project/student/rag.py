"""rag.py - 미니 RAG (검색 증강 생성). 색인(build/add) → 검색(search) → 출처와 함께 답(answer).

- 임베딩은 embed.py(실제 로컬 모델)가, 저장·검색은 Chroma가 담당합니다(D3 역할 분담).
- Chroma가 설치되어 있지 않으면 순수 파이썬 코사인 정렬로 자동 대체합니다(D3 3-6 폴백).
- 답변 생성은 규칙 기반: 가장 비슷한 문서의 본문을 그대로 보여 주고 출처를 붙입니다(D4 3-2).
"""
import uuid

from docs import DOCS
from embed import cosine, embed

try:
    import chromadb
except ImportError:            # Chroma 없으면 폴백(순수 파이썬)
    chromadb = None

# 1위 근거의 유사도가 이 값보다 낮으면 "관련 문서를 찾지 못했어요"로 답합니다(D4 부록 FAQ의 임계값).
# 값은 INTEGRATION.md '임계값 실측'에서 정했습니다. 내 문서로 바꾸면 다시 측정해 조정하세요.
MIN_SCORE = 0.80


class MiniRAG:
    def __init__(self):
        self._items = []       # (title, text, vec) - 폴백 검색용으로도 보관
        self._col = None
        if chromadb is not None:
            client = chromadb.Client()                                    # 메모리 위 Chroma(서버 불필요)
            self._col = client.create_collection(
                "rag_" + uuid.uuid4().hex[:8],                            # 이름은 매번 랜덤(충돌 방지)
                metadata={"hnsw:space": "cosine"})                        # '가까움'은 코사인으로 잰다

    @property
    def uses_chroma(self) -> bool:
        return self._col is not None

    def add(self, title: str, text: str):
        """문서 하나를 색인. 본문을 직접 임베딩해서 Chroma에 넣는다(키 불필요)."""
        vec = embed(text, prefix="passage: ")                            # 색인 문서는 'passage: '
        self._items.append((title, text, vec))
        if self._col is not None:
            self._col.add(
                ids=[uuid.uuid4().hex],
                documents=[text],
                embeddings=[vec],                                         # ← 임베딩을 '직접' 넣는다
                metadatas=[{"title": title}])                             # 제목 = 출처

    def build(self, docs=DOCS):
        """[준비] 문서 전체를 색인. 넣은 개수를 돌려준다."""
        for title, text in docs:
            self.add(title, text)
        return len(self._items)

    def search(self, question: str, k: int = 2):
        """질문과 가장 비슷한 문서 k개. 반환: [(title, text, score), ...]"""
        qv = embed(question)                                              # 질문은 'query: '(기본값)
        k = max(1, min(k, len(self._items)))
        if self._col is not None:
            r = self._col.query(query_embeddings=[qv], n_results=k)
            out = []
            for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0]):
                out.append((meta.get("title", "?"), doc, round(1 - dist, 4)))   # 코사인 거리 → 유사도
            return out
        # 폴백: Chroma 없으면 순수 파이썬으로 직접 정렬
        scored = [(t, x, cosine(qv, v)) for t, x, v in self._items]
        return sorted(scored, key=lambda z: -z[2])[:k]

    def answer(self, question: str, k: int = 2, min_score: float = MIN_SCORE):
        """검색된 근거로 '출처와 함께' 답한다. 반환: (답변, 근거리스트).

        근거 리스트(hits)는 점수와 상관없이 항상 돌려줍니다(사람이 직접 판단할 수 있도록).
        다만 1위 점수가 min_score 미만이면 지어내지 않고 "관련 문서를 찾지 못했어요."로 답합니다.
        """
        hits = self.search(question, k)
        if not hits or hits[0][2] < min_score:
            return "관련 문서를 찾지 못했어요.", hits
        top_title, top_text, _ = hits[0]
        answer = (f"[{top_title}] {top_text}\n"
                  f"(출처: {', '.join(h[0] for h in hits)} · 규칙 기반 답변)")
        return answer, hits


if __name__ == "__main__":
    rag = MiniRAG()
    n = rag.build()
    print("색인 문서 수:", n, "| Chroma:", rag.uses_chroma)
    for q in ["반품하고 싶어요", "배송 얼마나 걸려요?", "포인트 어떻게 쌓나요", "돈을 다시 돌려받고 싶어요"]:
        ans, hits = rag.answer(q)
        print(f"\nQ: {q}")
        print("  근거:", [(t, s) for t, _, s in hits])
        print("  답:", ans.replace("\n", " "))

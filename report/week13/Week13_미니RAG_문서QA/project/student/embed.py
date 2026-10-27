"""embed.py - 실제 로컬 임베딩 모델로 문장을 벡터로 바꾼다(D2). 키·네트워크 불필요(최초 1회 모델 다운로드 제외).

D2 교안의 embed.py는 '문자 n-그램 해싱'(글자 겹침) 흉내 임베딩이었습니다.
이 버전은 사전학습된 다국어 임베딩 모델(intfloat/multilingual-e5-small, 384차원)을
내 컴퓨터 CPU에서 돌려 '뜻'이 담긴 벡터를 만듭니다. cosine()은 D2와 똑같습니다.

- 최초 1회: 모델(약 450MB)을 내려받아 ~/.cache/huggingface 에 저장, 이후엔 캐시에서 로드
- 다른 모델을 쓰려면: EMBED_MODEL=모델이름 python3 embed.py
"""
import os

MODEL_NAME = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-small")
DIM = 384            # multilingual-e5-small 의 벡터 칸 수(차원). D2의 해시 버전은 512였습니다.

_model = None        # 전역 캐시: 모델 로드는 수 초가 걸리므로 한 번만 읽고 재사용


def _load_model():
    """임베딩 모델을 처음 한 번만 로드해 전역 변수에 보관합니다."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError(
                "sentence-transformers가 설치되어 있지 않습니다. "
                "'bash env_set_up.sh' 또는 'pip install -r requirements.txt'를 먼저 실행하세요."
            ) from e
        _model = SentenceTransformer(MODEL_NAME, device="cpu")
    return _model


def embed(text: str, prefix: str = "query: "):
    """문장을 DIM 길이의 벡터(실수 리스트)로. 길이 1로 정규화(L2)해서 돌려준다.

    e5 계열 모델은 입력 앞에 'query: '(질문) / 'passage: '(문서) 표시를 붙이도록 학습되었습니다.
    질문은 기본값 'query: ', 색인할 문서는 rag.py가 'passage: '를 넘깁니다.
    같은 모델(같은 자)로 재므로 질문 벡터와 문서 벡터를 비교할 수 있습니다(D3 3-1).
    """
    vec = _load_model().encode(prefix + text, normalize_embeddings=True)
    return [float(x) for x in vec]


def cosine(a, b) -> float:
    """두 벡터의 코사인 유사도(-1~1). 임베딩이 정규화돼 있으면 내적과 같다."""
    return round(sum(x * y for x, y in zip(a, b)), 4)


if __name__ == "__main__":
    print("모델:", MODEL_NAME)
    v = embed("배송이 너무 느려요")
    print("벡터 길이:", len(v))
    print("앞 5칸:", [round(x, 4) for x in v[:5]])
    q = embed("배송이 너무 느려요")
    print('질문: "배송이 너무 느려요"')
    for s in ["배송 지연 불만", "가격이 저렴해요", "배송이 빨라 좋아요"]:
        print(f"  {cosine(q, embed(s)):+.3f}  {s}")

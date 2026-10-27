"""app.py - 미니 RAG 문서 Q&A (Streamlit).

실행:  streamlit run app.py
선택:  USE_CLAUDE_CLI=1 streamlit run app.py   (Claude CLI가 있으면 답변을 자연어로 한 번 더 다듬음, 없으면 조용히 skip)
선택:  USE_CODEX_CLI=1  streamlit run app.py   (Codex CLI 경로, Claude와 독립)

흐름: docs.py(DOCS) → rag.MiniRAG.build() → embed.embed() → Chroma
      질문 → embed(question) → MiniRAG.search() → MiniRAG.answer() → 답변 + 근거 표
"""
import pandas as pd
import streamlit as st

import embed as em
from cli_augment import augment, enabled_clis, unverified_numbers
from docs import DOCS
from rag import MIN_SCORE, MiniRAG

st.set_page_config(page_title="미니 RAG 문서 Q&A", page_icon="🔎", layout="wide")
st.title("🔎 미니 RAG 문서 Q&A")
st.caption("사내 FAQ에서 질문과 뜻이 가장 비슷한 문서를 찾아, 그 문서를 근거(출처)로 답합니다. "
           "임베딩·검색·답변 모두 내 컴퓨터에서, API 키 없이.")


@st.cache_resource(show_spinner="임베딩 모델을 불러오고 문서를 색인하는 중... (최초 1회는 모델 다운로드로 오래 걸릴 수 있어요)")
def get_rag():
    rag = MiniRAG()
    rag.build()
    return rag


try:
    rag = get_rag()
except Exception as e:                                   # 모델 미설치·다운로드 실패 등 → 앱은 죽지 않고 안내
    st.error(f"임베딩 모델을 준비하지 못했습니다: {type(e).__name__}: {e}\n\n"
             "'bash env_set_up.sh'를 실행했는지, 최초 실행이라면 인터넷이 연결되어 있는지 확인하세요"
             "(INTEGRATION.md 트러블슈팅 참고).")
    st.stop()

with st.sidebar:
    st.header("설정")
    k = st.slider("근거 문서 수 (k)", min_value=1, max_value=len(DOCS), value=2,
                  help="질문과 가장 비슷한 문서를 몇 개 가져올지(D3 3-4 Top-k).")
    min_score = st.slider("최소 유사도(임계값)", min_value=0.0, max_value=1.0, value=MIN_SCORE, step=0.01,
                          help="1위 근거의 유사도가 이 값보다 낮으면 지어내지 않고 '관련 문서를 찾지 못했어요'로 답합니다.")
    st.header("엔진 상태")
    st.markdown(f"**임베딩 모델:** `{em.MODEL_NAME}` ({em.DIM}차원, 로컬 CPU)")
    st.markdown("**VectorDB:** " + ("🟢 Chroma" if rag.uses_chroma else "🟡 Chroma 없음 → 순수 파이썬 코사인 검색(폴백)"))
    clis = enabled_clis()
    st.markdown("**CLI 다듬기:** " + (", ".join(clis) + " 켜짐" if clis else "꺼짐(로컬 모드)"))
    with st.expander(f"지식베이스 ({len(DOCS)}건)"):
        for t, x in DOCS:
            st.markdown(f"**{t}** — {x}")

examples = ["반품하고 싶어요", "배송 얼마나 걸려요?", "포인트 어떻게 쌓나요", "돈을 다시 돌려받고 싶어요", "해외 배송도 되나요?"]
st.markdown("**예시 질문**")
cols = st.columns(len(examples))
for c, ex in zip(cols, examples):
    if c.button(ex, key=f"ex_{ex}"):
        st.session_state["question"] = ex

question = st.text_input("질문을 입력하세요", key="question", placeholder="예: 쿠폰 두 장 같이 써도 돼요?")

if question.strip():
    with st.spinner("관련 문서를 찾는 중..."):
        answer, hits = rag.answer(question, k=k, min_score=min_score)

    st.subheader("답변")
    if hits and hits[0][2] >= min_score:
        st.success(answer)
    else:
        st.warning(answer + f"\n\n(1위 근거의 유사도가 임계값 {min_score:.2f}보다 낮습니다. "
                   "이 질문에 답하려면 관련 문서를 docs.py에 추가하세요.)")

    st.subheader("근거(출처)")
    st.dataframe(
        pd.DataFrame([{"순위": i, "출처(제목)": t, "유사도": s, "본문": x} for i, (t, x, s) in enumerate(hits, 1)]),
        hide_index=True, width="stretch")
    st.caption("유사도 = 1 - 코사인 거리(클수록 비슷). 점수가 낮으면 '억지로 끌어온' 근거일 수 있으니 "
               "출처 원문과 답을 직접 대조하세요(D4 4-2 검증 3문).")

    if clis and hits and hits[0][2] >= min_score:
        with st.spinner("CLI로 답변을 다듬는 중..."):
            polished = augment(question, hits)
        evidence = " ".join(x for _, x, _ in hits)
        labels = {"claude": "🤖 Claude CLI가 다듬은 답변", "codex": "🤖 Codex CLI가 다듬은 답변"}
        for name, text in polished.items():               # 실패·미설치 CLI는 dict에 없음 → 박스가 안 보임(정상)
            st.subheader(labels[name])
            st.info(text)
            bad = unverified_numbers(text, evidence)
            if bad:
                st.warning(f"⚠️ 근거 문서에 없는 숫자가 있습니다: {', '.join(bad)} → 출처 원문 확인 필요")
            else:
                st.caption("✅ 다듬은 답변 속 숫자가 모두 근거 문서에 있습니다(숫자 대조 통과).")

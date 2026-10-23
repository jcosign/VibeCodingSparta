"""Streamlit 채팅 웹앱 - LangChain 업무 비서.

실행: streamlit run app.py   (또는 bash run.sh)
"""
import streamlit as st

from agent import MemoryAgent
from llm import LOCAL_MODEL, current_mode

st.set_page_config(page_title="LangChain 업무 비서", page_icon="🤖")

MODE_BADGE = {"local": "🟢 local", "openai": "🔵 openai", "anthropic": "🔵 anthropic", "mock": "🟡 mock"}

# 세션마다 에이전트(=메모리) 하나. 새로고침/재시작하면 사라진다(영속화 X).
if "agent" not in st.session_state:
    st.session_state.agent = MemoryAgent()
agent = st.session_state.agent

with st.sidebar:
    st.header("🤖 업무 비서")
    with st.spinner("모델 확인 중... (첫 실행은 모델 다운로드로 오래 걸릴 수 있어요)"):
        mode = current_mode()
    st.markdown(f"**모드:** {MODE_BADGE.get(mode, mode)}")
    if mode == "local":
        st.caption(f"로컬 모델: {LOCAL_MODEL}")
    st.markdown(
        "**이렇게 입력해 보세요**\n"
        "1. 내 이름은 홍길동이야\n"
        "2. 12*8 계산해줘\n"
        "3. 환불 규정 알려줘\n"
        "4. 내 이름 뭐였지?"
    )
    st.caption(f"메모리 길이(turns): {len(agent.history)}")
    if st.button("🗑 대화 초기화"):
        agent.history.clear()
        st.rerun()

st.title("LangChain 업무 비서")
st.caption("계산·FAQ는 도구가, 대화는 LLM이 답합니다. [calc]/[faq] 접두사 = 도구 응답")

for h in agent.history:
    with st.chat_message("user" if h["role"] == "사용자" else "assistant"):
        st.markdown(h["content"])

if user := st.chat_input("메시지를 입력하세요"):
    with st.chat_message("user"):
        st.markdown(user)
    with st.spinner("답변 생성 중..."):
        agent.chat(user)
    st.rerun()

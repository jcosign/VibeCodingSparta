"""Streamlit UI for the Week 7 mini data Q&A agent."""

import os

import streamlit as st

from agent import run_agent
from tools import CATEGORIES, SALES_DATA, TOOLS


st.set_page_config(page_title="미니 데이터 Q&A 에이전트", page_icon="🧰", layout="centered")
st.title("🧰 미니 데이터 Q&A 에이전트")
st.caption("질문에 맞는 도구를 선택해 코드로 매출을 조회하고 계산합니다.")

mode = os.getenv("AI_MODE", "mock").lower()
st.info(f"현재 모드: **{mode}** · 기본 mock 모드는 API 키 없이 동작합니다.")

with st.expander("교육용 데이터와 카테고리 보기"):
    st.write(f"사용 가능한 카테고리: {', '.join(CATEGORIES)}")
    st.dataframe(SALES_DATA, hide_index=True, width="stretch")
    st.caption("출처: tools.py가 seed=7로 생성한 교육용 합성 데이터입니다. 실제 기업 데이터가 아닙니다.")

with st.expander("도구 승인 정책"):
    st.write("도구 정의에 `requires_approval=True`를 설정하면, 도구가 선택된 뒤 별도 승인 버튼을 눌러야 실행됩니다.")
    approval_tools = [tool["name"] for tool in TOOLS if tool.get("requires_approval")]
    st.write("현재 승인 대상:", ", ".join(approval_tools) or "없음")

examples = [
    "의류 매출 알려줘",
    "총매출은 얼마야?",
    "306+231",
    "의류 객단가 알려줘",
    "의류 매출과 주문당 평균을 함께 알려줘",
    "오늘 날씨 어때?",
]
st.subheader("예시 질문")
columns = st.columns(len(examples))
for index, sample in enumerate(examples):
    if columns[index].button(sample, key=f"example-{index}", use_container_width=True):
        st.session_state["question"] = sample

question = st.text_input(
    "질문",
    key="question",
    placeholder="예: 신발 매출은? / 전체 매출? / 306+231?",
)

if st.button("질문하기", type="primary", disabled=not question.strip()):
    answer, trace = run_agent(question)
    st.session_state["last_answer"] = answer
    st.session_state["last_trace"] = trace
    approval = next((item for item in trace if item["step"] == "승인 대기"), None)
    if approval:
        st.session_state["pending_approval"] = {
            "question": question,
            "tool": approval["detail"],
        }
    else:
        st.session_state.pop("pending_approval", None)

if "pending_approval" in st.session_state:
    pending = st.session_state["pending_approval"]
    st.warning(f"`{pending['tool']}` 도구가 선택됐습니다. 실행하려면 명시적으로 승인하세요.")
    approve_column, cancel_column = st.columns(2)
    if approve_column.button("승인하고 실행", type="primary", key="approve-tool"):
        answer, trace = run_agent(pending["question"], approved_tool=pending["tool"])
        st.session_state["last_answer"] = answer
        st.session_state["last_trace"] = trace
        st.session_state.pop("pending_approval", None)
        st.rerun()
    if cancel_column.button("취소", key="cancel-tool"):
        st.session_state["last_answer"] = "도구 실행 승인이 취소되어 아무 작업도 실행하지 않았습니다."
        st.session_state["last_trace"] = [
            *st.session_state.get("last_trace", []),
            {"step": "승인 취소", "detail": f"{pending['tool']} 도구를 실행하지 않았습니다."},
        ]
        st.session_state.pop("pending_approval", None)
        st.rerun()

if "last_answer" in st.session_state:
    st.subheader("답변")
    st.success(st.session_state["last_answer"])
    st.subheader("실행 트레이스")
    for step in st.session_state["last_trace"]:
        st.write(f"**{step['step']}** — {step['detail']}")

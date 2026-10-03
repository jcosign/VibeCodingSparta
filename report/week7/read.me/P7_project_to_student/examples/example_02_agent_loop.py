"""Run sample questions through the mock agent and print its trace."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import run_agent


QUESTIONS = (
    "의류 매출 알려줘",
    "총매출은 얼마야?",
    "306+231",
    "의류 객단가 알려줘",
    "오늘 날씨 어때?",
)

for question in QUESTIONS:
    answer, trace = run_agent(question, mode="mock")
    print(f"\n질문: {question}\n답변: {answer}")
    for step in trace:
        print(f"  - {step['step']}: {step['detail']}")


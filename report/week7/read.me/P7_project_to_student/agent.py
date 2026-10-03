"""A small tool-using agent with a deterministic mock mode."""

import json
import os
import re
from typing import Any

from tools import CATEGORIES, TOOL_BY_NAME, TOOLS


def _decide_mock(question: str) -> tuple[str | None, dict[str, Any], str]:
    normalized = question.strip().lower()

    if any(word in normalized for word in ("평균", "객단가", "주문당")):
        category = next((name for name in CATEGORIES if name in question), None)
        if category:
            return "avg_order", {"category": category}, f"{category}의 주문당 평균 매출 질문"
        return None, {}, "평균 매출을 계산할 카테고리명이 없습니다."

    if any(word in normalized for word in ("총매출", "전체 매출", "전체매출", "합계", "총 매출")):
        return "total_sales", {}, "전체 매출 또는 합계를 요청한 질문"

    category = next((name for name in CATEGORIES if name in question), None)
    if category:
        return "lookup_sales", {"category": category}, f"{category} 카테고리 매출 조회 질문"

    expression = re.search(r"(?<!\w)\d+(?:\.\d+)?(?:\s*[\+\-*/%]\s*\d+(?:\.\d+)?)+(?!\w)", question)
    if expression:
        return "calc", {"expression": expression.group(0)}, "숫자 수식 계산 질문"

    return None, {}, "지원하는 매출 조회나 계산 도구를 찾지 못했습니다."


def _decide_llm(question: str, mode: str) -> tuple[str | None, dict[str, Any], str]:
    if mode == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        try:
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
                max_tokens=256,
                tools=[
                    {
                        "name": tool["name"],
                        "description": tool["desc"],
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                key: {"type": "string", "description": description}
                                for key, description in tool["parameters"].items()
                            },
                            "required": list(tool["parameters"]),
                        },
                    }
                    for tool in TOOLS
                ],
                messages=[{"role": "user", "content": question}],
            )
        except anthropic.APIError as error:
            raise ValueError(f"Anthropic 요청 실패: {error}") from error
        selected = next((block for block in response.content if block.type == "tool_use"), None)
        if selected is None:
            return None, {}, "LLM이 실행할 도구를 선택하지 않았습니다."
        return selected.name, dict(selected.input), "Anthropic Tool Calling에서 도구 선택"

    if mode == "openai":
        import openai
        from openai import OpenAI

        client = OpenAI()
        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": question}],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["desc"],
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    key: {"type": "string", "description": description}
                                    for key, description in tool["parameters"].items()
                                },
                                "required": list(tool["parameters"]),
                            },
                        },
                    }
                    for tool in TOOLS
                ],
                tool_choice="required",
            )
        except openai.APIError as error:
            raise ValueError(f"OpenAI 요청 실패: {error}") from error
        call = response.choices[0].message.tool_calls[0]
        return call.function.name, json.loads(call.function.arguments), "OpenAI Tool Calling에서 도구 선택"

    raise ValueError(f"지원하지 않는 AI_MODE입니다: {mode}")


def _run_multistep_mock(question: str, trace: list[dict[str, str]]) -> str | None:
    normalized = question.strip().lower()
    category = next((name for name in CATEGORIES if name in question), None)
    asks_for_average = any(word in normalized for word in ("평균", "객단가", "주문당"))
    asks_for_lookup_then_calculation = any(
        phrase in normalized
        for phrase in ("매출과", "매출 및", "조회하고", "조회해서", "조회한 뒤", "조회한 다음")
    )
    if category is None or not asks_for_average or not asks_for_lookup_then_calculation:
        return None

    lookup_tool = TOOL_BY_NAME["lookup_sales"]
    calc_tool = TOOL_BY_NAME["calc"]
    calls = (
        (lookup_tool, {"category": category}, f"{category} 매출을 먼저 조회"),
    )
    results: list[dict[str, Any]] = []
    for tool, arguments, reason in calls:
        trace.append({"step": "도구 선택", "detail": f"{tool['name']}: {reason}"})
        result = tool["function"](**arguments)
        results.append(result)
        trace.append(
            {"step": "도구 실행", "detail": f"{tool['name']}: {json.dumps(result, ensure_ascii=False, sort_keys=True)}"}
        )

    sales = results[0]
    expression = f"{sales['revenue']}/{sales['orders']}"
    trace.append({"step": "도구 선택", "detail": f"calc: 조회 결과의 매출을 주문 수로 나눔 ({expression})"})
    average = calc_tool["function"](expression=expression)
    trace.append(
        {"step": "도구 실행", "detail": f"{calc_tool['name']}: {json.dumps(average, ensure_ascii=False, sort_keys=True)}"}
    )
    return (
        f"{sales['category']} 매출은 {sales['revenue']}만원, 주문 수는 {sales['orders']}건입니다. "
        f"주문당 평균 매출은 {average['result']:.2f}만원입니다."
    )


def run_agent(
    question: str,
    mode: str | None = None,
    approved_tool: str | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """Choose one tool, execute it, and return a Korean answer plus a user-facing trace."""
    selected_mode = (mode or os.getenv("AI_MODE", "mock")).strip().lower()
    trace: list[dict[str, str]] = [
        {"step": "질문", "detail": question.strip() or "(빈 질문)"},
    ]

    if not question.strip():
        trace.append({"step": "안전 처리", "detail": "질문을 입력하지 않아 도구를 실행하지 않았습니다."})
        return "질문을 입력해 주세요.", trace

    if selected_mode in ("anthropic", "openai"):
        required_key = "ANTHROPIC_API_KEY" if selected_mode == "anthropic" else "OPENAI_API_KEY"
        if not os.getenv(required_key):
            trace.append({"step": "LLM 폴백", "detail": f"{required_key}가 없어 mock 규칙으로 전환했습니다."})
            selected_mode = "mock"
            tool_name, arguments, reason = _decide_mock(question)
        else:
            try:
                tool_name, arguments, reason = _decide_llm(question, selected_mode)
            except (ImportError, ValueError, json.JSONDecodeError) as error:
                trace.append({"step": "LLM 폴백", "detail": f"{selected_mode} 설정/응답 오류: {error}. mock 규칙으로 전환했습니다."})
                selected_mode = "mock"
                tool_name, arguments, reason = _decide_mock(question)
    elif selected_mode == "mock":
        tool_name, arguments, reason = _decide_mock(question)
    else:
        trace.append({"step": "모드 오류", "detail": f"지원하지 않는 모드: {selected_mode}"})
        return f"지원하지 않는 AI_MODE입니다: {selected_mode}", trace

    trace.append({"step": "모드", "detail": selected_mode})
    if selected_mode == "mock":
        try:
            multistep_answer = _run_multistep_mock(question, trace)
        except (TypeError, ValueError, ZeroDivisionError) as error:
            trace.append({"step": "도구 오류", "detail": str(error)})
            return f"다단계 도구 실행에 실패했습니다: {error}", trace
        if multistep_answer is not None:
            return multistep_answer, trace

    if tool_name is None:
        trace.append({"step": "도구 선택", "detail": reason})
        return "쓸 수 있는 도구가 없어요. 매출, 총매출, 주문당 평균 매출 또는 숫자 계산을 질문해 주세요.", trace

    tool = TOOL_BY_NAME.get(tool_name)
    if tool is None:
        trace.append({"step": "안전 처리", "detail": f"등록되지 않은 도구({tool_name})를 차단했습니다."})
        return "선택한 도구를 안전하게 실행할 수 없습니다.", trace

    expected_arguments = set(tool["parameters"])
    if not isinstance(arguments, dict) or set(arguments) != expected_arguments or not all(
        isinstance(value, str) for value in arguments.values()
    ):
        trace.append({"step": "안전 처리", "detail": f"{tool_name} 도구 입력값이 정의된 형식과 달라 실행을 차단했습니다."})
        return "선택한 도구의 입력값이 올바르지 않습니다.", trace

    trace.append({"step": "도구 선택", "detail": f"{tool_name}: {reason}"})
    if tool.get("requires_approval", False):
        if approved_tool != tool_name:
            trace.append({"step": "승인 대기", "detail": tool_name})
            return f"{tool_name} 도구는 실행 전에 사용자의 승인이 필요합니다.", trace
        trace.append({"step": "승인", "detail": f"{tool_name} 실행을 사용자가 승인했습니다."})

    try:
        result = tool["function"](**arguments)
    except (TypeError, ValueError, ZeroDivisionError) as error:
        trace.append({"step": "도구 오류", "detail": str(error)})
        return f"요청한 도구를 실행하지 못했습니다: {error}", trace
    trace.append({"step": "도구 실행", "detail": json.dumps(result, ensure_ascii=False, sort_keys=True)})
    return _format_answer(tool_name, result), trace


def _format_answer(tool_name: str, result: dict[str, Any]) -> str:
    if tool_name == "calc":
        return f"{result['expression']} = {result['result']}"
    if tool_name == "lookup_sales":
        return f"{result['category']} 매출은 {result['revenue']}만원, 주문 수는 {result['orders']}건입니다."
    if tool_name == "total_sales":
        return f"전체 매출은 {result['revenue']}만원, 총 주문 수는 {result['orders']}건입니다."
    if tool_name == "avg_order":
        return f"{result['category']} 주문당 평균 매출은 {result['average']}만원/주문입니다."
    return "도구 실행이 완료되었습니다."

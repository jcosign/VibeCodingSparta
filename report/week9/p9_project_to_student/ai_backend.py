"""선택형 LLM 백엔드. 설정이 없거나 호출에 실패하면 mock으로 대체합니다."""

from __future__ import annotations

import logging
import os
import subprocess
from importlib import import_module
from typing import Any


logger = logging.getLogger(__name__)
SUPPORTED_MODES = ("mock", "claude", "openai", "openrouter", "claude-cli", "codex-cli")


def _mock_answer(prompt: str) -> str:
    preview = " ".join(prompt.split())
    if len(preview) > 180:
        preview = f"{preview[:177]}..."
    return f"[mock 응답] 입력 내용을 확인했습니다: {preview or '(빈 입력)'}"


def _anthropic_answer(prompt: str) -> str:
    anthropic = import_module("anthropic")
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=os.getenv("AI_MODEL", "claude-3-5-haiku-latest"),
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(block.text for block in response.content if hasattr(block, "text"))


def _openai_answer(prompt: str, *, openrouter: bool = False) -> str:
    options: dict[str, Any] = {}
    if openrouter:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY 환경 변수가 설정되지 않았습니다.")
        options["base_url"] = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        options["api_key"] = api_key
    OpenAI = import_module("openai").OpenAI
    client = OpenAI(**options)
    response = client.chat.completions.create(
        model=os.getenv("AI_MODEL", "openai/gpt-4o-mini" if openrouter else "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )
    return response.choices[0].message.content or ""


def _cli_answer(command: list[str], prompt: str) -> str:
    result = subprocess.run(
        [*command, prompt],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
        encoding="utf-8",
    )
    return result.stdout.strip()


def ask(prompt: str, mode: str | None = None) -> str:
    """선택한 AI_MODE에 질문하고, 실패하면 사유를 로그에 남긴 뒤 mock 응답을 줍니다."""
    if not isinstance(prompt, str):
        raise TypeError("프롬프트는 문자열이어야 합니다.")

    selected_mode = (mode or os.getenv("AI_MODE", "mock")).strip().casefold()
    if selected_mode not in SUPPORTED_MODES:
        raise ValueError(f"지원하지 않는 AI_MODE입니다: {selected_mode!r}")
    if selected_mode == "mock":
        return _mock_answer(prompt)

    try:
        if selected_mode == "claude":
            return _anthropic_answer(prompt)
        if selected_mode == "openai":
            return _openai_answer(prompt)
        if selected_mode == "openrouter":
            return _openai_answer(prompt, openrouter=True)
        if selected_mode == "claude-cli":
            return _cli_answer(["claude", "-p"], prompt)
        return _cli_answer(["codex", "exec"], prompt)
    except Exception as error:
        logger.warning(
            "%s 백엔드 호출에 실패해 mock으로 대체합니다: %s",
            selected_mode,
            error,
            exc_info=True,
        )
        return _mock_answer(prompt)

"""Optional text-generation backends used by the Week 7 integration example."""

import os
import subprocess
from typing import Any


class BackendRequestError(RuntimeError):
    """A provider SDK rejected or could not complete a request."""


def _generate(prompt: str, mode: str) -> str:
    if mode == "claude":
        import anthropic

        try:
            response = anthropic.Anthropic().messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as error:
            raise BackendRequestError(f"Anthropic 요청 실패: {error}") from error
        return "\n".join(block.text for block in response.content if block.type == "text")

    if mode in ("openai", "openrouter"):
        import openai
        from openai import OpenAI

        try:
            if mode == "openrouter":
                client = OpenAI(
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1",
                )
                model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
            else:
                client = OpenAI()
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
        except openai.APIError as error:
            raise BackendRequestError(f"OpenAI 호환 API 요청 실패: {error}") from error
        return response.choices[0].message.content or ""

    if mode == "claude-cli":
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=90,
        )
        return result.stdout.strip()

    if mode == "codex-cli":
        result = subprocess.run(
            ["codex", "exec", prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=90,
        )
        return result.stdout.strip()

    raise ValueError(f"지원하지 않는 AI_MODE입니다: {mode}")


def complete(prompt: str, mode: str | None = None) -> dict[str, Any]:
    """Generate text, explicitly reporting a mock fallback when a backend is unavailable."""
    selected_mode = (mode or os.getenv("AI_MODE", "mock")).strip().lower()
    if selected_mode == "mock":
        return {"text": f"[mock 응답] 입력 내용을 확인했습니다: {prompt}", "mode": "mock", "fallback": None}

    key_by_mode = {
        "claude": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    key_name = key_by_mode.get(selected_mode)
    if key_name and not os.getenv(key_name):
        reason = f"{key_name}가 설정되지 않았습니다."
        return _mock_fallback(prompt, selected_mode, reason)

    try:
        text = _generate(prompt, selected_mode)
    except ImportError as error:
        reason = f"필요한 SDK를 설치할 수 없습니다: {error}"
    except (BackendRequestError, OSError, subprocess.SubprocessError, ValueError) as error:
        reason = f"백엔드를 실행할 수 없습니다: {error}"
    else:
        return {"text": text, "mode": selected_mode, "fallback": None}

    return _mock_fallback(prompt, selected_mode, reason)


def _mock_fallback(prompt: str, requested_mode: str, reason: str) -> dict[str, Any]:
    return {
        "text": f"[mock 폴백] {reason} 입력 내용을 확인했습니다: {prompt}",
        "mode": "mock",
        "fallback": f"{requested_mode}: {reason}",
    }

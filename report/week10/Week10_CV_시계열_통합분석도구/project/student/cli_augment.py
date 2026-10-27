"""cli_augment.py - 로컬(기본) + Claude/Codex CLI(선택) 하이브리드 모듈.

기본 동작은 "아무것도 하지 않음"입니다. 로컬 모델 결과만으로 앱은 완성되어 있고,
환경변수를 켰을 때만 CLI 코딩 에이전트에게 결과 요약을 보내 자연어 해설 한 줄을 덧붙입니다.

- USE_CLAUDE_CLI=1 : `claude -p "<질문>"` 로 Claude Code CLI 해설 요청
- USE_CODEX_CLI=1  : `codex exec "<질문>"` 로 Codex CLI 해설 요청
- 두 플래그는 서로 독립적입니다(하나만 켜도, 둘 다 켜도 됨).
- CLI가 설치되어 있지 않거나, 로그인이 안 되어 있거나, 시간이 초과되거나, 오류가 나면
  조용히 건너뜁니다(예외를 밖으로 던지지 않으므로 앱이 죽지 않습니다).

보안: CLI에는 이미지·CSV 원본이 아니라 "결과 요약 텍스트"(라벨·숫자)만 보냅니다.
민감한 회사 데이터를 다룰 때는 이 요약도 외부로 나가도 되는지 먼저 확인하세요(D1·D2 보안 한 줄).
"""
import os
import shutil
import subprocess

TIMEOUT_SEC = int(os.getenv("CLI_TIMEOUT_SEC", "60"))

_PROMPT = (
    "다음은 로컬 AI 모델의 결과 요약입니다. 비전공자 직장인이 이해할 수 있도록 "
    "한국어로 두세 문장 이내로 해설해 주세요. 결과에 없는 숫자는 만들지 마세요.\n\n"
    "[작업] {task}\n[결과]\n{summary}"
)


def _flag(name):
    return os.getenv(name, "").strip() == "1"


def enabled_clis():
    """켜져 있는 CLI 플래그 목록(설치 여부와 무관). 사이드바 표시용."""
    names = []
    if _flag("USE_CLAUDE_CLI"):
        names.append("claude")
    if _flag("USE_CODEX_CLI"):
        names.append("codex")
    return names


def _run(cmd):
    """CLI를 실행해 표준출력을 돌려줍니다. 어떤 실패든 None."""
    exe = shutil.which(cmd[0])
    if exe is None:
        return None                                  # 설치 안 됨 → 조용히 skip
    try:
        proc = subprocess.run(
            [exe, *cmd[1:]],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=TIMEOUT_SEC,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None                                  # 로그인 안 됨 등 → 조용히 skip
    text = (proc.stdout or "").strip()
    return text or None


def augment(task, summary):
    """결과 요약에 CLI 해설을 덧붙입니다.

    반환: {"claude": "해설", "codex": "해설"} 중 성공한 것만 담긴 dict.
          플래그가 모두 꺼져 있거나 전부 실패하면 빈 dict {}.
    """
    out = {}
    prompt = _PROMPT.format(task=task, summary=summary)
    if _flag("USE_CLAUDE_CLI"):
        text = _run(["claude", "-p", prompt])
        if text:
            out["claude"] = text
    if _flag("USE_CODEX_CLI"):
        text = _run(["codex", "exec", prompt])
        if text:
            out["codex"] = text
    return out


if __name__ == "__main__":
    print("켜진 플래그:", enabled_clis() or "없음(로컬 모드)")
    print("augment 결과:", augment("이미지 분류", "1위 tabby (62.1%)"))

"""cli_augment.py - 로컬(기본) + Claude/Codex CLI(선택) 하이브리드 모듈.

기본 동작은 "아무것도 하지 않음"입니다. 로컬 검색 + 규칙 기반 답변만으로 앱은 완성되어 있고,
환경변수를 켰을 때만 CLI 코딩 에이전트에게 "질문 + 검색된 근거 문서"를 보내 자연어 답변으로 다듬습니다.

- USE_CLAUDE_CLI=1 : `claude -p "<요청>"` 로 Claude Code CLI에 다듬기 요청
- USE_CODEX_CLI=1  : `codex exec "<요청>"` 로 Codex CLI에 다듬기 요청
- 두 플래그는 서로 독립적입니다(하나만 켜도, 둘 다 켜도 됨).
- CLI가 설치되어 있지 않거나, 로그인이 안 되어 있거나, 시간이 초과되거나, 오류가 나면
  조용히 건너뜁니다(예외를 밖으로 던지지 않으므로 앱이 죽지 않습니다 → 규칙 기반 답변 그대로).

보안: CLI에는 지식베이스 전체가 아니라 '검색된 근거 문서 k개'와 질문만 보냅니다.
그래도 외부로 나가는 내용이므로, 실제 사내 문서라면 민감정보가 없는지 먼저 확인하세요(D4 4-3).
"""
import os
import re
import shutil
import subprocess

TIMEOUT_SEC = int(os.getenv("CLI_TIMEOUT_SEC", "60"))

# D4 3-4 RAG 황금률을 그대로 지시: 근거로만 답 + 출처 표시 + 근거 없으면 모른다고
_PROMPT = (
    "당신은 쇼핑몰 CS 도우미입니다. 아래 '근거 문서'에 있는 내용으로만 질문에 한국어 2~3문장으로 답하세요.\n"
    "- 근거 문서에 없는 내용·숫자는 지어내지 마세요. 숫자는 근거 문서 그대로 옮기세요.\n"
    "- 근거 문서로 답할 수 없으면 \"문서에 없어 확인이 필요합니다\"라고만 답하세요.\n"
    "- 답 끝에 근거로 쓴 문서 제목을 (출처: 제목) 형식으로 붙이세요.\n"
    "답변만 출력하세요.\n\n"
    "[근거 문서]\n{evidence}\n\n[질문] {question}"
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


def unverified_numbers(text, evidence):
    """text 속 숫자 중 근거 문서(evidence)에 없는 것. D4 4-2 검증 3문 ③(근거대로 답했나)을 자동으로 확인."""
    nums = set(re.findall(r"\d+(?:\.\d+)?", text))
    return sorted(n for n in nums if n not in evidence)


def augment(question, hits):
    """검색된 근거(hits: [(title, text, score), ...])로 CLI에게 자연어 답변을 요청합니다.

    반환: {"claude": "다듬은 답변", "codex": "다듬은 답변"} 중 성공한 것만 담긴 dict.
          플래그가 모두 꺼져 있거나, 근거가 없거나, 전부 실패하면 빈 dict {}.
    """
    out = {}
    if not hits:
        return out
    evidence = "\n".join(f"- ({t}) {x}" for t, x, _ in hits)
    prompt = _PROMPT.format(evidence=evidence, question=question)
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
    demo_hits = [("반품정책", "구매 후 7일 이내 미개봉 상품은 무료 반품이 가능합니다. 개봉 상품은 불량일 때만 반품됩니다.", 0.9)]
    print("augment 결과:", augment("반품 며칠 안에 가능해요?", demo_hits))

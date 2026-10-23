"""하이브리드 CLI 확장(선택).

USE_CLAUDE_CLI=1 / USE_CODEX_CLI=1 이 켜져 있고 해당 CLI가 설치돼 있으면,
LLM 응답 뒤에 그 CLI가 만든 짧은 자연어 해설을 덧붙인다.
꺼져 있거나 CLI가 없거나 실패하면 원래 응답을 그대로 돌려준다(조용히 skip).

보안: 외부 CLI로 보내기 전에 대화의 개인정보를 가린다(mask_pii).
"""
import os
import re
import shutil
import subprocess

TIMEOUT = int(os.getenv("CLI_AUGMENT_TIMEOUT", "60"))

# (켜는 환경변수, 표시 이름, 실행 파일, 프롬프트 → 인자 목록)
CLIS = [
    ("USE_CLAUDE_CLI", "Claude CLI", "claude", lambda p: ["-p", p]),
    ("USE_CODEX_CLI", "Codex CLI", "codex", lambda p: ["exec", p]),
]


def mask_pii(text: str) -> str:
    """주민번호·카드·전화·이메일을 자리표시자로 치환."""
    text = re.sub(r"\d{6}-\d{7}", "[주민번호]", text)
    text = re.sub(r"\d{4}-\d{4}-\d{4}-\d{4}", "[카드번호]", text)
    text = re.sub(r"\d{2,3}-\d{3,4}-\d{4}", "[전화]", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[이메일]", text)
    return text


def _run(exe_path: str, args: list) -> str:
    try:
        r = subprocess.run([exe_path, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def augment(user: str, reply: str) -> str:
    notes = []
    for env, label, exe, build_args in CLIS:
        if os.getenv(env) != "1":
            continue
        exe_path = shutil.which(exe)
        if exe_path is None:  # CLI 미설치 → 조용히 skip
            continue
        prompt = ("다음은 업무 비서 챗봇의 대화입니다. 비서의 답변을 2~3문장으로 쉽게 해설해 주세요.\n"
                  f"사용자: {mask_pii(user)}\n비서: {mask_pii(reply)}")
        out = _run(exe_path, build_args(prompt))
        if out:
            notes.append(f"💬 {label} 해설: {out}")
    return reply if not notes else reply + "\n\n" + "\n\n".join(notes)

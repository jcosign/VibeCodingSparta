"""test_app.py - Streamlit AppTest로 app.py를 실제로 돌려 보는 검증 스크립트.

실행(project/student 폴더에서): .venv/Scripts/python.exe ../../검증/test_app.py
가짜 claude 명령(fake_cli/claude.cmd)을 PATH 맨 앞에 두어 실제 외부 호출 없이 CLI 경로를 확인합니다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDENT = os.path.join(HERE, "..", "project", "student")
os.chdir(STUDENT)
sys.path.insert(0, STUDENT)

from streamlit.testing.v1 import AppTest  # noqa: E402


def run(question, k=None, env=None):
    for key in ("USE_CLAUDE_CLI", "USE_CODEX_CLI"):
        os.environ.pop(key, None)
    os.environ.update(env or {})
    at = AppTest.from_file(os.path.join(STUDENT, "app.py"), default_timeout=300)
    at.run()
    if k is not None:
        at.sidebar.slider[0].set_value(k).run()
    at.text_input(key="question").input(question).run()
    assert not at.exception, at.exception
    return at


def show(title, at):
    print(f"\n### {title}")
    for el in list(at.success) + list(at.warning) + list(at.info):
        print(f"  [{el.type}] {el.value[:150]!r}")
    print("  subheaders:", [s.value for s in at.subheader])
    if at.dataframe:
        df = at.dataframe[0].value
        print("  근거 표:", list(zip(df["출처(제목)"], df["유사도"])))


show("기본(k=2) 반품하고 싶어요", run("반품하고 싶어요"))
show("k=3 돈을 다시 돌려받고 싶어요", run("돈을 다시 돌려받고 싶어요", k=3))
show("답 없는 질문(주가)", run("우리 회사 주가 얼마예요?"))

fake = os.path.join(HERE, "fake_cli")
os.environ["PATH"] = fake + os.pathsep + os.environ["PATH"]
show("USE_CLAUDE_CLI=1 + 가짜 claude(숫자 지킴) + USE_CODEX_CLI=1(미설치)",
     run("반품하고 싶어요", env={"USE_CLAUDE_CLI": "1", "USE_CODEX_CLI": "1", "FAKE_MODE": "good"}))
show("USE_CLAUDE_CLI=1 + 가짜 claude(14일 지어냄)",
     run("반품하고 싶어요", env={"USE_CLAUDE_CLI": "1", "FAKE_MODE": "bad"}))
os.environ["PATH"] = os.environ["PATH"].replace(fake + os.pathsep, "")
print("\nEND OK")

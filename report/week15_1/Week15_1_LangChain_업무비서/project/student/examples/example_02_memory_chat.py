"""D3·D4: 도구 + 메모리 멀티턴 통합 예제.

실행: python examples/example_02_memory_chat.py   (project/student 폴더에서)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from agent import MemoryAgent  # noqa: E402
from llm import current_mode  # noqa: E402

agent = MemoryAgent()
print("모드:", current_mode())
for q in ["내 이름은 홍길동이야", "120 + 231 * 2 는?", "배송 얼마나 걸려?", "내 이름 뭐였지?"]:
    print(f"\n사용자: {q}\n비서: {agent.chat(q)}")

print("\n[메모리에 쌓인 기록]")
for h in agent.history:
    print(f"  {h['role']}: {h['content']}")
print("메모리 길이(turns):", len(agent.history))

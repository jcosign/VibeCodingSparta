"""검증용 가짜 claude CLI 출력. FAKE_MODE=bad 이면 근거에 없는 숫자(14일)를 지어낸 답을 냅니다."""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
if os.getenv("FAKE_MODE") == "bad":
    print("반품은 구매 후 14일 이내에 가능합니다. (출처: 반품정책)")
else:
    print("미개봉 상품은 구매 후 7일 이내라면 무료로 반품하실 수 있어요. (출처: 반품정책)")

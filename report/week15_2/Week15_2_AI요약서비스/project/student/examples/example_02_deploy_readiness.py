"""배포 준비 점검: 배포에 필요한 파일 6종이 다 있는지 + .env가 이미지에서 빠지는지."""
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FILES = ["app.py", "requirements.txt", "Dockerfile", "run.sh", ".dockerignore", ".env.example"]

ok = True
for f in FILES:
    exists = os.path.exists(os.path.join(BASE, f))
    ok = ok and exists
    print("[O]" if exists else "[X]", f)

ignore_path = os.path.join(BASE, ".dockerignore")
ignored = os.path.exists(ignore_path) and ".env" in open(ignore_path, encoding="utf-8").read().split()
print("[O]" if ignored else "[X]", ".dockerignore 에 .env 포함(키가 이미지에 안 실림)")
print("배포 준비 완료" if ok and ignored else "누락된 항목을 채우세요")

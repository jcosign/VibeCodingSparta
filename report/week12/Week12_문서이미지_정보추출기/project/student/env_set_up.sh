#!/usr/bin/env bash
# env_set_up.sh - 환경 자동 설정
#   1) 가상환경(.venv) 생성  2) requirements.txt 설치
#   3) Tesseract OCR 설치 여부 확인  4) OCR 검증(샘플 영수증을 실제로 읽어 봄)
# 모든 출력은 env_set_up.log 에도 함께 저장됩니다.
set -euo pipefail
cd "$(dirname "$0")"

LOG=env_set_up.log
exec > >(tee "$LOG") 2>&1

PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
echo "사용할 파이썬: $("$PY" --version 2>&1)"

echo "[1/4] 가상환경(.venv) 생성"
[ -d .venv ] || "$PY" -m venv .venv
# macOS/Linux는 .venv/bin, Windows(Git Bash)는 .venv/Scripts
if [ -f .venv/bin/activate ]; then source .venv/bin/activate; else source .venv/Scripts/activate; fi
python -m pip install --upgrade pip

echo "[2/4] requirements.txt 설치"
python -m pip install -r requirements.txt

echo "[3/4] Tesseract OCR 확인 (🧾 이미지 탭의 로컬 OCR에 필요)"
if command -v tesseract >/dev/null 2>&1; then
  echo "Tesseract 확인: $(tesseract --version 2>&1 | head -n 1)"
else
  echo "⚠️ PATH에서 tesseract를 찾지 못했습니다. 이미지 탭을 쓰려면 설치하세요."
  echo "   macOS: brew install tesseract / Ubuntu·Docker: apt-get install -y tesseract-ocr / Windows: winget install UB-Mannheim.TesseractOCR"
  echo "   (Windows는 기본 설치 경로 C:\\Program Files\\Tesseract-OCR 를 extract.py가 자동으로 찾습니다)"
  echo "   (📄 PDF 탭·🌐 HTML 탭은 Tesseract 없이도 동작합니다)"
fi

echo "[4/4] OCR 검증 (샘플 영수증 이미지 → OCR → JSON)"
python - <<'EOF'
import extract as ex
from sample_docs import make_sample_image
v = ex.tesseract_version()
if v is None:
    print("⚠️ OCR 검증 건너뜀: Tesseract를 찾지 못했습니다(위 3단계 안내대로 설치 후 다시 실행).")
else:
    text, meta = ex.image_extract(make_sample_image())
    obj = ex.safe_json(text)
    print("OCR 원문:", " | ".join(l for l in meta.get("ocr_text", "").splitlines() if l.strip()))
    print("구조화 JSON:", text.replace("\n", " "))
    print("검산:", ex.verify_receipt(obj))
    if obj.get("항목"):
        print(f"검증 성공: Tesseract {v} OCR로 샘플 영수증 {len(obj['항목'])}개 항목 인식")
    else:
        print("⚠️ OCR은 실행됐지만 항목을 찾지 못했습니다. OCR 원문을 확인하세요.")
EOF

echo ""
echo "다음 단계:"
echo "  source .venv/bin/activate   (Windows Git Bash: source .venv/Scripts/activate)"
echo "  streamlit run app.py"

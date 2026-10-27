# 컨테이너 배포용
FROM python:3.12-slim

# 로컬 OCR(pytesseract)은 Tesseract 프로그램이 있어야 동작합니다(컨테이너 안에도 반드시 설치)
# 한국어 영수증도 읽으려면 tesseract-ocr-kor 를 함께 설치하세요(extract.py가 kor를 자동 감지).
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py extract.py gemini_client.py cli_augment.py sample_docs.py sample_invoice.pdf ./
COPY examples ./examples

EXPOSE 8501
# Gemini를 쓰려면 실행 시 키를 넘기세요: docker run -e GEMINI_API_KEY=... (이미지에 키를 넣지 마세요)
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

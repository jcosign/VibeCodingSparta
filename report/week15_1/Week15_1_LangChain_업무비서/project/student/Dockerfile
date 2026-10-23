FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# 컨테이너는 CPU 전용 torch
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 모델은 첫 실행 때 내려받습니다. 캐시를 남기려면:
#   docker run -p 8501:8501 -v hf-cache:/root/.cache/huggingface week15-assistant
# API 키는 이미지에 넣지 말고 실행할 때 -e OPENAI_API_KEY=... 로 전달하세요.
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

# 컨테이너 배포용 - CPU 전용
FROM python:3.12-slim

# Whisper가 오디오 파일을 읽으려면 ffmpeg가 필요합니다(컨테이너 안에도 반드시 설치)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt

COPY app.py local_model.py cli_augment.py ./

EXPOSE 8501
# 모델(임베딩·리랭커·Whisper-tiny)은 컨테이너 안에서 처음 쓸 때 내려받습니다.
# E2B를 쓰려면 실행 시 키를 넘기세요: docker run -e E2B_API_KEY=... (이미지에 키를 넣지 마세요)
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

# 컨테이너 배포용 - CPU 전용
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt

COPY app.py local_model.py cli_augment.py ./

EXPOSE 8501
# 모델(ViT-Tiny, tiny-sd)은 컨테이너 안에서 처음 쓸 때 내려받습니다.
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

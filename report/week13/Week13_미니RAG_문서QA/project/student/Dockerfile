# 컨테이너 배포용
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# GPU가 없는 컨테이너이므로 CPU 전용 torch를 먼저 설치합니다(기본 torch 휠은 CUDA 포함이라 매우 큼)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py rag.py embed.py docs.py cli_augment.py ./
COPY examples ./examples

# 임베딩 모델을 빌드 시점에 미리 내려받아 이미지에 넣습니다(컨테이너 실행 때 다운로드 대기 없음)
RUN python -c "from embed import embed; print(len(embed('검증')))"

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

# 배포용 컨테이너 이미지 (Cloud Run 호환)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Cloud Run은 $PORT로 포트를 알려줍니다(기본 8080). Streamlit을 그 포트로 실행.
ENV PORT=8080
EXPOSE 8080
CMD streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true

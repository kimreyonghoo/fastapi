# 1. Python 슬림 이미지 사용
FROM python:3.10-slim

# 2. 작업 디렉토리
WORKDIR /app

# 3. 시스템 패키지 설치 (YOLO와 OpenCV용)
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 git curl \
    && rm -rf /var/lib/apt/lists/*

# 4. requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 전체 프로젝트 복사
COPY . .

# 6. 콘솔 로그 실시간 출력
ENV PYTHONUNBUFFERED=1

# 7. FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

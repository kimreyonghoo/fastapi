# 1. Python 베이스 이미지 사용 (버전은 프로젝트에 맞게)
FROM python:3.12-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 복사 및 설치
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 4. 전체 코드 복사
COPY . .

# 5. 환경 변수 설정 (콘솔 출력을 실시간으로 보기 위함)
ENV PYTHONUNBUFFERED=1

# 6. 서버 실행 (reload는 개발용 옵션)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

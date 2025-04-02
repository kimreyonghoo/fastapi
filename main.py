import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ .env 먼저 로드
from dotenv import load_dotenv
load_dotenv()

from router import s3_router
from internal.database import get_dynamodb
from internal.aws_config import aws_access
from internal import database
#from domain.domain import UserRepository
#from router.predict_router import router

# FastAPI 애플리케이션 생성
app = FastAPI()

db=get_dynamodb(aws_access) #user_repository= UserRepository(db 객체 자체 반환)

# ✅ CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (Flutter 앱이 접근 가능하도록)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 요청 헤더 허용
)

# 라우터 등록
app.include_router(s3_router.router, prefix="/s3", tags=["S3"])
app.include_router(database.router)

# app.include_router(router)


@app.get("/")
def read_root():
    return {"message": "Hello from new FastAPI environment!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

import os
from internal.database import get_dynamodb

# 환경 변수에서 AWS 자격증명 가져오기
access = {
    "region_ap": os.getenv("AWS_REGION", "ap-northeast-2"),
    "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
}

# DynamoDB 클라이언트 생성 테스트
try:
    db = get_dynamodb(access)
    print("✅ get_dynamodb() 실행 성공!")
    
    # DynamoDB 테이블 목록 가져오기 (연결 확인용)
    response = db.list_tables()
    print("📌 DynamoDB 테이블 목록:", response["TableNames"])
except Exception as e:
    print("❌ get_dynamodb() 실행 실패:", e)

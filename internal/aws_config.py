import boto3
import os
from dotenv import load_dotenv

# ✅ .env 파일 강제 로드
load_dotenv()

# ✅ AWS 환경 변수 가져오기
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")  # ⬅️ 여기서 `S3_BUCKET_NAME`이 로드되는지 확인!

#aws키의 딕셔너리 
aws_access = {
    'region_ap': AWS_REGION,
    'aws_access_key_id': AWS_ACCESS_KEY_ID,
    'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
}

# ✅ 환경 변수가 None이면 실행 중단
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME]):
    raise ValueError("🚨 AWS 환경 변수가 올바르게 설정되지 않았습니다! .env 파일을 확인하세요.")

# ✅ S3 클라이언트 생성
try:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    print("✅ S3 클라이언트 생성 성공!")
except Exception as e:
    raise RuntimeError(f"🚨 S3 클라이언트 생성 중 오류 발생: {str(e)}")

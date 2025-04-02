import boto3
import os
from internal.aws_config import s3_client, S3_BUCKET_NAME  # ✅ aws_config에서 S3_BUCKET_NAME 가져오기
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError
from internal.aws_config import aws_access

# .env 파일 로드
load_dotenv()

# S3 설정


# S3 클라이언트 생성
s3_client = boto3.client(
    "s3",
    region_name=aws_access['region_ap'],
    aws_access_key_id=aws_access['aws_access_key_id'],
    aws_secret_access_key=aws_access['aws_secret_access_key']
)
# ✅ S3 업로드 함수
def upload_file_to_s3(file_path: str, s3_key: str):
    try:
        if not file_path or not s3_key:
            raise ValueError("🚨 업로드할 파일 경로나 S3 키가 없습니다!")

        print(f"📂 업로드할 파일 경로: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"🚨 파일을 찾을 수 없습니다: {file_path}")

        # ✅ S3 업로드
        s3_client.upload_file(
            file_path,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ACL": "public-read"}
        )

        print("✅ S3 업로드 성공!")
        return {
            "message": "Upload Successful",
            "url": f"https://{S3_BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
        }

    except Exception as e:
        raise RuntimeError(f"🚨 업로드 실패: {str(e)}")


# ✅ S3 파일 삭제 함수
def delete_all_related_files(file_name: str):
    try:
        if not file_name:
            raise ValueError("🚨 삭제할 파일명이 없습니다!")

        base_name = file_name  # 예: 20240402_egg.jpg
        result_img_name = f"result_{file_name}"                # 결과 이미지
        result_json_name = f"result_{file_name}.json"          # 분석 JSON

        delete_targets = {
            "original": f"uploads/{base_name}",
            "result_image": f"results/{result_img_name}",
            "result_json": f"json_results/{result_json_name}"
        }

        deleted = []

        for label, key in delete_targets.items():
            print(f"🗑️ S3 삭제 요청: {key}")
            response = s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=key)

            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 204:
                print(f"✅ 삭제 완료: {label}")
                deleted.append(label)
            else:
                print(f"⚠️ 삭제 실패 또는 존재하지 않음: {key}")

        return {
            "message": "관련 파일 삭제 완료",
            "deleted": deleted
        }

    except Exception as e:
        raise RuntimeError(f"🚨 관련 파일 삭제 중 오류 발생: {str(e)}")

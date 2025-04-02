from fastapi import APIRouter, UploadFile, File, HTTPException
from s3_service import upload_file_to_s3, delete_all_related_files
from yolo.detect import run_detection
import os, json
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "temp"
RESULT_DIR = "results"
JSON_DIR = "json_results"

# ✅ 디렉토리 자동 생성
for d in [UPLOAD_DIR, RESULT_DIR, JSON_DIR]:
    os.makedirs(d, exist_ok=True)

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="🚨 파일이 없습니다.")

        # ✅ 타임스탬프 파일 이름 생성
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        result_img_path = os.path.join(RESULT_DIR, f"result_{filename}")
        result_json_path = os.path.join(JSON_DIR, f"result_{filename}.json")

        # ✅ 이미지 저장
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        print(f"📂 파일 저장 완료: {file_path}")

        # ✅ YOLO 분석
        detection_result = run_detection(
            img_path=file_path,
            save_path=result_img_path
        )

        # ✅ 분석 결과 JSON 저장
        with open(result_json_path, "w", encoding="utf-8") as f:
            json.dump(detection_result, f, ensure_ascii=False, indent=2)

        # ✅ S3 업로드 (원본, 결과 이미지, 결과 JSON)
        s3_original = upload_file_to_s3(file_path, f"uploads/{filename}")
        s3_result_img = upload_file_to_s3(result_img_path, f"results/result_{filename}")
        s3_result_json = upload_file_to_s3(result_json_path, f"json_results/result_{filename}.json")

        # ✅ 로컬 파일 정리
        os.remove(file_path)
        os.remove(result_img_path)
        os.remove(result_json_path)

        return {
            "message": "Complete",
            "yolo_result": detection_result,
            "s3": {
                "result_image_url": s3_result_img["url"],
                "result_json_url": s3_result_json["url"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 처리 중 오류 발생: {str(e)}")

@router.delete("/delete/")
async def delete_related(file_name: str):
    try:
        result = delete_all_related_files(file_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

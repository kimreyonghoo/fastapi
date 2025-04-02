from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from datetime import datetime
import shutil
import os
from yolo.detect import run_detection  # YOLO 추론 함수 가져오기

router = APIRouter()

UPLOAD_DIR = "uploads"
RESULT_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

@router.post("/predict/")
async def predict(file: UploadFile = File(...)):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    result_path = os.path.join(RESULT_DIR, f"result_{filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = run_detection(img_path=file_path, save_path=result_path)

    return JSONResponse(content={
        "result": result,
        "saved_image": result_path
        "saved_image": result_image_url
    })

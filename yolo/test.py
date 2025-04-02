"""from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
from detect import run_detection
from datetime import datetime

app = FastAPI()

UPLOAD_DIR = "uploads" # client가 업로드한 이미지 저장 폴더
RESULT_DIR = "results" # YOLO model이 추론한 결과에 박스가 그려진 이미지 저장 폴더
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    # 저장 경로 및 파일명
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    result_path = os.path.join(RESULT_DIR, f"result_{filename}")

    # 이미지 저장
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # YOLO 추론 수행
    result = run_detection(img_path=file_path, save_path=result_path)

    # 결과 리턴
    return JSONResponse(content={
        "result": result,
        "saved_image": result_path
    })
"""
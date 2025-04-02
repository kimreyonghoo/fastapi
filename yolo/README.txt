1. best.pt             - 학습된 YOLO11s 모델 가중치
2. detect.py           - YOLO 추론 기능이 포함된 파일
3. main.py             - FastAPI 서버 실행 및 추론 연동 코드
4. requirements.txt    - Python 패키지 설치 목록

패키지 설치

pip install -r requirements.txt

FastAPI 서버 실행

uvicorn main:app --reload

실행 확인

http://127.0.0.1:8000/docs 접속
-> /predict/ 엔드포인트에서 이미지 업로드로 테스트 가능

===========================
📤 API 설명 (POST /predict/)
===========================

요청:
- multipart/form-data 형식
- 필드명: file
- 업로드된 이미지가 YOLO 모델을 통해 인식됨

응답:
- JSON 형식
{
  "result": [
    {
      "label_kor": "삼겹살",
      "confidence": 0.8654
    },
    ...
  ],
  "saved_image": "results/result_20250401123059_test.png"
}

 폴더 설명

- uploads/ : 사용자가 업로드한 원본 이미지 저장
- results/ : 박스가 그려진 결과 이미지 저장

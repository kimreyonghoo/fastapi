from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# 요청 바디 스키마
class AnalyzeRequest(BaseModel):
    image_url: str

# 응답 스키마
class Nutrition(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float

class AnalyzeResponse(BaseModel):
    menu: str
    nutrition: Nutrition
    status: str

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(req: AnalyzeRequest):
    try:
        # 1. YOLO 모델 호출 → 메뉴명 추론
        # menu = run_yolo_and_get_menu(req.image_url)

        # 2. DB에서 영양 정보 조회
        # nutrition = get_nutrition_from_db(menu)

        # 3. [선택] 추천 기능 또는 분석 추가
        # recommended = get_supplement_recommendation(nutrition)

        # 4. 최종 응답
        return {
            "menu": menu,
            "nutrition": nutrition,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

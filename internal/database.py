from fastapi import APIRouter, HTTPException
from urllib.parse import unquote
import boto3
import boto3.resources
from internal.aws_config import aws_access
import botocore
import logging
from botocore.exceptions import ClientError
from fastapi import Body
from pydantic import BaseModel
from decimal import Decimal
from typing import Dict
from uuid import uuid4
from datetime import datetime

from internal.repository3 import recommend_suppl

def get_dynamodb(access:dict):
    dynamodb = boto3.client(
        'dynamodb',
        region_name=access['region_ap'],
        aws_access_key_id=access['aws_access_key_id'],
        aws_secret_access_key=access['aws_secret_access_key']
    )
    print('get DynamoDB')
    return dynamodb

def get_table(table_name:str, access:dict):
    db_resource = boto3.resource(
        'dynamodb',
        region_name = access['region_ap'],
        aws_access_key_id=access['aws_access_key_id'],
        aws_secret_access_key=access['aws_secret_access_key']
    )
    print('get DynamoDB resource')
    try:
        table = db_resource.Table(table_name)
        print(f'get {table.table_name} Table')
        return table
    except botocore.exceptions.ClientError as e:
        logging.error(e)
        print(f'no {table_name} table')
        return None

db=get_dynamodb(aws_access)

def get_name(tablename, name: str) -> dict:
        response = get_table(tablename,aws_access).get_item(
            Key={
                'PK': f'{unquote(name)}'
            }
        )
        item = response.get('Item', {})
        return {
            'nutrients': item.get('nutrients', {}),
            'qty': item.get('qty', 0)
        }
    
router = APIRouter()

@router.get("/database/{tablename}:{name}")#음식 정보 가져오기 tablename:food_data
async def get_database_nutrients(tablename: str, name: str):
    try:
        nutrients = get_name(tablename, name)
        return nutrients
    except HTTPException as http_err:
        # 🔹 이미 발생한 HTTPException은 그대로 반환
        raise http_err

# 영양정보(날짜) flutter -> dynamodb에 저장
class NutritionSaveRequest(BaseModel):
    user_id: str 
    date: str  # 예: "2025-05-01"
    nutrients: list[float]

@router.post("/database/{tablename}/save")
async def save_nutrient_data(
    tablename: str,
    data: NutritionSaveRequest = Body(...)
):
    try:
        table = get_table(tablename, aws_access)
        if not table:
            raise HTTPException(status_code=404, detail="테이블을 찾을 수 없습니다.")

        # float → Decimal로 변환
        nutrition_decimal = [Decimal(str(v)) for v in data.nutrition]

        item = {
            'PK': data.user_id,           # 예: "junho"
            'SK': f'meal#{data.date}',              # 예: "2025-05-06"
            'nutrition': nutrition_decimal
        }

        table.put_item(Item=item)
        return {"message": "✅ 저장 성공", "item": item}

    except Exception as e:
        logging.error(f"DynamoDB 저장 실패: {e}")
        raise HTTPException(status_code=500, detail="DynamoDB 저장 중 오류 발생")

# 영양정보 삭제
class NutritionDeleteRequest(BaseModel):
    user_id: str
    date: str


@router.post("/database/{tablename}/delete")
async def delete_nutrient_data(
    tablename: str,
    data: NutritionDeleteRequest = Body(...)
):
    try:
        table = get_table(tablename, aws_access)
        if not table:
            raise HTTPException(status_code=404, detail="테이블을 찾을 수 없습니다.")

        key = {
            'PK': data.user_id,
            'SK': f'meal#{data.date}'
        }

        response = table.get_item(Key=key)
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="삭제할 식단 데이터를 찾을 수 없습니다.")

        table.delete_item(Key=key)
        return {"message": "✅ 삭제 성공", "user_id": data.user_id, "date": data.date}

    except Exception as e:
        logging.error(f"DynamoDB 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="DynamoDB 삭제 중 오류 발생")
    
@router.get("/supplements/recommend/{userid}")#영양제 추천
async def recommend_supplements(userid: str):
    result = recommend_suppl(userid)
    return result

class userProfileData(BaseModel):
    gender:str
    age: str
    height: str
    weight: str
    act_level: str


@router.post("/database/user/profile")
async def save_user_profile(userid:str,
    user: userProfileData = Body(...)):

    #유저 프로필 수정정
    table = get_table('user',aws_access)
    # 저장
    response = table.put_item(
        Item={
            'PK': f'{userid}',  # 파티션 키
            'SK':'profile',
            **dict(user)
        }
    )
    return response

@router.post("/database/user/register")
async def register_user_profile(userid:str,
    user: userProfileData = Body(...)):
    try:
        #유저 프로필 수정정
        table = get_table('user',aws_access)
        # 저장
        response = table.put_item(
            Item={
            'PK': f'{userid}',  # 파티션 키
            'SK':'profile',
            **dict(user)
            },
            ConditionExpression='attribute_not_exists(userid)'  # 조건: userid가 존재하지 않아야 저장
        )
        return {"status": "success", "message": "User registered successfully."}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # 프론트엔드에서 알 수 있도록 409 Conflict와 커스텀 메시지 전달
            raise HTTPException(status_code=409, detail="UserID already exists.")
        else:
            raise HTTPException(status_code=500, detail="Unexpected error occurred.")
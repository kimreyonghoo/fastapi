
from decimal import ROUND_HALF_UP, Decimal
import json
from fastapi import APIRouter, HTTPException
from urllib.parse import unquote
import boto3
import boto3.resources
import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from internal.aws_config import aws_access
from internal.database import get_table
import botocore
import logging
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta, timezone
#영양소 목록
nutr_db=['에너지', '탄수화물', '식이섬유', '단백질', '리놀레산', '알파-리놀렌산', 'EPA+DHA', 
      '메티오닌', '류신', '이소류신', '발린', '라이신', '페닐알라닌+티로신', '트레오닌', '트립토판', '히스티딘', 
      '비타민A', '비타민D', '비타민E', '비타민K', '비타민C', '비타민B1', '비타민B2', '나 이아신', '비타민B6', 
      '비타민B12', '엽산', '판토텐산', '비오틴', '칼슘', '인', '나트륨', '염소', '칼륨', '마그네슘', '철', 
      '아연', '구리', '망간', '요 오드', '셀레늄', '몰리브덴', '크롬']


def get_rdi_pk(age):#프론트 구현 x
    #db에서 권장영양섭취량을 계산하기 위한 키
    if age in range(15,19):
        return '15-18'
    elif age in range(19,30):
        return '19-29'
    elif age in range(30,50):
        return '30-49'
    elif age in range(50,65):
        return '50-64'
    elif age in range(65,75):
        return '65-74'
    elif age >=75:
        return '75-'
    else:
        return None

def get_rdi(PK,SK):#프론트 구현 x
    table = get_table("rdi", aws_access)

    response = table.get_item(
        Key={
            'PK': PK,
            'SK': SK
        }
    )
    item = response.get('Item') 
    nutrition = [float(n) for n in item['nutrition']]
    return nutrition

def convert_types(data):#프론트 구현 x
    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = convert_types(v)
        return data
    elif isinstance(data, list):
        return [convert_types(i) for i in data]
    else:
        try:
            return Decimal(str(data)).quantize(Decimal('.1'), rounding=ROUND_HALF_UP)
        except:
            return data
    
def put_user_profile(user_id, user_profile_data:dict): #유저 프로필 수정정
    table = get_table('user',aws_access)
    # 저장
    response = table.put_item(
        Item={
            'PK': f'{user_id}',  # 파티션 키
            'SK':'profile#',
            **user_profile_data
        }
    )
    return response
def get_user_profile():#유저 프로필 가져오기기
    table = get_table('user',aws_access)
    response = table.query(
        KeyConditionExpression='PK = :user_id AND SK = :profile',
        ExpressionAttributeValues={
            ':user_id': 'krh6818@naver.com',
            ':profile': 'profile#'
        }
    )
    return response['Items'][0]

def put_user_meal(user_id, date,user_meal_data:dict):#영양정보 넣기 @post, '2025-05-11'형식
    table = get_table('user',aws_access)
    user_meal_data['nutrition']=convert_types(user_meal_data['nutrition'])
    # 저장
    response = table.put_item(
        Item={
            'PK': f'{user_id}',  # 파티션 키
            'SK': f'meal#{date}',
            **user_meal_data
        }
    )
    return response    

def get_user_meal(date):#영양정보 가져오기
    table = get_table('user',aws_access)
    response = table.query(
        KeyConditionExpression='PK = :user_id AND SK = :meal#',
        ExpressionAttributeValues={
            ':user_id': 'krh6818@naver.com',
            ':profile': f'meal#{date}'
        }
    )
    return response['Items'][0]

def del_user_meal(date):  # 영양정보 삭제
    table = get_table('user', aws_access)

    response = table.delete_item(
        Key= {
            'PK': 'krh6818@naver.com',  
            'SK': f'meal#{date}'       
        }
    )

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)
    
def calculate_bmr(user: dict):#user['profile'], 프론트 구현 x
    """
user_profile = {

    'sex': 'male',
    'age': '16',
    'physique': {
        'height': '176',
        'weight': '75',
        'act_level': '1.5'# 일상적 생활만 한다-1.2 가벼운 운동을 주 1-3회-1.5 주 3-5 일 운동을 한다(헬스) -1.725 강도높은 운동이나 육체노동- 1.9 
    },
}   
meal_data = {
    'nutrition': [2700.0, 130000.0, 30000.0]
}
    """
    # BMR 계산 
    if user['sex'] == 'male':
        bmr = 10 * user['pysique']['weight'] + 6.25 * user['pysique']['height'] - 5 * user['age'] + 5
    else:
        bmr = 10 * user['pysique']['weight'] + 6.25 * user['pysique']['height'] - 5 * user['age'] - 161

    # TDEE 계산 
    activity_level = user.get('pysique', {}).get('act_level', 1.2)  # 기본값: 1.2 (정적 생활)
    tdee = bmr * activity_level

    rdi_key = get_rdi_pk(user['age']) 
    recommended_rdi = get_rdi(user['sex'], rdi_key) 
    rdi_calories = recommended_rdi[0]
    calorie_ratio = tdee / rdi_calories
    
    recommended_rdi = [
        int(tdee) if i == 0 else int(value * calorie_ratio)
        for i, value in enumerate(recommended_rdi)
]
    #nutr_db의 순서와 동일,0번이 칼로리
    return recommended_rdi

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj
    
def recom_suppl(userid):
    KST = timezone(timedelta(hours=9))
    today= datetime.now(KST).date()
    start_date = today - timedelta(days=6)

    table=get_table("user",aws_access)
    response = table.query(
        KeyConditionExpression='PK = :pk AND SK BETWEEN :start AND :end',
        ExpressionAttributeValues={
            ':pk': f'{userid}',
            ':start': f"meal#{start_date.isoformat()}",
            ':end': f"meal#{today.isoformat()}"
        }
    )
    for item in response["Items"]:  
        if "nutrients" in item:
            item["nutrients"] = convert_decimals(item["nutrients"])
            
    print(response["Items"])
   

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj
    
def recom_suppl(userid):
    KST = timezone(timedelta(hours=9))
    today= datetime.now(KST).date()
    start_date = today - timedelta(days=6)

    table=get_table("user",aws_access)
    response = table.query(
        KeyConditionExpression='PK = :pk AND SK BETWEEN :start AND :end',
        ExpressionAttributeValues={
            ':pk': f'{userid}',
            ':start': f"meal#{start_date.isoformat()}",
            ':end': f"meal#{today.isoformat()}"
        }
    )
    for item in response["Items"]:  
        if "nutrients" in item:
            item["nutrients"] = convert_decimals(item["nutrients"])
            
    print(response["Items"])
   
    
user_profile = {

    'sex': 'male',
    'age': '16',
    'physique': {
        'height': '176',
        'weight': '75',
        'act_level': '1.5'# 일상적 생활만 한다-1.2 가벼운 운동을 주 1-3회-1.5 주 3-5 일 운동을 한다(헬스) -1.725 강도높은 운동이나 육체노동- 1.9 
    },
}  
put_user_profile("test@naver.com",user_profile)
recom_suppl("krh6818")
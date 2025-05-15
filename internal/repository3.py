
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
def get_user_profile(userid):#유저 프로필 가져오기기
    table = get_table('user',aws_access)
    response = table.query(
        KeyConditionExpression='PK = :user_id AND SK = :profile',
        ExpressionAttributeValues={
            ':user_id': f'{userid}',
            ':profile': 'profile'
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

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)
    
def cal_deficiency(userid):#user['profile'], 프론트 구현 x
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
    user=get_user_profile(userid)

    weight = float(user['physique']['weight'])  # 몸무게
    height = float(user['physique']['height'])  # 키
    age = int(user['age'])                      # 나이
    act_level=float(user['physique']['act_level'])
    if user['sex'] == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # TDEE 계산 
    tdee = bmr * act_level

    rdi_key = get_rdi_pk(age) 
    recommended_rdi = get_rdi(user['sex'], rdi_key) 
    rdi_calories = recommended_rdi[0]
    calorie_ratio = tdee / rdi_calories
    
    recommended_rdi = [
        int(tdee) if i == 0 else int(value * calorie_ratio)
        for i, value in enumerate(recommended_rdi)
    ]
    
    
    total_nutrition = [0.0] * len(nutr_db)
    count = 0
    
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
        if "nutrition" in item:
            item["nutrition"] = convert_decimals(item["nutrition"])
            
    for item in response['Items']:
        if 'nutrition' in item:
            nut = convert_decimals(item['nutrition'])
            total_nutrition = [a + b for a, b in zip(total_nutrition, nut)]
            count += 1
    avg_nutrition = [x / count for x in total_nutrition] if count else [0.0] * len(nutr_db)
    
    #nutr_db의 순서와 동일,0번이 칼로리
    deficiency = [max(r - a, 0.0) for r, a in zip(recommended_rdi, avg_nutrition)]
    return deficiency#최종 결핍수치(평균값)
 
def recommend_suppl(userid):
    categories = ["vitamin", "iron", "magnesium", "calcium"]
    result = {}

    # 사용자 부족량 벡터 계산
    deficiency_vector = cal_deficiency(userid)

    for cat in categories:
        table = get_table(cat, aws_access)
        items = table.scan()['Items']
        ranked = []

        for item in items:
            if 'nutrition' in item:
                nutrition_vector=convert_decimals(item['nutrition'])
                item['nutrition']=nutrition_vector
                product_vector = np.array(nutrition_vector)
                similarity = cosine_similarity([deficiency_vector], [product_vector])[0][0]
                ranked.append((item, similarity))

        # 유사도 기준으로 정렬 후 상위 5개
        top_items = sorted(ranked, key=lambda x: x[1], reverse=True)[:5]

        # category key: category#{cat} 형식으로 저장
        result[f"category#{cat}"] = [item for item, _ in top_items]

    return ranked






    
    

    
    

from decimal import Decimal
from fastapi import APIRouter, HTTPException
from urllib.parse import unquote
import boto3
import boto3.resources
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from internal.aws_config import aws_access
from internal.database import get_table
import botocore
import logging

test_user={
        'PK':'userA',
        'create_at':'2025-05-11',
        'sex':'male',
        'age':'16',
        'physique':{
            'height':'176',
            'weight':'75',
            'act_level':'1.5'
            },
        'nutrition':[2700.0, 130000.0, 30000.0, 65000.0, 14000.0, 1700.0, 230.0, 1400.0, 3200.0, 1400.0, 1800.0,
                     2900.0, 2600.0, 1500.0, 400.0, 900.0, 0.9, 0.0, 12.0, 0.1, 100.0, 1.3, 1.5, 15.0, 1.5, 0.0, 0.4, 5.0, 
                     0.0, 900.0, 1200.0, 1500.0, 2300.0, 3500.0, 410.0, 14.0, 10.0, 0.9, 4.0, 0.1, 0.1, 0.0, 0.0]
    }

#영양소 목록
nutr_db=['에너지', '탄수화물', '식이섬유', '단백질', '리놀레산', '알파-리놀렌산', 'EPA+DHA', 
      '메티오닌', '류신', '이소류신', '발린', '라이신', '페닐알라닌+티로신', '트레오닌', '트립토판', '히스티딘', 
      '비타민A', '비타민D', '비타민E', '비타민K', '비타민C', '비타민B1', '비타민B2', '나 이아신', '비타민B6', 
      '비타민B12', '엽산', '판토텐산', '비오틴', '칼슘', '인', '나트륨', '염소', '칼륨', '마그네슘', '철', 
      '아연', '구리', '망간', '요 오드', '셀레늄', '몰리브덴', '크롬']


def get_rdi_pk(age):
    #db에서 권장영양섭취량을 계산하기 위한 키키
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

def get_rdi(PK,SK):
    table = get_table("rdi", aws_access)

    response = table.get_item(
        Key={
            'PK': PK,
            'SK': SK
        }
    )
    item = response.get('Item')  
    item = response.get('Item')
    nutrition = [float(n) for n in item['nutrition']]
    print(nutrition) 

def convert_to_decimal(data):
    if isinstance(data, list):
        return [convert_to_decimal(item) for item in data]
    elif isinstance(data, dict):
        return {k: convert_to_decimal(v) for k, v in data.items()}
    elif isinstance(data, float):
        return Decimal(str(data))
    else:
        return data
    
def put_user(table_name, user_id, user_data):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    # Decimal 변환
    user_data['nutrition'] = convert_to_decimal(user_data['nutrition'])

    # 저장
    response = table.put_item(
        Item={
            'user_id': user_id,  # 파티션 키
            **user_data
        }
    )
    return response


def calculate_bmr(user: dict):
    """
    user={
        'PK':'',
        'sex':'',
        'age':'',
        'physique':{
            'height':'',
            'weight':'',
            'act_level':''
            },
        'meal':[
            {
                'created_at':'',
                'nutrition':[]
            }
        ]
        
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
    rdi_calories = recommended_rdi.get('calories')
    calorie_ratio = tdee / rdi_calories
    
    recommended_rdi = [value * calorie_ratio if i != 0 else tdee for i, value in enumerate(recommended_rdi)]
    #nutr_db의 순서와 동일,0번이 칼로리
    return recommended_rdi

  
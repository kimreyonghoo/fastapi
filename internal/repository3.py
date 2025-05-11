
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



#영양소 목록
nutr_db=['에너지', '탄수화물', '식이섬유', '단백질', '리놀레산', '알파-리놀렌산', 'EPA+DHA', 
      '메티오닌', '류신', '이소류신', '발린', '라이신', '페닐알라닌+티로신', '트레오닌', '트립토판', '히스티딘', 
      '비타민A', '비타민D', '비타민E', '비타민K', '비타민C', '비타민B1', '비타민B2', '나 이아신', '비타민B6', 
      '비타민B12', '엽산', '판토텐산', '비오틴', '칼슘', '인', '나트륨', '염소', '칼륨', '마그네슘', '철', 
      '아연', '구리', '망간', '요 오드', '셀레늄', '몰리브덴', '크롬']


def update_user_nutrition(user_id, new_physique, table_name='user'):
    """
    DynamoDB user 테이블의 physique와 nutr_db 항목을 업데이트
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    try:
        response = table.update_item(
            Key={
                'user_id': user_id
            },
            UpdateExpression="SET physique = :p, meal.nutr_db = :n",
            ExpressionAttributeValues={
                ':p': new_physique,
            },
            ReturnValues="UPDATED_NEW"
        )
        print("업데이트 완료:", response['Attributes'])
        return response['Attributes']
    except Exception as e:
        print("오류 발생:", e)
        return None
user=get_table("user",aws_access)

def get_rdi_pk(age):
    #db에서 권장영양섭취량을 계산하기 위한 키키
    if age in range(15,19):
        return '#15-18'
    elif age in range(19,30):
        return '#19-29'
    elif age in range(30,50):
        return '#30-49'
    elif age in range(50,65):
        return '#50-64'
    elif age in range(65,75):
        return '#65-74'
    elif age >=75:
        return '#75-'
    else:
        return None

def calculate_bmr(sex: str, weight: float, height: float, age: int, user: dict):
    """
    :param sex: 'male' or 'female'
    :param weight: kg
    :param height: cm
    :param age: 나이
    :param user: {'physique': {'activity_level': float}} 형태의 dict
    :return: (rdi_key, tdee)
    """
    
    # BMR 계산 
    if sex.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # TDEE 계산 
    activity_level = user.get('physique', {}).get('activity_level', 1.2)  # 기본값: 1.2 (정적 생활)
    tdee = bmr * activity_level

    rdi_key = get_rdi_pk(age)
    rdi=get_table("rdi",aws_access)
    return tdee

  
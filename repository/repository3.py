
from fastapi import APIRouter, HTTPException
from urllib.parse import unquote
import boto3
import boto3.resources
from internal.aws_config import aws_access
import botocore
import logging
from internal.database import get_table
#영양소 목록
nutr_db=['에너지', '탄수화물', '식이섬유', '단백질', '리놀레산', '알파-리놀렌산', 'EPA+DHA', 
      '메티오닌', '류신', '이소류신', '발린', '라이신', '페닐알라닌+티로신', '트레오닌', '트립토판', '히스티딘', 
      '비타민A', '비타민D', '비타민E', '비타민K', '비타민C', '비타민B1', '비타민B2', '나 이아신', '비타민B6', 
      '비타민B12', '엽산', '판토텐산', '비오틴', '칼슘', '인', '나트륨', '염소', '칼륨', '마그네슘', '철', 
      '아연', '구리', '망간', '요 오드', '셀레늄', '몰리브덴', '크롬']


def update_user_nutrition(user_id, new_physique, new_nutr_vector, table_name='user'):
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
                ':n': new_nutr_vector
            },
            ReturnValues="UPDATED_NEW"
        )
        print("업데이트 완료:", response['Attributes'])
        return response['Attributes']
    except Exception as e:
        print("오류 발생:", e)
        return None
user=get_table("user",aws_access)
def calculate_bmr(sex, weight, height, age,user:dict):
      #기초대사량 계산
      bmr=0
      if sex.lower() == 'male':
            bmr=10 * weight + 6.25 * height - 5 * age + 5
      else:
            bmr=10 * weight + 6.25 * height - 5 * age - 161
      tdee=bmr*user.pysique.actyvity_level

  
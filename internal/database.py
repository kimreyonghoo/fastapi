from fastapi import APIRouter, HTTPException
from urllib.parse import unquote
import boto3
import boto3.resources
from internal.aws_config import aws_access
import botocore
import logging
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

@router.get("/database/{tablename}:{name}")
async def get_database_nutrients(tablename: str, name: str):
    try:
        nutrients = get_name(tablename, name)
        return nutrients
    except HTTPException as http_err:
        # 🔹 이미 발생한 HTTPException은 그대로 반환
        raise http_err
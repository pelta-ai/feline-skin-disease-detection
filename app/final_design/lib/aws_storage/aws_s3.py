import os
import boto3
from datetime import date
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import lib.aws_storage.aws_s3_constants as constants

s3_client = constants.S3_CLIENT_ACCOUNT

def list_object_paths(bucket=constants.BUCKET, prefix=None):
    paginator = s3_client.get_paginator('list_objects_v2')

    paths = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if not key.endswith('/'):  # skip folders
                paths.append(key)

    return paths

def folder_exists(file_path, bucket=constants.BUCKET):
    if not file_path.endswith('/'):
        file_path += '/'

    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=file_path, MaxKeys=1)
    return 'Contents' in response

def create_user_folder(user_id):
    _create_folder_helper(user_id)

def create_today_folder(user_id):
    _create_folder_helper(user_id + '/' + _get_today_date() + '/images/')
    _create_folder_helper(user_id + '/' + _get_today_date() + '/diagnosis/')

def add_file(file_name, file_path, user_id, bucket=constants.BUCKET):
    if not folder_exists(user_id + '/' + _get_today_date()):
        create_today_folder(user_id)

    destination_path = ''
    if file_name.endswith('.txt'):
        destination_path = user_id + '/' + _get_today_date() + '/diagnosis/' + file_name
    else: 
        destination_path = user_id + '/' + _get_today_date() + '/images/' + file_name

    try:
        s3_client.upload_file(
            Filename=file_path,
            Bucket=bucket,
            Key=destination_path
        )
        print(f"Successfully added file '{file_name}' in '{destination_path}'")
    except Exception as e:
        print(f"Error adding file '{file_name}' in '{destination_path}': {e}")

def get_file_url(file_path, expire_time=3600, bucket=constants.BUCKET):
    try: 
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': file_path},
            ExpiresIn=expire_time
    )
    except Exception as e:
        print(f"Error creating file url of '{file_path}': {e}")

def _create_folder_helper(folder_path, bucket=constants.BUCKET):
    if not folder_path.endswith('/'):
        folder_path += '/'

    try:
        s3_client.put_object(Bucket=bucket, Key=folder_path)
        print(f"Folder '{folder_path}' created successfully in bucket '{bucket}'")
    except Exception as e:
        print(f"Error creating folder '{folder_path}': {e}")

def _get_today_date():
    today = date.today()
    formatted = today.strftime("%B%d%Y").lower()
    
    return formatted

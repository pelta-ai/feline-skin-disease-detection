import boto3

BUCKET = 'felineskindiseasedetectionbucket'
S3_CLIENT_ACCOUNT = boto3.client('s3')
S3_CLIENT_EMULATOR = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

bucket = os.getenv('S3_BUCKET_NAME')
prefix = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/frontend/src/'

files_to_check = [
    'main.jsx',
    'index.html',
    'App.jsx'
]

for filename in files_to_check:
    key = prefix + filename if not filename.startswith('index') else prefix.replace('/src/', '/') + filename
    
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
        content = resp['Body'].read().decode('utf-8')
        
        print(f"\n{'='*60}")
        print(f"=== {filename} ===")
        print(f"{'='*60}\n")
        print(content[:1500])
        
    except Exception as e:
        print(f"\n❌ Could not read {filename}: {e}")

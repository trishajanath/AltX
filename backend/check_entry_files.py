import boto3
import os
from dotenv import load_dotenv

load_dotenv()

from backend.s3_storage import s3_client as s3

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

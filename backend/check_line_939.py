import boto3
import os
from dotenv import load_dotenv

load_dotenv()

from backend.s3_storage import s3_client as s3

key = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/frontend/src/App.jsx'
bucket = os.getenv('S3_BUCKET_NAME')

resp = s3.get_object(Bucket=bucket, Key=key)
content = resp['Body'].read().decode('utf-8')
lines = content.split('\n')

print(f"Total lines: {len(lines)}")
print(f"\nLine 939 and nearby:\n")
for i in range(935, 945):
    if i < len(lines):
        print(f"Line {i+1}: {lines[i]}")

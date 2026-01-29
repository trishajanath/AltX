import boto3
import os
from dotenv import load_dotenv

load_dotenv()

from backend.s3_storage import s3_client as s3

bucket = os.getenv('S3_BUCKET_NAME')

# Check the Button.jsx file (which exports Button, Input, Card, etc.)
key = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/frontend/src/components/ui/Button.jsx'

try:
    resp = s3.get_object(Bucket=bucket, Key=key)
    content = resp['Body'].read().decode('utf-8')
    
    print(f"=== Button.jsx Contents ===\n")
    print(content[:2000])  # First 2000 chars
    
    print(f"\n\n=== Checking for CommonJS ===")
    if 'exports' in content.lower():
        print("⚠️ Found 'exports'")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'exports' in line.lower():
                print(f"Line {i}: {line}")
    else:
        print("✅ No exports found")
        
except Exception as e:
    print(f"Error: {e}")

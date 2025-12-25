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
prefix = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/'

# List all files in the project
response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

print(f"Checking all JS/JSX files for CommonJS syntax...\n")

for obj in response.get('Contents', []):
    key = obj['Key']
    if key.endswith(('.js', '.jsx')):
        try:
            resp = s3.get_object(Bucket=bucket, Key=key)
            content = resp['Body'].read().decode('utf-8')
            
            if 'exports' in content.lower() or 'require(' in content:
                print(f"\n🔍 Found in: {key}")
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'exports' in line.lower() or 'require(' in line:
                        print(f"  Line {i}: {line.strip()}")
        except Exception as e:
            print(f"Error reading {key}: {e}")

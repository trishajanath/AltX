import boto3, os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

bucket = os.getenv("S3_BUCKET_NAME")
key = "projects/6917910c004fca6f164755e6/web-ecommerce-busy-557776/frontend/src/App.jsx"

obj = s3.get_object(Bucket=bucket, Key=key)
content = obj["Body"].read().decode("utf-8")
lines = content.split('\n')

print("Lines 50-65 (UI COMPONENTS section):")
print("=" * 80)
for i in range(49, min(65, len(lines))):
    marker = "🔴" if i in [52, 53, 54, 55] else "  "
    print(f"{marker} {i+1:3d}: {lines[i]}")

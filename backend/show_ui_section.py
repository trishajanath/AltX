import boto3
import os

load_dotenv()


from backend.s3_storage import s3_client as s3
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

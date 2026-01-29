import boto3
import os

load_dotenv()


from backend.s3_storage import s3_client as s3
key = "projects/6917910c004fca6f164755e6/web-ecommerce-busy-557776/frontend/src/App.jsx"
bucket = os.getenv("S3_BUCKET_NAME")

obj = s3.get_object(Bucket=bucket, Key=key)
content = obj["Body"].read().decode("utf-8")

print("Lines 50-60 (where duplicate Button is):")
print("=" * 80)
for i, line in enumerate(content.split('\n')[49:60], 50):
    marker = "🔴" if i == 53 else "  "
    print(f"{marker} {i:3d}: {line}")

print("\n" + "=" * 80)
print("✅ SOLUTION: This project needs to import Button from './components/ui/Button'")
print("❌ CURRENT: It declares 'const Button =' inline (duplicate with ui/Button.jsx)")

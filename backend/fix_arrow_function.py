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

print("📥 Downloading App.jsx from S3...")
obj = s3.get_object(Bucket=bucket, Key=key)
content = obj["Body"].read().decode("utf-8")

print("🔍 Fixing arrow function syntax error on line 1342...")

# Fix the syntax error: () = /> should be () =>
fixed_content = content.replace('onChange={() = />', 'onChange={() =>')

if fixed_content != content:
    print("✅ Found and fixed the syntax error!")
    print("   Changed: onChange={() = /> to onChange={() =>")
else:
    print("⚠️  Pattern not found, trying alternative fix...")
    # Try to find and fix any malformed arrow functions
    import re
    fixed_content = re.sub(r'\(\)\s*=\s*/>', '() =>', content)
    if fixed_content != content:
        print("✅ Fixed using regex pattern")

# Upload fixed content
print(f"\n📤 Uploading fixed App.jsx to S3...")
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=fixed_content.encode('utf-8'),
    ContentType='text/javascript'
)

print(f"✅ Successfully uploaded fixed App.jsx ({len(fixed_content)} bytes)")
print("\n🎉 DONE! Arrow function syntax fixed.")
print("🔄 Refresh your browser to see the changes.")

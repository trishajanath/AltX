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

lines = content.split('\n')

print(f"📊 Current line count: {len(lines)}")
print("\n🔍 Looking for orphaned code around line 941...")

# Show context around the error
for i in range(935, min(950, len(lines))):
    marker = "🔴" if i == 940 else "  "
    print(f"{marker} {i+1:3d}: {lines[i]}")

# Find and remove the orphaned return statement and surrounding orphan code
# Looking for the pattern where there's a return outside function
cleaned_lines = []
skip_next = False

for i, line in enumerate(lines):
    # Skip lines that are orphaned from removed component
    if i >= 938 and i <= 942:  # Lines 939-943 (0-indexed: 938-942)
        stripped = line.strip()
        if (stripped == '' or 
            stripped.startswith('return <Wrapper') or 
            stripped == '};' or
            stripped == '//'):
            print(f"🗑️  Removing orphaned line {i+1}: {line[:60]}")
            continue
    
    cleaned_lines.append(line)

fixed_content = '\n'.join(cleaned_lines)

print(f"\n📊 Line count: {len(lines)} → {len(cleaned_lines)}")

# Upload fixed content
print(f"\n📤 Uploading fixed App.jsx to S3...")
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=fixed_content.encode('utf-8'),
    ContentType='text/javascript'
)

print(f"✅ Successfully uploaded fixed App.jsx ({len(fixed_content)} bytes)")
print("\n🎉 DONE! Orphaned code removed.")
print("🔄 Refresh your browser to see the changes.")

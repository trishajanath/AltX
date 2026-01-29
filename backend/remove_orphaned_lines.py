import boto3, os
from dotenv import load_dotenv

load_dotenv()

from backend.s3_storage import s3_client as s3

bucket = os.getenv("S3_BUCKET_NAME")
key = "projects/6917910c004fca6f164755e6/web-ecommerce-busy-557776/frontend/src/App.jsx"

print("📥 Downloading App.jsx from S3...")
obj = s3.get_object(Bucket=bucket, Key=key)
content = obj["Body"].read().decode("utf-8")

lines = content.split('\n')
print(f"📊 Current lines: {len(lines)}")

# Remove lines 53-57 (0-indexed: 52-56)
# Line 53: // 💅 UI COMPONENTS
# Line 54: (empty)
# Line 55: (empty)  
# Line 56:     return <Wrapper className={className}>{text}</Wrapper>;
# Line 57: };

print("\n🗑️  Removing orphaned code (lines 53-57):")
for i in range(52, 57):
    if i < len(lines):
        print(f"   Line {i+1}: {lines[i][:70]}")

# Remove the lines
del lines[52:57]  # This removes indices 52-56 (lines 53-57)

fixed_content = '\n'.join(lines)

print(f"\n📊 Line count: {len(content.split(chr(10)))} → {len(lines)}")

# Upload fixed content
print(f"\n📤 Uploading fixed App.jsx to S3...")
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=fixed_content.encode('utf-8'),
    ContentType='text/javascript'
)

print(f"✅ Successfully uploaded ({len(fixed_content)} bytes)")

# Verify the fix
print("\n✅ Verification - Lines 50-60 after fix:")
new_lines = fixed_content.split('\n')
for i in range(49, min(60, len(new_lines))):
    print(f"   {i+1:3d}: {new_lines[i][:70]}")

print("\n🎉 DONE! Orphaned code removed.")
print("🔄 Refresh your browser to see the changes.")

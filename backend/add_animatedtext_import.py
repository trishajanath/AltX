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

print("🔍 Current imports (first 5 lines):")
for i in range(min(5, len(lines))):
    print(f"   {i+1}: {lines[i]}")

# Find the line with Button import
import_line_idx = None
for i, line in enumerate(lines[:10]):
    if "import { Button, Input, Card }" in line and "./components/ui/Button" in line:
        import_line_idx = i
        print(f"\n✅ Found Button import at line {i+1}")
        break

if import_line_idx is not None:
    # Add AnimatedText import after Button import
    lines.insert(import_line_idx + 1, "import { AnimatedText } from './components/ui/AnimatedText';")
    print(f"✅ Added AnimatedText import at line {import_line_idx + 2}")
else:
    print("⚠️  Button import not found, adding both imports at line 2")
    lines.insert(1, "import { Button, Input, Card } from './components/ui/Button';")
    lines.insert(2, "import { AnimatedText } from './components/ui/AnimatedText';")

fixed_content = '\n'.join(lines)

print(f"\n📊 Line count: {len(content.split(chr(10)))} → {len(lines)}")

# Upload
print(f"\n📤 Uploading fixed App.jsx to S3...")
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=fixed_content.encode('utf-8'),
    ContentType='text/javascript'
)

print(f"✅ Successfully uploaded ({len(fixed_content)} bytes)")

# Verify
print("\n✅ Verification - First 5 lines:")
new_lines = fixed_content.split('\n')
for i in range(min(5, len(new_lines))):
    print(f"   {i+1}: {new_lines[i]}")

print("\n🎉 DONE! AnimatedText import added.")
print("🔄 Refresh your browser to see the changes.")

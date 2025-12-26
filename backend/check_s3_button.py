import boto3, os, re
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

key = "projects/6917910c004fca6f164755e6/web-ecommerce-busy-557776/frontend/src/App.jsx"
bucket = os.getenv("S3_BUCKET_NAME")

print(f"📥 Downloading App.jsx from S3...")
obj = s3.get_object(Bucket=bucket, Key=key)
content = obj["Body"].read().decode("utf-8")

print(f"✅ Downloaded {len(content)} bytes")
print(f"📊 Total lines: {len(content.split(chr(10)))}")

# Find Button declarations
button_pattern = r'const\s+Button\s*='
matches = list(re.finditer(button_pattern, content))

print(f"\n🔍 Found {len(matches)} 'const Button =' declarations")

if matches:
    lines = content.split('\n')
    for i, match in enumerate(matches):
        # Find line number
        line_num = content[:match.start()].count('\n') + 1
        print(f"\n❌ Declaration #{i+1} at line {line_num}:")
        print(f"   {lines[line_num-1][:100]}")

# Check imports
import_button_pattern = r'import\s+\{[^}]*Button[^}]*\}\s+from'
import_matches = list(re.finditer(import_button_pattern, content))

print(f"\n✅ Found {len(import_matches)} Button import statements")
if import_matches:
    lines = content.split('\n')
    for i, match in enumerate(import_matches):
        line_num = content[:match.start()].count('\n') + 1
        print(f"   Line {line_num}: {lines[line_num-1].strip()}")

# Show first 30 lines
print("\n📄 First 30 lines of App.jsx:")
print("=" * 80)
for i, line in enumerate(content.split('\n')[:30], 1):
    print(f"{i:3d}: {line}")

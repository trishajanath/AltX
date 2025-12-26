import boto3, os, re
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
print(f"✅ Downloaded {len(content)} bytes")

# Split into lines for easier manipulation
lines = content.split('\n')

print("\n🔍 Analyzing file structure...")

# Find the Button declaration and remove it
button_start = None
button_end = None
brace_count = 0
in_button = False

for i, line in enumerate(lines):
    if re.match(r'^\s*const\s+Button\s*=', line):
        button_start = i
        in_button = True
        brace_count = line.count('{') - line.count('}')
        print(f"🔴 Found Button declaration at line {i+1}")
        continue
    
    if in_button:
        brace_count += line.count('{') - line.count('}')
        if brace_count <= 0 and ';' in line:
            button_end = i
            print(f"🔴 Button declaration ends at line {i+1}")
            break

if button_start is None:
    print("❌ No Button declaration found!")
    exit(1)

# Remove the Button declaration
print(f"\n🗑️  Removing lines {button_start+1} to {button_end+1} ({button_end - button_start + 1} lines)")
del lines[button_start:button_end+1]

# Check if import already exists
has_button_import = False
import_line_idx = None
for i, line in enumerate(lines[:50]):  # Check first 50 lines
    if "import" in line and "from 'react'" in line:
        import_line_idx = i
    if "Button" in line and "import" in line and "./components/ui/" in line:
        has_button_import = True
        break

# Add import after React import if not present
if not has_button_import:
    if import_line_idx is not None:
        # Add after React import
        insert_at = import_line_idx + 1
        lines.insert(insert_at, "import { Button, Input, Card } from './components/ui/Button';")
        print(f"✅ Added Button import at line {insert_at+1}")
    else:
        # Add at beginning
        lines.insert(0, "import { Button, Input, Card } from './components/ui/Button';")
        print(f"✅ Added Button import at line 1")
else:
    print("✅ Button import already exists")

# Rejoin content
fixed_content = '\n'.join(lines)

# Verify no duplicate Button declarations remain
button_matches = list(re.finditer(r'const\s+Button\s*=', fixed_content))
if button_matches:
    print(f"\n⚠️  WARNING: Still found {len(button_matches)} Button declarations!")
    for match in button_matches:
        line_num = fixed_content[:match.start()].count('\n') + 1
        print(f"   Line {line_num}")
else:
    print("\n✅ No Button declarations found in fixed content")

# Verify import exists
if "import" in fixed_content and "Button" in fixed_content and "./components/ui/" in fixed_content:
    print("✅ Button import verified")
else:
    print("⚠️  WARNING: Button import may be missing!")

# Upload fixed content back to S3
print(f"\n📤 Uploading fixed App.jsx to S3...")
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=fixed_content.encode('utf-8'),
    ContentType='text/javascript'
)

print(f"✅ Successfully uploaded fixed App.jsx ({len(fixed_content)} bytes)")
print(f"📊 Line count: {len(content.split(chr(10)))} → {len(fixed_content.split(chr(10)))}")
print("\n🎉 DONE! The duplicate Button declaration has been removed.")
print("🔄 Refresh your browser to see the changes.")

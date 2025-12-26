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

print("🔍 Searching for AnimatedText usage...")

# Find all AnimatedText usages
matches = list(re.finditer(r'<AnimatedText[^>]*>', content))
print(f"Found {len(matches)} AnimatedText usages")

if matches:
    for i, match in enumerate(matches):
        line_num = content[:match.start()].count('\n') + 1
        print(f"  Usage {i+1} at line {line_num}")
        # Get context
        start = max(0, match.start() - 100)
        end = min(len(content), match.end() + 100)
        context = content[start:end]
        print(f"    Context: ...{context}...")

# Option 1: Replace AnimatedText with a simple h1
print("\n🔧 Replacing AnimatedText with simple h1 tags...")

# Replace <AnimatedText el="h1" text="..." className="..."/> with <h1 className="...">...</h1>
def replace_animated_text(match):
    # Extract attributes
    full_match = match.group(0)
    text_match = re.search(r'text="([^"]*)"', full_match)
    class_match = re.search(r'className="([^"]*)"', full_match)
    
    text = text_match.group(1) if text_match else ""
    class_name = class_match.group(1) if class_match else ""
    
    return f'<h1 className="{class_name}">{text}</h1>'

fixed_content = re.sub(
    r'<AnimatedText[^>]*/>',
    replace_animated_text,
    content
)

# Remove AnimatedText import
fixed_content = re.sub(
    r"import \{ AnimatedText \} from './components/ui/AnimatedText';\n",
    "",
    fixed_content
)

print(f"\n✅ Replaced {len(matches)} AnimatedText components with h1 tags")
print(f"✅ Removed AnimatedText import")

# Upload
print(f"\n📤 Uploading fixed App.jsx to S3...")
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=fixed_content.encode('utf-8'),
    ContentType='text/javascript'
)

print(f"✅ Successfully uploaded ({len(fixed_content)} bytes)")
print("\n🎉 DONE! AnimatedText replaced with simple h1 elements.")
print("🔄 Hard refresh your browser (Ctrl+Shift+R) to clear cache.")

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

from backend.s3_storage import s3_client as s3

bucket = os.getenv('S3_BUCKET_NAME')
prefix = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/'

# List all files
response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

print(f"🔍 Deep search for 'exports' in all project files...\n")

found_any = False

for obj in response.get('Contents', []):
    key = obj['Key']
    if key.endswith(('.js', '.jsx', '.ts', '.tsx', '.html', '.json')):
        try:
            resp = s3.get_object(Bucket=bucket, Key=key)
            content = resp['Body'].read().decode('utf-8')
            
            # Search for exports (case-sensitive)
            if 'exports' in content:
                found_any = True
                print(f"\n📄 {key.split('/')[-1]}")
                print(f"   Full path: {key}")
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'exports' in line:
                        print(f"   Line {i}: {line.strip()}")
        except Exception as e:
            pass

if not found_any:
    print("✅ No 'exports' found in any file")
    print("\n🔍 Let me check for other CommonJS patterns...")
    
    # Check for module.exports, require, __dirname, etc.
    commonjs_patterns = ['module.exports', 'require(', '__dirname', '__filename', 'process.env']
    
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(('.js', '.jsx')):
            try:
                resp = s3.get_object(Bucket=bucket, Key=key)
                content = resp['Body'].read().decode('utf-8')
                
                for pattern in commonjs_patterns:
                    if pattern in content:
                        print(f"\n📄 {key.split('/')[-1]} contains '{pattern}'")
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if pattern in line:
                                print(f"   Line {i}: {line.strip()}")
            except Exception as e:
                pass

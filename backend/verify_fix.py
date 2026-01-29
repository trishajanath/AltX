import boto3
import os
from dotenv import load_dotenv

load_dotenv()

from backend.s3_storage import s3_client as s3

bucket = os.getenv('S3_BUCKET_NAME')
key = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/frontend/src/App.jsx'

# Download current version
resp = s3.get_object(Bucket=bucket, Key=key)
content = resp['Body'].read().decode('utf-8')

print("=== First 5 lines of current App.jsx in S3 ===\n")
lines = content.split('\n')
for i, line in enumerate(lines[:5], 1):
    print(f"Line {i}: {line}")

print(f"\n=== Checking for syntax errors ===")
if "import React, from" in content:
    print("❌ ERROR: Still has 'import React, from' syntax error!")
elif "import React from 'react'" in content:
    print("✅ GOOD: Correct import syntax")
else:
    print("⚠️ WARNING: No React import found")

print(f"\n=== Checking ALL files for 'exports' ===")
prefix = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/'
response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

found_exports = []
for obj in response.get('Contents', []):
    file_key = obj['Key']
    if file_key.endswith(('.js', '.jsx', '.ts', '.tsx', '.json', '.html')):
        try:
            resp = s3.get_object(Bucket=bucket, Key=file_key)
            file_content = resp['Body'].read().decode('utf-8')
            
            # Check for CommonJS patterns
            if any(pattern in file_content for pattern in ['exports.', 'module.exports', 'require(', '__dirname', '__filename']):
                found_exports.append({
                    'file': file_key.split('/')[-1],
                    'path': file_key
                })
        except:
            pass

if found_exports:
    print("\n⚠️ Found CommonJS patterns in:")
    for item in found_exports:
        print(f"   - {item['file']}")
else:
    print("\n✅ No CommonJS patterns found in any file")

print("\n=== Checking package.json for type module ===")
pkg_key = prefix + 'frontend/package.json'
try:
    resp = s3.get_object(Bucket=bucket, Key=pkg_key)
    pkg_content = resp['Body'].read().decode('utf-8')
    import json
    pkg_json = json.loads(pkg_content)
    
    if pkg_json.get('type') == 'commonjs':
        print("❌ ERROR: package.json has 'type': 'commonjs'")
    elif pkg_json.get('type') == 'module':
        print("✅ GOOD: package.json has 'type': 'module'")
    else:
        print("ℹ️  INFO: No 'type' field in package.json (defaults to commonjs for Node, but Vite uses ESM)")
except Exception as e:
    print(f"⚠️ Could not check package.json: {e}")

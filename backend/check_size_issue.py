"""List project files and check for size-related issues"""
from s3_storage import s3_client, S3_BUCKET_NAME

prefix = 'projects/6917910c004fca6f164755e6/e-commerce-selling-groceries-736975/'
response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)

print('Files in project:')
for obj in response.get('Contents', []):
    key = obj['Key'].replace(prefix, '')
    print(f'  {key}')

# Now check each component file for 'size' issues
print("\n=== Checking components for 'size' issues ===")
component_files = [
    'frontend/src/components/ui/Loading.jsx',
    'frontend/src/components/ui/Input.jsx',
    'frontend/src/components/ui/Card.jsx',
    'frontend/src/components/ui/AnimatedText.jsx',
    'frontend/src/components/ui/Navigation.jsx',
]

for file_path in component_files:
    key = prefix + file_path
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        content = response['Body'].read().decode('utf-8')
        
        if 'sizes[size]' in content or '.size' in content:
            print(f"\n⚠️ {file_path} has potential 'size' issue:")
            # Find the problematic line
            for i, line in enumerate(content.split('\n'), 1):
                if 'sizes[size]' in line or (']' in line and '.size' in line):
                    print(f"   Line {i}: {line.strip()[:80]}")
        else:
            print(f"✅ {file_path} - no size issues")
    except Exception as e:
        print(f"❌ Could not check {file_path}: {e}")

"""Check and fix the CSS file for double brace issues"""
from s3_storage import s3_client, S3_BUCKET_NAME

project_id = '6917910c004fca6f164755e6'
project_name = 'e-commerce-selling-groceries-736975'
key = f'projects/{project_id}/{project_name}/frontend/src/index.css'

print(f"📥 Fetching index.css from S3...")
response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
content = response['Body'].read().decode('utf-8')

print(f'Original size: {len(content)} chars')

# Check for double braces issue
double_open = content.count('{{')
double_close = content.count('}}')
if double_open > 0 or double_close > 0:
    print(f'❌ FOUND DOUBLE BRACES IN CSS - This breaks styling!')
    print(f'   {{ count: {double_open}')
    print(f'   }} count: {double_close}')
    
    # Fix by replacing double braces with single
    fixed = content.replace('{{', '{').replace('}}', '}')
    
    print(f'\n✅ Fixed CSS - uploading to S3...')
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=fixed.encode('utf-8'), ContentType='text/css')
    print('✅ Uploaded fixed index.css to S3!')
else:
    print('✅ No double braces found in CSS')

# Also check and show the first part
print('\n=== CSS PREVIEW (first 500 chars) ===')
print(content[:500])

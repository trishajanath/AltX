from s3_storage import s3_client, S3_BUCKET_NAME

# List all files in the project
prefix = 'projects/6917910c004fca6f164755e6/web-grocery-working-864606/'
response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)

print("=== FILES IN PROJECT ===")
for obj in response.get('Contents', []):
    print(obj['Key'].replace(prefix, ''))

# Check Button.jsx content
button_key = prefix + 'frontend/src/components/ui/Button.jsx'
try:
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=button_key)
    content = response['Body'].read().decode('utf-8')
    print("\n=== Button.jsx Content ===")
    print(content[:2000])
except Exception as e:
    print(f"Error getting Button.jsx: {e}")

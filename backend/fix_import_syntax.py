import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

bucket = os.getenv('S3_BUCKET_NAME')
key = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/frontend/src/App.jsx'

# Download the file
resp = s3.get_object(Bucket=bucket, Key=key)
content = resp['Body'].read().decode('utf-8')

print("Original line 1:")
print(content.split('\n')[0])

# Fix the syntax error: "import React, from 'react';" -> "import React from 'react';"
fixed_content = content.replace("import React, from 'react';", "import React from 'react';")

# Upload the fixed file
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=fixed_content.encode('utf-8'),
    ContentType='application/javascript'
)

print("\nFixed line 1:")
print(fixed_content.split('\n')[0])
print(f"\n✅ Fixed {key}")

# AWS S3 Setup Guide - Quick Start

## Prerequisites
- AWS account with S3 access
- Python 3.8+ with boto3 installed
- AltX backend configured

## Step 1: Install Dependencies (Already Done!)
```bash
cd backend
pip install boto3 python-multipart python-dotenv
```

## Step 2: Create AWS S3 Bucket

### Option A: AWS Console
1. Go to [AWS S3 Console](https://s3.console.aws.amazon.com/)
2. Click "Create bucket"
3. Bucket name: `altx-projects` (must be globally unique)
4. Region: `us-east-1` (or your preferred region)
5. Block all public access: **Enabled** (keep private)
6. Versioning: **Optional** (recommended for backup)
7. Click "Create bucket"

### Option B: AWS CLI
```bash
aws s3 mb s3://altx-projects --region us-east-1
```

## Step 3: Configure CORS Policy

### Via AWS Console
1. Go to your bucket → Permissions → CORS
2. Add this policy:
```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedOrigins": [
      "http://localhost:5173",
      "http://localhost:8000",
      "https://your-production-domain.com"
    ],
    "ExposeHeaders": ["ETag", "Content-Type"]
  }
]
```

### Via AWS CLI
```bash
aws s3api put-bucket-cors --bucket altx-projects --cors-configuration file://cors-policy.json
```

## Step 4: Create IAM User (Recommended)

### 1. Create IAM User
```bash
aws iam create-user --user-name altx-s3-uploader
```

### 2. Create Access Key
```bash
aws iam create-access-key --user-name altx-s3-uploader
```
**Save the output!** You'll need `AccessKeyId` and `SecretAccessKey`.

### 3. Attach S3 Policy
Create `altx-s3-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::altx-projects",
        "arn:aws:s3:::altx-projects/*"
      ]
    }
  ]
}
```

Attach policy:
```bash
aws iam put-user-policy --user-name altx-s3-uploader \
  --policy-name AltXS3Access \
  --policy-document file://altx-s3-policy.json
```

## Step 5: Configure Environment Variables

### 1. Copy Example File
```bash
cd backend
cp .env.example .env
```

### 2. Edit `.env` File
```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIA1234567890EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=altx-projects

# Google Gemini AI (required for project generation)
GOOGLE_API_KEY=your_actual_gemini_key_here

# GitHub (optional, for repo scanning)
GITHUB_TOKEN=your_github_token_here
```

### 3. Verify Configuration
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('AWS Key ID:', os.getenv('AWS_ACCESS_KEY_ID')[:10] + '...')
print('S3 Bucket:', os.getenv('S3_BUCKET_NAME'))
print('Region:', os.getenv('AWS_REGION'))
"
```

## Step 6: Test S3 Integration

### Test 1: Upload Test File
```bash
python
>>> from s3_storage import upload_project_to_s3
>>> test_files = [{'path': 'test.txt', 'content': 'Hello S3!'}]
>>> result = upload_project_to_s3('test-project', test_files, 'anonymous')
>>> print(result)
{'success': True, 'files_uploaded': 1, 'project_slug': 'test-project'}
```

### Test 2: List Projects
```bash
python
>>> from s3_storage import list_user_projects
>>> projects = list_user_projects('anonymous')
>>> print(projects)
['test-project']
```

### Test 3: Download Project
```bash
python
>>> from s3_storage import get_project_from_s3
>>> project = get_project_from_s3('test-project', 'anonymous')
>>> print(project['files'][0])
{'path': 'test.txt', 'content': 'Hello S3!'}
```

### Test 4: Full API Test
```bash
# Start backend
uvicorn main:app --reload

# In another terminal, test API
curl -X POST http://localhost:8000/api/projects/save \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test API Project",
    "slug": "test-api-project",
    "user_id": "anonymous",
    "files": [
      {"path": "index.html", "content": "<h1>Test</h1>"}
    ]
  }'

# List projects
curl http://localhost:8000/api/projects?user_id=anonymous
```

## Step 7: Verify S3 Bucket Contents

### Via AWS Console
1. Go to S3 Console
2. Open `altx-projects` bucket
3. Navigate to `projects/anonymous/`
4. You should see your test projects

### Via AWS CLI
```bash
# List all projects
aws s3 ls s3://altx-projects/projects/anonymous/

# Download a project to verify
aws s3 cp s3://altx-projects/projects/anonymous/test-project/ ./test-download/ --recursive
```

## Step 8: Generate First Real Project

1. **Start Backend:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Create Project via UI:**
   - Open http://localhost:5173
   - Use voice/text to request: "Create a portfolio website"
   - Wait for generation to complete
   - Check terminal logs for "✅ Uploaded N files to S3"

4. **Verify in S3:**
   ```bash
   aws s3 ls s3://altx-projects/projects/anonymous/ --recursive
   ```

## Troubleshooting

### Error: "NoCredentialsError: Unable to locate credentials"
**Solution:** Check `.env` file exists and has correct AWS keys
```bash
cat backend/.env | grep AWS_ACCESS_KEY_ID
```

### Error: "NoSuchBucket: The specified bucket does not exist"
**Solution:** Verify bucket name matches `.env` setting
```bash
aws s3 ls | grep altx-projects
```

### Error: "AccessDenied: Access Denied"
**Solutions:**
1. Check IAM policy allows S3 operations
2. Verify bucket policy doesn't block access
3. Ensure AWS keys belong to correct account

### Error: "botocore.exceptions.ClientError: An error occurred (403) when calling PutObject"
**Solution:** Add `s3:PutObject` permission to IAM policy

### Files Upload but Don't Show in Frontend
**Solution:** Check `/api/project-history` endpoint in browser DevTools
```javascript
// Check response
fetch('http://localhost:8000/api/project-history?user_id=anonymous')
  .then(r => r.json())
  .then(console.log)
```

## Security Best Practices

### ✅ Implemented
- Private S3 bucket (no public access)
- IAM user with least-privilege policy
- User-based key partitioning
- CORS policy restricts origins

### 🔲 TODO for Production
- [ ] Enable S3 bucket encryption (AES-256)
- [ ] Add JWT authentication to identify users
- [ ] Implement rate limiting (10 uploads/min per user)
- [ ] Add file size validation (max 10MB per file)
- [ ] Enable S3 versioning for rollback
- [ ] Set up CloudWatch alarms for errors
- [ ] Use AWS Secrets Manager for credentials

## Cost Estimation

### S3 Pricing (us-east-1)
- Storage: $0.023/GB/month
- PUT requests: $0.005/1000 requests
- GET requests: $0.0004/1000 requests

### Example Usage (100 projects)
- Storage: 100 projects × 5MB avg = 500MB = **$0.01/month**
- Uploads: 100 projects × 20 files = 2000 PUTs = **$0.01/month**
- Downloads: 1000 views × 20 files = 20k GETs = **$0.008/month**

**Total:** ~$0.03/month for light usage

### Cost Optimization
1. Enable S3 Intelligent-Tiering for older projects
2. Set lifecycle policy to delete projects after 90 days
3. Use CloudFront CDN to reduce GET requests
4. Compress files before upload (gzip)

## Next Steps

1. **Add Authentication** - Replace `user_id='anonymous'` with real user IDs
2. **Database Integration** - Store project metadata in PostgreSQL
3. **CDN Setup** - Add CloudFront for faster downloads
4. **Monitoring** - Set up CloudWatch dashboards
5. **Backup Strategy** - Enable S3 versioning + lifecycle rules

## Support

- AWS S3 Documentation: https://docs.aws.amazon.com/s3/
- Boto3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- FastAPI Documentation: https://fastapi.tiangolo.com/

---

**Setup Status: ✅ Ready to Use**

Your AltX backend is now configured to automatically upload projects to S3!

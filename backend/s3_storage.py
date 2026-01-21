import boto3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Cache to remember which user_id works for each project (avoids repeated lookups)
# Format: {"project_slug": "working_user_id"}
_project_user_cache: Dict[str, str] = {}

def get_cached_user_id_for_project(project_slug: str) -> Optional[str]:
    """Get the cached user_id that works for this project"""
    return _project_user_cache.get(project_slug)

def cache_user_id_for_project(project_slug: str, user_id: str):
    """Cache the user_id that works for this project"""
    _project_user_cache[project_slug] = user_id
    # Keep cache from growing too large (max 1000 entries)
    if len(_project_user_cache) > 1000:
        # Remove oldest entries (simple approach: clear half)
        keys_to_remove = list(_project_user_cache.keys())[:500]
        for key in keys_to_remove:
            del _project_user_cache[key]

def upload_project_to_s3(project_slug: str, files: List[Dict[str, str]], user_id: str = 'anonymous') -> Dict:
    """
    Upload project files to S3
    
    Args:
        project_slug: Unique project identifier
        files: List of file objects with 'path' and 'content' keys
        user_id: User identifier for organization
        
    Returns:
        Dict with upload status and file URLs
    """
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
    
    uploaded_files = []
    
    try:
        for file in files:
            file_path = file.get('path', '')
            file_content = file.get('content', '')
            
            # Create S3 key with user organization
            s3_key = f"projects/{user_id}/{project_slug}/{file_path}"
            
            # Upload file to S3
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_content.encode('utf-8'),
                ContentType=get_content_type(file_path),
                Metadata={
                    'project_slug': project_slug,
                    'user_id': user_id,
                    'upload_time': datetime.utcnow().isoformat()
                }
            )
            
            uploaded_files.append({
                'path': file_path,
                's3_key': s3_key,
                'size': len(file_content)
            })
        
        return {
            'success': True,
            'project_slug': project_slug,
            'files_uploaded': len(uploaded_files),
            'files': uploaded_files
        }
        
    except ClientError as e:
        raise Exception(f"S3 upload failed: {str(e)}")


def get_content_type(file_path: str) -> str:
    """Determine content type based on file extension"""
    extension = file_path.split('.')[-1].lower()
    
    content_types = {
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'json': 'application/json',
        'jsx': 'application/javascript',
        'tsx': 'application/javascript',
        'ts': 'application/javascript',
        'py': 'text/x-python',
        'md': 'text/markdown',
        'txt': 'text/plain',
    }
    
    return content_types.get(extension, 'application/octet-stream')


def get_project_from_s3(project_slug: str, user_id: str = 'anonymous') -> Optional[Dict]:
    """
    Retrieve project files from S3
    
    Args:
        project_slug: Unique project identifier
        user_id: User identifier
        
    Returns:
        Dict with project files or None if not found
    """
    if not S3_BUCKET_NAME:
        print("❌ S3_BUCKET_NAME environment variable is not set")
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
    
    try:
        prefix = f"projects/{user_id}/{project_slug}/"
        # Only log first attempt or cache miss to reduce spam
        
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return None
        
        print(f"✅ Found {len(response['Contents'])} files in S3 for {project_slug}")
        
        # Cache this user_id since it works
        cache_user_id_for_project(project_slug, user_id)
        
        files = []
        metadata = {}
        project_name = None
        
        for obj in response['Contents']:
            # Get file content
            file_obj = s3_client.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=obj['Key']
            )
            content = file_obj['Body'].read().decode('utf-8')
            
            # Extract relative path
            relative_path = obj['Key'].replace(prefix, '')
            
            # Check if this is the metadata file
            if relative_path == 'project_metadata.json':
                try:
                    metadata = json.loads(content)
                    project_name = metadata.get('name', project_slug)
                except:
                    pass
            
            files.append({
                'path': relative_path,
                'content': content,
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat()
            })
        
        return {
            'project_slug': project_slug,
            'name': project_name or project_slug.replace('-', ' ').title(),
            'files': files,
            'metadata': metadata
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        print(f"❌ S3 ClientError ({error_code}): {error_message}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error retrieving project from S3: {type(e).__name__}: {str(e)}")
        return None


def list_user_projects(user_id: str = 'anonymous') -> List[Dict]:
    """
    List all projects for a user
    
    Args:
        user_id: User identifier
        
    Returns:
        List of project metadata
    """
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
    
    try:
        prefix = f"projects/{user_id}/"
        
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=prefix,
            Delimiter='/'
        )
        
        projects = []
        if 'CommonPrefixes' in response:
            for prefix_obj in response['CommonPrefixes']:
                # Extract project slug from prefix
                project_slug = prefix_obj['Prefix'].rstrip('/').split('/')[-1]
                projects.append({
                    'slug': project_slug,
                    'prefix': prefix_obj['Prefix']
                })
        
        return projects
        
    except ClientError as e:
        print(f"Error listing projects: {str(e)}")
        return []


def delete_project_from_s3(project_slug: str, user_id: str = 'anonymous') -> bool:
    """
    Delete all files for a project from S3
    
    Args:
        project_slug: Unique project identifier
        user_id: User identifier
        
    Returns:
        True if successful, False otherwise
    """
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
    
    try:
        prefix = f"projects/{user_id}/{project_slug}/"
        
        # List all objects
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return False
        
        # Delete all objects
        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
        
        s3_client.delete_objects(
            Bucket=S3_BUCKET_NAME,
            Delete={'Objects': objects_to_delete}
        )
        
        return True
        
    except ClientError as e:
        print(f"Error deleting project: {str(e)}")
        return False


def find_project_user_id(project_slug: str) -> Optional[str]:
    """
    Find the user_id for a project by searching across all users.
    This is used when we don't know which user owns the project.
    
    Args:
        project_slug: Unique project identifier
        
    Returns:
        user_id if found, None otherwise
    """
    if not S3_BUCKET_NAME:
        return None
    
    try:
        # List all objects under projects/ prefix to find the project
        paginator = s3_client.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix='projects/', Delimiter='/'):
            # Each CommonPrefix is a user folder like projects/user123/
            for prefix_obj in page.get('CommonPrefixes', []):
                user_prefix = prefix_obj['Prefix']  # e.g., "projects/user123/"
                user_id = user_prefix.split('/')[1]  # Extract user_id
                
                # Check if this user has the project
                project_prefix = f"{user_prefix}{project_slug}/"
                response = s3_client.list_objects_v2(
                    Bucket=S3_BUCKET_NAME,
                    Prefix=project_prefix,
                    MaxKeys=1  # We only need to check if it exists
                )
                
                if 'Contents' in response:
                    print(f"🔍 Found project '{project_slug}' under user '{user_id}'")
                    cache_user_id_for_project(project_slug, user_id)
                    return user_id
        
        return None
        
    except Exception as e:
        print(f"Error searching for project: {str(e)}")
        return None

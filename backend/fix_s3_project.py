"""
Fix S3 Project Files - Remove duplicate declarations and other errors
Run this script to fix a specific project stored in S3
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from s3_storage import s3_client, S3_BUCKET_NAME, get_project_from_s3, upload_project_to_s3
from code_validator import auto_fix_jsx_for_sandbox, validate_generated_code

def fix_project_in_s3(project_slug: str, user_id: str):
    """
    Fetch a project from S3, fix all JSX files, and re-upload them
    """
    print(f"\n{'='*60}")
    print(f"🔧 Fixing project: {project_slug}")
    print(f"👤 User ID: {user_id}")
    print(f"{'='*60}\n")
    
    # 1. Fetch project from S3
    print("📥 Fetching project from S3...")
    project_data = get_project_from_s3(project_slug, user_id)
    
    if not project_data or not project_data.get('files'):
        print(f"❌ Project not found in S3: {project_slug}")
        return False
    
    print(f"✅ Found {len(project_data['files'])} files")
    
    # 2. Process each JSX file
    fixed_files = []
    files_fixed_count = 0
    
    for file_data in project_data['files']:
        file_path = file_data['path']
        content = file_data['content']
        
        # Check if it's a JSX file
        if file_path.endswith('.jsx') or file_path.endswith('.js'):
            print(f"\n🔍 Checking: {file_path}")
            
            # Get filename for the fix function
            filename = file_path.split('/')[-1]
            
            # Apply sandbox fixes (includes duplicate removal)
            original_content = content
            fixed_content = auto_fix_jsx_for_sandbox(content, filename)
            
            # Check if content changed
            if fixed_content != original_content:
                print(f"   ✅ Fixed issues in {filename}")
                files_fixed_count += 1
                content = fixed_content
            else:
                print(f"   ✓ No issues in {filename}")
            
            # Validate the fixed code
            validation = validate_generated_code(fixed_content, 'jsx', filename)
            if not validation.is_valid:
                print(f"   ⚠️ Remaining validation issues:")
                for error in validation.errors[:3]:
                    print(f"      - {error}")
        
        fixed_files.append({
            'path': file_path,
            'content': content
        })
    
    # 3. Re-upload fixed files to S3
    if files_fixed_count > 0:
        print(f"\n📤 Uploading {files_fixed_count} fixed files to S3...")
        
        # Upload files individually to preserve existing files
        for file_data in fixed_files:
            file_path = file_data['path']
            content = file_data['content']
            
            # Only re-upload JSX/JS files that were processed
            if file_path.endswith('.jsx') or file_path.endswith('.js'):
                s3_key = f"projects/{user_id}/{project_slug}/{file_path}"
                
                try:
                    s3_client.put_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=s3_key,
                        Body=content.encode('utf-8'),
                        ContentType='application/javascript'
                    )
                    print(f"   ✅ Uploaded: {file_path}")
                except Exception as e:
                    print(f"   ❌ Failed to upload {file_path}: {e}")
        
        print(f"\n🎉 Successfully fixed {files_fixed_count} files in {project_slug}")
    else:
        print(f"\n✅ No fixes needed for {project_slug}")
    
    return True


def list_recent_projects(user_id: str, limit: int = 10):
    """List recent projects for a user"""
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
                project_name = prefix_obj['Prefix'].split('/')[-2]
                projects.append(project_name)
        
        return projects[:limit]
    except Exception as e:
        print(f"Error listing projects: {e}")
        return []


if __name__ == "__main__":
    # Default project to fix
    project_slug = "web-ecommerce-busy-328145"
    user_id = "6917910c004fca6f164755e6"  # MongoDB _id from the logs
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        project_slug = sys.argv[1]
    if len(sys.argv) > 2:
        user_id = sys.argv[2]
    
    # Show available projects
    print("📋 Recent projects for this user:")
    projects = list_recent_projects(user_id)
    for p in projects:
        print(f"   - {p}")
    
    # Fix the specified project
    fix_project_in_s3(project_slug, user_id)

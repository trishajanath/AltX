import boto3
import re
import boto3
import os

load_dotenv()


from backend.s3_storage import s3_client as s3
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def remove_duplicate_components(content, components):
    """Remove duplicate component declarations from the content."""
    lines = content.split('\n')
    removed_components = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line declares a duplicate component
        for comp in components:
            if (f'const {comp} = ' in line or 
                f'function {comp}(' in line or 
                f'const {comp} = React.forwardRef' in line):
                
                print(f"🔍 Found duplicate {comp} at line {i+1}")
                
                # Find the start of this component
                start_line = i
                
                # Find the end by counting braces
                brace_count = 0
                in_component = False
                end_line = i
                
                for j in range(i, len(lines)):
                    for char in lines[j]:
                        if char == '{':
                            brace_count += 1
                            in_component = True
                        elif char == '}':
                            brace_count -= 1
                    
                    if in_component and brace_count == 0:
                        end_line = j
                        break
                
                # Remove the component definition
                print(f"🗑️ Removing duplicate {comp} (lines {start_line+1}-{end_line+1})")
                del lines[start_line:end_line+1]
                removed_components.append(comp)
                
                # Don't increment i, process the same index again
                i = start_line - 1
                break
        
        i += 1
    
    return '\n'.join(lines), removed_components

def fix_project():
    """Fix the latest project by removing duplicate components."""
    
    user_id = '6917910c004fca6f164755e6'
    
    # Get all projects for this user
    prefix = f'projects/{user_id}/'
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix, Delimiter='/')
    
    if 'CommonPrefixes' not in response:
        print("❌ No projects found")
        return
    
    # Get the most recent project (last in the list)
    projects = [p['Prefix'].split('/')[-2] for p in response['CommonPrefixes']]
    latest_project = sorted(projects)[-1]
    
    print(f"🎯 Targeting latest project: {latest_project}")
    
    # Fix App.jsx
    app_key = f'projects/{user_id}/{latest_project}/frontend/src/App.jsx'
    
    try:
        # Download the file
        response = s3.get_object(Bucket=BUCKET_NAME, Key=app_key)
        content = response['Body'].read().decode('utf-8')
        
        print(f"📥 Downloaded {app_key}")
        print(f"📄 File size: {len(content)} bytes")
        
        # UI components that should not be redeclared
        ui_components = ['Button', 'Input', 'Card', 'Loading', 'AnimatedText', 
                        'NavBar', 'NavLink', 'FloatingTabs']
        
        # Remove duplicates
        fixed_content, removed = remove_duplicate_components(content, ui_components)
        
        if removed:
            # Upload the fixed file
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=app_key,
                Body=fixed_content.encode('utf-8'),
                ContentType='application/javascript'
            )
            
            print(f"✅ Fixed {app_key} - removed {len(removed)} duplicate components: {', '.join(removed)}")
        else:
            print(f"✨ No duplicates found in {app_key}")
    
    except Exception as e:
        print(f"❌ Error fixing {app_key}: {e}")

if __name__ == '__main__':
    print("🔧 Starting duplicate component removal...\n")
    fix_project()
    print("\n✅ Done!")

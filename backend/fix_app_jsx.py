import sys
sys.path.insert(0, '.')
from s3_storage import s3_client, S3_BUCKET_NAME

# Read the App.jsx file
key = 'projects/6917910c004fca6f164755e6/web-ecommerce-platform-949200/frontend/src/App.jsx'

try:
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
    content = response['Body'].read().decode('utf-8')
    
    # Find and remove duplicate Button component declaration
    # Look for the inline Button component definition
    lines = content.split('\n')
    new_lines = []
    skip_until_line = -1
    
    for i, line in enumerate(lines):
        # Skip lines if we're in a duplicate component definition
        if i < skip_until_line:
            continue
            
        # Check if this line starts a duplicate Button component
        if 'const Button = ({' in line or 'const Button = (' in line:
            # Find the end of this component (look for the closing );)
            depth = 0
            found_start = False
            for j in range(i, len(lines)):
                if '(' in lines[j]:
                    depth += lines[j].count('(')
                    found_start = True
                if ')' in lines[j]:
                    depth -= lines[j].count(')')
                if found_start and depth <= 0 and ');' in lines[j]:
                    skip_until_line = j + 1
                    print(f'🗑️  Removing duplicate Button component at lines {i+1}-{j+1}')
                    break
            continue
        
        new_lines.append(line)
    
    fixed_content = '\n'.join(new_lines)
    
    # Upload fixed file back to S3
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=fixed_content.encode('utf-8'),
        ContentType='text/javascript'
    )
    
    print(f'✅ Fixed App.jsx - removed duplicate Button component')
    print(f'📍 Location: {key}')
    print('🔄 Refresh your browser to see the changes!')
    
except Exception as e:
    print(f'❌ Error: {e}')

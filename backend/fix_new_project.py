import sys
import re
sys.path.insert(0, '.')
from s3_storage import s3_client, S3_BUCKET_NAME

# Read the App.jsx file
key = 'projects/6917910c004fca6f164755e6/web-enable-working-292020/frontend/src/App.jsx'

try:
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
    content = response['Body'].read().decode('utf-8')
    
    # UI components that should be imported, not redefined
    ui_components = ['Button', 'Input', 'Card', 'Loading', 'AnimatedText', 
                     'NavBar', 'NavLink', 'FloatingTabs']
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    removed_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line declares a UI component
        component_declared = None
        for comp in ui_components:
            if f'const {comp} = ' in line or f'function {comp}(' in line or f'const {comp} = React.forwardRef' in line:
                component_declared = comp
                break
        
        if component_declared:
            # Find the end of this component definition
            start_line = i
            depth = 0
            in_component = False
            
            for j in range(i, len(lines)):
                current_line = lines[j]
                
                # Count parentheses and braces
                depth += current_line.count('(') + current_line.count('{')
                depth -= current_line.count(')') + current_line.count('}')
                
                if j > i:
                    in_component = True
                
                # Check for component end
                if in_component and (');' in current_line or '});' in current_line) and depth <= 0:
                    print(f'🗑️  Removing duplicate {component_declared} (lines {start_line+1}-{j+1})')
                    i = j + 1
                    removed_count += 1
                    break
            else:
                i += 1
        else:
            new_lines.append(line)
            i += 1
    
    fixed_content = '\n'.join(new_lines)
    
    # Clean up any UI COMPONENTS comments
    fixed_content = re.sub(r'//\s*UI\s*COMPONENTS.*?\n\s*\n', '\n', fixed_content, flags=re.IGNORECASE)
    
    # Upload fixed file
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=fixed_content.encode('utf-8'),
        ContentType='text/javascript'
    )
    
    print(f'\n✅ Fixed - removed {removed_count} duplicate components')
    print(f'📍 {key}')
    print('🔄 Refresh browser!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

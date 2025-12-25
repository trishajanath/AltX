import sys
import re
sys.path.insert(0, '.')
from s3_storage import s3_client, S3_BUCKET_NAME

# Read the App.jsx file
key = 'projects/6917910c004fca6f164755e6/web-ecommerce-platform-949200/frontend/src/App.jsx'

try:
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
    content = response['Body'].read().decode('utf-8')
    
    # Find all component names imported from ui components
    import_match = re.search(r'import\s+{([^}]+)}\s+from\s+[\'"]\.\/components\/ui', content)
    if import_match:
        imported_components = [comp.strip() for comp in import_match.group(1).split(',')]
        print(f'📦 Found imported components: {imported_components}')
    else:
        imported_components = ['Button', 'Input', 'Card', 'Loading', 'AnimatedText', 'Navigation']
        print(f'⚠️  No import found, using default list: {imported_components}')
    
    # Remove all duplicate inline component definitions
    lines = content.split('\n')
    new_lines = []
    i = 0
    removed_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line declares a component that's already imported
        component_declared = None
        for comp in imported_components:
            if f'const {comp} = (' in line or f'const {comp} = {{' in line:
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
                    print(f'🗑️  Removing duplicate {component_declared} component (lines {start_line+1}-{j+1})')
                    i = j + 1
                    removed_count += 1
                    break
            else:
                # If we didn't find the end, skip this line anyway
                i += 1
        else:
            new_lines.append(line)
            i += 1
    
    fixed_content = '\n'.join(new_lines)
    
    # Clean up any remaining UI COMPONENTS comments without components
    fixed_content = re.sub(r'//\s*UI\s*COMPONENTS.*?\n\s*\n', '', fixed_content, flags=re.IGNORECASE)
    
    # Upload fixed file back to S3
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=fixed_content.encode('utf-8'),
        ContentType='text/javascript'
    )
    
    print(f'\n✅ Fixed App.jsx - removed {removed_count} duplicate components')
    print(f'📍 Location: {key}')
    print('🔄 Refresh your browser to see the changes!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

"""Fix the App.jsx export statement - replace wrong export with correct App export"""
from s3_storage import s3_client, S3_BUCKET_NAME
import re

project_id = '6917910c004fca6f164755e6'
project_name = 'e-commerce-selling-groceries-736975'
key = f'projects/{project_id}/{project_name}/frontend/src/App.jsx'

print(f"📥 Fetching App.jsx from S3...")
response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
content = response['Body'].read().decode('utf-8')

print(f'Original size: {len(content)} chars')

# Check what's being exported
export_match = re.search(r'export default (\w+);?', content)
if export_match:
    current_export = export_match.group(1)
    print(f"📌 Current export: {current_export}")
else:
    print("⚠️ No export default found!")

# Look for the App component definition
app_patterns = [
    r'(const App\s*=)',
    r'(function App\s*\()',
    r'(class App\s+extends)',
]

has_app_component = False
for pattern in app_patterns:
    if re.search(pattern, content):
        has_app_component = True
        print(f"✅ Found App component definition")
        break

if not has_app_component:
    print("⚠️ No App component found in file!")
    # Search for what components ARE defined
    component_defs = re.findall(r'(?:const|function|class)\s+([A-Z]\w+)', content)
    print(f"📋 Components found: {component_defs}")

# Fix the export
fixes_applied = []

# Remove wrong exports
wrong_exports = ['Notification', 'Button', 'Card', 'Input', 'Modal', 'Header', 'Footer']
for wrong in wrong_exports:
    wrong_export = f'export default {wrong};'
    if wrong_export in content:
        content = content.replace(wrong_export, '')
        fixes_applied.append(f"Removed wrong export: {wrong}")

    wrong_export_no_semi = f'export default {wrong}'
    if wrong_export_no_semi in content and 'export default App' not in content:
        content = content.replace(wrong_export_no_semi + '\n', '')
        content = content.replace(wrong_export_no_semi, '')
        fixes_applied.append(f"Removed wrong export (no semicolon): {wrong}")

# Ensure App is exported
if 'export default App' not in content:
    # Add it at the end
    content = content.rstrip() + '\n\nexport default App;\n'
    fixes_applied.append("Added export default App")
    print("✅ Added 'export default App;'")

# Remove duplicate exports if any
export_count = content.count('export default App')
if export_count > 1:
    # Keep only one
    content = re.sub(r'(export default App;?\s*)+', 'export default App;\n', content)
    fixes_applied.append(f"Removed {export_count - 1} duplicate export statements")

print(f'\n🔧 Fixes applied: {len(fixes_applied)}')
for fix in fixes_applied:
    print(f'   - {fix}')

print(f'\nFixed size: {len(content)} chars')

# Upload fixed version
s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=content.encode('utf-8'), ContentType='text/javascript')
print('✅ Uploaded fixed App.jsx to S3!')
print('🔄 Refresh the preview to see the fix.')

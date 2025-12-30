"""Comprehensive fix for the e-commerce project - check App.jsx and all files"""
from s3_storage import s3_client, S3_BUCKET_NAME
import re

project_id = '6917910c004fca6f164755e6'
project_name = 'e-commerce-selling-groceries-736975'

def get_file(path):
    key = f'projects/{project_id}/{project_name}/{path}'
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"❌ Could not fetch {path}: {e}")
        return None

def put_file(path, content, content_type='text/javascript'):
    key = f'projects/{project_id}/{project_name}/{path}'
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=content.encode('utf-8'), ContentType=content_type)
    print(f"✅ Uploaded {path}")

# 1. Check App.jsx for issues
print("\n=== CHECKING App.jsx ===")
app_jsx = get_file('frontend/src/App.jsx')
if app_jsx:
    issues = []
    
    # Check the main return/render
    if 'return (' not in app_jsx:
        issues.append("Missing return statement")
    
    # Check for the main div with styling
    if 'bg-slate-900' in app_jsx:
        print("✅ Has dark background styling (bg-slate-900)")
    else:
        issues.append("Missing dark background")
    
    if 'min-h-screen' not in app_jsx:
        issues.append("Missing min-h-screen class - page might not fill viewport")
        # Fix: Add min-h-screen to the main container
        app_jsx = app_jsx.replace(
            '<div className="bg-slate-900 font-sans">',
            '<div className="bg-slate-900 font-sans min-h-screen">'
        )
        print("🔧 Added min-h-screen to main container")
    
    # Check exports
    if 'export default App' not in app_jsx:
        issues.append("Missing export default App")
        app_jsx = app_jsx.rstrip() + '\n\nexport default App;\n'
        print("🔧 Added export default App")
    
    # Check for duplicate export statements
    export_count = app_jsx.count('export default')
    if export_count > 1:
        issues.append(f"Found {export_count} export default statements")
        # Remove duplicates
        app_jsx = re.sub(r'(export default \w+;?\s*)+$', 'export default App;\n', app_jsx)
        print("🔧 Fixed duplicate exports")
    
    # Upload fixed version
    if issues:
        print(f"\n🔧 Found {len(issues)} issues:")
        for i in issues:
            print(f"   - {i}")
        put_file('frontend/src/App.jsx', app_jsx)
    else:
        print("✅ App.jsx looks good!")
    
    # Print the main App component return
    app_return = re.search(r'const App = .*?return \(([^)]+(?:\([^)]*\)[^)]*)*)\);?\s*\};?', app_jsx, re.DOTALL)
    if app_return:
        print("\n=== APP RETURN STRUCTURE (first 500 chars) ===")
        print(app_return.group(1)[:500])

# 2. Check index.html 
print("\n\n=== CHECKING index.html ===")
index_html = get_file('frontend/index.html')
if index_html:
    if 'id="root"' in index_html:
        print("✅ Has root div")
    else:
        print("❌ Missing root div!")
    
    if '<title>' in index_html:
        print("✅ Has title tag")

print("\n🔄 Refresh your browser to see the fixes!")

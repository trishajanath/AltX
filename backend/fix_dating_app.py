#!/usr/bin/env python3
"""Fix the dating app routing and swipe handler"""

from s3_storage import get_project_from_s3, upload_project_to_s3
import re

def fix_dating_app():
    data = get_project_from_s3('dating', '69185f9403d5c9719c80c17a')
    if not data:
        print("❌ Could not load project")
        return
    
    files = data.get('files', [])
    modified = False
    
    # Fix App.jsx
    for f in files:
        if f.get('path') == 'frontend/src/App.jsx':
            content = f.get('content')
            
            # Fix: Swap routes so catch-all is LAST
            # Find the routes section and reorder
            routes_pattern = r'(<Route path="/chat-option[^/]*/>)\s*\n(\s*<Route path="\*"[^/]*/>)'
            if not re.search(routes_pattern, content):
                # Routes are in wrong order, swap them
                content = re.sub(
                    r'(\s*)(<Route path="\*" element=\{<Navigate to="/discover" />\} />)\s*\n(\s*)(<Route path="/chat-option[^"]*" element=\{<ChatOption />\} />)',
                    r'\1\4\n\3\2',
                    content
                )
                print("✅ Fixed route order (catch-all now last)")
            
            f['content'] = content
            modified = True
            break
    
    if modified:
        upload_project_to_s3('dating', files, '69185f9403d5c9719c80c17a')
        print("✅ Uploaded fixed files to S3")
    else:
        print("⚠️ No changes needed")

if __name__ == '__main__':
    fix_dating_app()

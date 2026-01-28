#!/usr/bin/env python3
from s3_storage import get_project_from_s3, upload_project_to_s3

data = get_project_from_s3('dating', '69185f9403d5c9719c80c17a')
if data:
    files = data.get('files', [])
    for f in files:
        if f.get('path') == 'frontend/src/App.jsx':
            content = f.get('content')
            # Swap the two route lines
            lines = content.split('\n')
            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                # Check if this is the catch-all route followed by chat-option
                if 'path="*"' in line and i + 1 < len(lines) and 'chat-option' in lines[i+1]:
                    # Swap them - put chat-option first
                    new_lines.append(lines[i+1])  # chat-option route
                    new_lines.append(line)         # catch-all route
                    i += 2
                else:
                    new_lines.append(line)
                    i += 1
            
            content = '\n'.join(new_lines)
            f['content'] = content
            print("Fixed route order")
            break
    
    upload_project_to_s3('dating', files, '69185f9403d5c9719c80c17a')
    print("Done")

#!/usr/bin/env python3
from s3_storage import get_project_from_s3

data = get_project_from_s3('dating', '69185f9403d5c9719c80c17a')
if data:
    for f in data.get('files', []):
        if f.get('path') == 'frontend/src/App.jsx':
            content = f.get('content')
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'handleSwipe' in line:
                    start = max(0, i-2)
                    end = min(len(lines), i+15)
                    print(f"=== handleSwipe context (lines {start+1}-{end}) ===")
                    for j in range(start, end):
                        print(f"{j+1}: {lines[j]}")
                    break

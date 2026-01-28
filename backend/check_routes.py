#!/usr/bin/env python3
from s3_storage import get_project_from_s3

data = get_project_from_s3('dating', '69185f9403d5c9719c80c17a')
if data:
    for f in data.get('files', []):
        if f.get('path') == 'frontend/src/App.jsx':
            for i, line in enumerate(f.get('content').split('\n')):
                if 'Route' in line and 'path=' in line:
                    print(f"Line {i+1}: {line.strip()}")

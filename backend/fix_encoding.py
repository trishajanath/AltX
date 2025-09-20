import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all 'with open(..., 'w')' with 'with open(..., 'w', encoding='utf-8')'
content = re.sub(r"with open\(([^,]+),\s*'w'\)", r"with open(\1, 'w', encoding='utf-8')", content)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed all file write operations to use UTF-8 encoding')
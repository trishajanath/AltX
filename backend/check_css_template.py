"""Check if CSS template has double braces"""
import re

with open('pure_ai_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the base_css section
base_css_match = re.search(r"base_css = '''(.*?)'''", content, re.DOTALL)
if base_css_match:
    base_css = base_css_match.group(1)
    double_open = base_css.count('{{')
    double_close = base_css.count('}}')
    print(f'Double braces in base_css template:')
    print(f'  {{ count: {double_open}')
    print(f'  }} count: {double_close}')
    if double_open == 0 and double_close == 0:
        print('✅ CSS template is clean!')
    else:
        print('❌ Still has double braces - need to fix!')
        # Show lines with double braces
        lines = base_css.split('\n')
        for i, line in enumerate(lines):
            if '{{' in line or '}}' in line:
                print(f'  Line {i}: {line[:80]}')
else:
    print('Could not find base_css template')

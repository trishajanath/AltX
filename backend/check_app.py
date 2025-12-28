from s3_storage import s3_client, S3_BUCKET_NAME
import re

key = 'projects/6917910c004fca6f164755e6/web-grocery-working-864606/frontend/src/App.jsx'
response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
content = response['Body'].read().decode('utf-8')

print('=== CHECKING FOR ISSUES ===')

# Check for Button component
button_uses = content.count('<Button')
print(f'Button components used: {button_uses}')

# Check for styling issues
print(f'bg-black count: {content.count("bg-black")}')
print(f'text-white count: {content.count("text-white")}')
print(f'font-mono count: {content.count("font-mono")}')

# Check if Button is redefined
if 'const Button' in content:
    print('WARNING: Button is being redefined!')
else:
    print('Button not redefined (good)')

# Show HomePage component
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'HomePage' in line and 'const' in line:
        print(f'\nHomePage component at line {i+1}:')
        for j in range(i, min(i+50, len(lines))):
            print(f'{j+1}: {lines[j]}')
        break

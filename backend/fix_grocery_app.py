"""Fix the grocery app styling - replace brutalist design with modern professional design"""
from s3_storage import s3_client, S3_BUCKET_NAME
import re

key = 'projects/6917910c004fca6f164755e6/web-grocery-working-864606/frontend/src/App.jsx'
response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
content = response['Body'].read().decode('utf-8')

print(f'Original size: {len(content)} chars')

# Replace brutalist styling with modern professional styling
replacements = [
    # Background colors
    ('bg-black', 'bg-white'),
    ('text-white', 'text-gray-800'),
    
    # Borders - make them softer
    ('border-2 border-white', 'border border-gray-200 shadow-sm'),
    ('border-white', 'border-gray-200'),
    
    # Font - replace harsh mono with clean sans
    ('font-mono', 'font-sans'),
    
    # Header - make it white with shadow
    ('sticky top-0 z-40 bg-white text-gray-800 p-[1rem] border border-gray-200 shadow-sm', 
     'sticky top-0 z-40 bg-white shadow-lg p-4 border-b border-gray-100'),
    
    # Button hover states on dark removed
    ('hover:bg-white hover:text-black', 'hover:bg-gray-100'),
    ('hover:bg-white/10', 'hover:bg-gray-100'),
    
    # Modal backgrounds
    ('bg-black/80', 'bg-black/50'),
    ('bg-white border border-gray-200 shadow-sm', 'bg-white rounded-xl shadow-2xl'),
    
    # Purple accent color (keep it but make it work on light backgrounds)
    ('bg-[#8b5cf6]', 'bg-purple-600'),
    ('text-[#8b5cf6]', 'text-purple-600'),
    ('hover:text-[#8b5cf6]', 'hover:text-purple-600'),
    
    # Make cards look better
    ('p-[1rem]', 'p-6'),
    
    # Fix specific components that reference white borders
    ('form-checkbox bg-white border-gray-800', 'form-checkbox'),
]

fixed = content
for old, new in replacements:
    if old in fixed:
        count = fixed.count(old)
        fixed = fixed.replace(old, new)
        print(f'  Replaced {count}x: "{old[:30]}..." -> "{new[:30]}..."')

# Additional regex fixes
# Fix the header className specifically
fixed = re.sub(
    r'className="sticky top-0 z-40 bg-white text-gray-800 p-4 border-b border-gray-100 border border-gray-200 shadow-sm"',
    'className="sticky top-0 z-40 bg-white shadow-md border-b border-gray-100 p-4"',
    fixed
)

# Make sure modals have proper rounded corners
fixed = re.sub(
    r'className="bg-white rounded-xl shadow-2xl w-full',
    'className="bg-white rounded-2xl shadow-2xl w-full',
    fixed
)

# Make sure we have good contrast
if 'text-gray-800' not in fixed:
    print("Warning: text-gray-800 not found - design may have issues")

print(f'\nFixed size: {len(fixed)} chars')

# Upload fixed version
s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=fixed.encode('utf-8'), ContentType='text/javascript')
print('✅ Uploaded fixed App.jsx to S3!')
print('Refresh the preview to see the improved design.')

import boto3, os, re
from dotenv import load_dotenv

load_dotenv()

from backend.s3_storage import s3_client as s3

bucket = os.getenv("S3_BUCKET_NAME")
key = "projects/6917910c004fca6f164755e6/web-ecommerce-busy-557776/frontend/src/App.jsx"

print("📥 Downloading App.jsx from S3...")
obj = s3.get_object(Bucket=bucket, Key=key)
content = obj["Body"].read().decode("utf-8")
print(f"✅ Downloaded {len(content)} bytes")

# Split into lines
lines = content.split('\n')

print("\n🔍 Searching for duplicate UI component declarations...")

# Components to remove (they're already in ui/ files)
components_to_remove = ['Input', 'Card', 'Loading', 'AnimatedText']
removed_count = 0

for component_name in components_to_remove:
    pattern = rf'^\s*const\s+{component_name}\s*='
    
    i = 0
    while i < len(lines):
        if re.match(pattern, lines[i]):
            start_line = i
            print(f"🔴 Found {component_name} declaration at line {i+1}")
            
            # Find the end of this declaration
            if '=>' in lines[i] and lines[i].strip().endswith(');'):
                # Single line arrow function
                end_line = i
            elif '=>' in lines[i] and '(' in lines[i]:
                # Multi-line arrow function - find closing
                paren_count = lines[i].count('(') - lines[i].count(')')
                brace_count = lines[i].count('{') - lines[i].count('}')
                end_line = i
                
                for j in range(i + 1, min(i + 50, len(lines))):
                    paren_count += lines[j].count('(') - lines[j].count(')')
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    
                    if (paren_count <= 0 and brace_count <= 0 and 
                        (');' in lines[j] or lines[j].strip().endswith(');'))):
                        end_line = j
                        break
            else:
                # Function with body
                brace_count = lines[i].count('{') - lines[i].count('}')
                end_line = i
                
                for j in range(i + 1, min(i + 50, len(lines))):
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if brace_count <= 0 and '};' in lines[j]:
                        end_line = j
                        break
            
            print(f"🗑️  Removing {component_name} (lines {start_line+1} to {end_line+1})")
            del lines[start_line:end_line+1]
            removed_count += 1
            # Don't increment i since we deleted lines
            continue
        
        i += 1

if removed_count == 0:
    print("✅ No duplicate component declarations found")
else:
    print(f"\n✅ Removed {removed_count} duplicate component declarations")

# Verify import exists
has_ui_import = False
for line in lines[:50]:
    if "Button" in line and "import" in line and "./components/ui/" in line:
        has_ui_import = True
        break

if not has_ui_import:
    print("⚠️  WARNING: Button import may be missing!")
else:
    print("✅ UI components import verified")

# Rejoin content
fixed_content = '\n'.join(lines)

# Verify no duplicates remain
duplicates_found = []
for component in ['Button', 'Input', 'Card', 'Loading', 'AnimatedText']:
    matches = list(re.finditer(rf'const\s+{component}\s*=', fixed_content))
    if matches:
        duplicates_found.append(f"{component} ({len(matches)}x)")

if duplicates_found:
    print(f"\n⚠️  WARNING: Still found declarations: {', '.join(duplicates_found)}")
else:
    print("\n✅ No UI component declarations found in fixed content")

# Upload fixed content back to S3
print(f"\n📤 Uploading fixed App.jsx to S3...")
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=fixed_content.encode('utf-8'),
    ContentType='text/javascript'
)

print(f"✅ Successfully uploaded fixed App.jsx ({len(fixed_content)} bytes)")
print(f"📊 Line count: {len(content.split(chr(10)))} → {len(fixed_content.split(chr(10)))}")
print("\n🎉 DONE! All duplicate UI component declarations removed.")
print("🔄 Refresh your browser to see the changes.")

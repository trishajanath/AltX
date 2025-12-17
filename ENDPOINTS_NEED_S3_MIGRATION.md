# Endpoints Requiring S3 Migration

## ✅ Already S3-Enabled (Current)

1. **`/api/project-file-tree`** (line 4315)
   - ✅ Reads from S3 first
   - ✅ Falls back to local
   - Status: **COMPLETE**

2. **`/api/project-file-content`** (line 4450)
   - ✅ Reads from S3 first
   - ✅ Falls back to local
   - Status: **COMPLETE**

3. **`/api/project-history`** (line 4216)
   - ✅ Lists projects from S3
   - Status: **COMPLETE**

4. **`/api/ai-customize-project`** (line 2930)
   - ✅ Reads from S3
   - ✅ Writes to S3
   - Status: **COMPLETE** (refactored earlier)

5. **`/api/sandbox-preview/{project_name}`** (line 715)
   - ✅ Reads from S3 first
   - ✅ Falls back to local
   - Status: **COMPLETE**

6. **`/api/create-project-structure`** (line 507)
   - ✅ Generates directly to S3 (via PureAIGenerator)
   - ✅ Removed redundant upload (just fixed)
   - Status: **COMPLETE**

7. **`/api/build-with-ai`** (line 1508)
   - ✅ Generates directly to S3
   - ✅ Removed redundant upload (just fixed)
   - Status: **COMPLETE**

## ❌ Still Using Local Storage (Need Migration)

### High Priority (Core Functionality)

1. **`/api/save-project-file`** (line 3335)
   ```python
   # Current: Writes to local filesystem only
   with open(full_file_path, 'w', encoding='utf-8') as f:
       f.write(cleaned_content)
   
   # Needed: Write to S3 + optional local cache
   upload_project_to_s3(project_slug, [{'path': file_path, 'content': content}], user_id)
   ```
   - **Issue**: Monaco editor saves go to local only
   - **Impact**: Changes lost on EC2 restart
   - **Fix**: Add S3 upload after write

2. **`/api/ai-apply-changes`** (line 3100)
   ```python
   # Current: Writes all AI edits to local
   with open(target, 'w', encoding='utf-8', newline='\n') as f:
       f.write(cleaned)
   
   # Needed: Batch upload to S3
   files_to_upload = [{'path': fp, 'content': content} for fp, content in edits]
   upload_project_to_s3(project_slug, files_to_upload, user_id)
   ```
   - **Issue**: AI-suggested changes not persisted to S3
   - **Impact**: AI improvements lost on EC2
   - **Fix**: Batch upload after applying edits

3. **`/api/ai-project-assistant`** (line 1807)
   ```python
   # Current: Complex local file operations
   # - Reads from local: open(app_jsx_path, 'r')
   # - Writes to local: open(app_jsx_path, 'w')
   # - Multiple files modified locally
   
   # Needed: Full S3 integration
   # - Read from S3: get_project_from_s3()
   # - Modify in memory
   # - Write to S3: upload_project_to_s3()
   ```
   - **Issue**: 200+ lines of local file operations
   - **Impact**: Assistant features don't work on EC2
   - **Fix**: Major refactor needed (similar to `/api/ai-customize-project`)

### Medium Priority (Legacy/Fallback)

4. **`/project-file-tree`** (line 184) - **DEPRECATED**
   - **Note**: Replaced by `/api/project-file-tree` (line 4315)
   - **Fix**: Remove or redirect to new endpoint

5. **`/project-file-content`** (line 244) - **DEPRECATED**
   - **Note**: Replaced by `/api/project-file-content` (line 4450)
   - **Fix**: Remove or redirect to new endpoint

### Low Priority (Development/Testing)

6. **`/api/install-dependencies`** (line 3378)
   - Runs `npm install` on local files
   - Likely needs local checkout for package installation
   - May be acceptable as local-only for development

7. **`/api/run-project`** (line 3465)
   - Starts dev servers on local files
   - Requires local filesystem for Vite/FastAPI
   - May be acceptable as local-only for preview

## 📋 Migration Plan

### Phase 1: Critical Fixes (DO NOW)
1. ✅ `/api/save-project-file` - Add S3 upload
2. ✅ `/api/ai-apply-changes` - Add S3 batch upload
3. ✅ `/api/ai-project-assistant` - Full S3 refactor

### Phase 2: Cleanup (NEXT)
4. ❌ Remove deprecated `/project-file-tree`
5. ❌ Remove deprecated `/project-file-content`

### Phase 3: Architecture Decision (LATER)
6. 🤔 Decide on preview/run strategy for EC2:
   - Option A: Pull from S3 to temp dir for preview
   - Option B: Use serverless functions (Lambda) for backend
   - Option C: Container-based ephemeral environments

## 🔧 S3 Migration Pattern

### Pattern 1: Read Operation
```python
# Try S3 first
try:
    project_data = get_project_from_s3(project_slug, user_id)
    if project_data and project_data.get('files'):
        # Find file in S3
        for file_info in project_data['files']:
            if file_info['path'] == target_path:
                return file_info['content']
except Exception as e:
    print(f"S3 error: {e}")

# Fallback to local (development mode)
local_path = Path("generated_projects") / project_slug / target_path
if local_path.exists():
    return local_path.read_text()
```

### Pattern 2: Write Operation
```python
# Write to S3 (primary)
upload_project_to_s3(
    project_slug=project_slug,
    files=[{'path': file_path, 'content': content}],
    user_id=user_id
)

# Optional: Also write locally for development
if os.getenv('DEV_MODE') == 'true':
    local_path = Path("generated_projects") / project_slug / file_path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(content)
```

### Pattern 3: Batch Write Operation
```python
# Collect all changes
files_to_upload = []
for edit in edits:
    files_to_upload.append({
        'path': edit['file_path'],
        'content': edit['content']
    })

# Single S3 upload for all changes
upload_project_to_s3(project_slug, files_to_upload, user_id)
```

## 🚨 Critical Issues on EC2

### Without S3 Migration:
1. ❌ Monaco editor saves → lost on restart
2. ❌ AI customizations → lost on restart
3. ❌ Manual file edits → lost on restart
4. ❌ AI project assistant → doesn't work at all

### With S3 Migration:
1. ✅ All changes persist in cloud
2. ✅ Multi-instance safe
3. ✅ Instant disaster recovery
4. ✅ No data loss on deployment

## 📊 Current Status

| Endpoint | S3 Read | S3 Write | Status | Priority |
|----------|---------|----------|--------|----------|
| `/api/create-project-structure` | N/A | ✅ Direct | **DONE** | - |
| `/api/build-with-ai` | N/A | ✅ Direct | **DONE** | - |
| `/api/project-file-tree` | ✅ | N/A | **DONE** | - |
| `/api/project-file-content` | ✅ | N/A | **DONE** | - |
| `/api/project-history` | ✅ | N/A | **DONE** | - |
| `/api/ai-customize-project` | ✅ | ✅ | **DONE** | - |
| `/api/sandbox-preview` | ✅ | N/A | **DONE** | - |
| `/api/save-project-file` | ❌ | ❌ | **TODO** | 🔴 HIGH |
| `/api/ai-apply-changes` | ❌ | ❌ | **TODO** | 🔴 HIGH |
| `/api/ai-project-assistant` | ❌ | ❌ | **TODO** | 🔴 HIGH |
| `/project-file-tree` (old) | ❌ | N/A | **DEPRECATED** | 🟡 REMOVE |
| `/project-file-content` (old) | ❌ | N/A | **DEPRECATED** | 🟡 REMOVE |

---

**Next Steps:** Fix the 3 HIGH priority endpoints to complete S3 migration.

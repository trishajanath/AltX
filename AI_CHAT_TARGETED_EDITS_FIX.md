# AI Chat Targeted Edits Fix

## Problem
The AI assistant in generated projects was **replacing entire files** instead of making targeted changes when users requested modifications like "change background color to black".

**Example of broken behavior:**
- User: "change background color to black"
- AI: Replaced entire 637-line App.jsx with just 17 lines
- Result: Lost all functionality, only showing basic header

## Root Cause
The AI was instructed to provide **"FULL file content"** in the system prompt, and returned `"edit_type": "full_file_replace"` which overwrote entire files.

## Solution Implemented

### 1. Updated System Prompt (main.py lines ~2105-2139)
Changed from:
```
7. For App.jsx updates, provide the FULL file content with imports
```

To:
```
CRITICAL RULES - TARGETED EDITS ONLY:
6. For EXISTING files (like App.jsx, App.css), use "edit_type": "targeted_edit" with search/replace
7. NEVER send full file replacements for existing files - only send the specific lines to change
```

### 2. Added Example for Targeted Edits
```json
{
  "changes": [
    {
      "file_path": "frontend/src/App.css",
      "edit_type": "targeted_edit",
      "search": ".App {\n  text-align: center;\n  background-color: #282c34;\n  min-height: 100vh;",
      "replace": ".App {\n  text-align: center;\n  background-color: #000000;\n  min-height: 100vh;"
    }
  ],
  "explanation": "Changed App background color to black"
}
```

### 3. Updated Edit Processing Logic (main.py lines ~2577-2615)
- Added support for both `search/replace` (new format) and `old_code/new_code` (legacy)
- Improved error messages when search pattern not found
- Added debugging output to help diagnose issues

### 4. Edit Types Now Supported
- `"new_file"`: Create completely new files (for new components only)
- `"targeted_edit"`: Modify existing files with search/replace patterns (PREFERRED)
- `"append"`: Add content to end of file
- `"replace"`: Full file replacement (discouraged, backwards compatibility only)

## How It Works Now

When user says "change background color to black":

1. AI analyzes the request and existing file
2. Generates targeted edit with:
   - `search`: Exact code snippet to find (with context)
   - `replace`: Exact code to replace it with
3. Backend finds the search pattern in file
4. Replaces ONLY that section
5. Preserves rest of file intact

## Benefits
✅ No more lost code when making simple changes
✅ Faster - only sends small code snippets, not entire files
✅ More accurate - AI includes context to ensure unique matches
✅ Better error handling - warns if pattern not found instead of failing silently

## Testing
To test the fix:
1. Open any generated project in Monaco editor
2. Use AI chat: "change background color to red"
3. Verify only the background-color CSS line changes
4. Verify rest of file remains intact

## Files Modified
- `backend/main.py` - Updated AI prompt and edit processing logic
- `backend/monaco_server.py` - Added `/api/smart-edit-file` endpoint for future use

## Notes
- Monaco server also has a similar AI chat endpoint that may need the same fix
- The grocery app has been restored from git (commit 6263767)
- Future improvements: Add diff preview before applying changes

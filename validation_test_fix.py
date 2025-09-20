#!/usr/bin/env python3
"""
Validation script to test the specific fix for the await issue
"""

import sys
import re

def validate_get_chat_response_calls():
    """Check that all get_chat_response calls use run_in_threadpool"""
    
    try:
        with open('backend/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all get_chat_response calls
        pattern = r'await\s+get_chat_response\('
        direct_awaits = re.findall(pattern, content)
        
        if direct_awaits:
            print(f"❌ Found {len(direct_awaits)} direct await calls to get_chat_response:")
            for match in direct_awaits:
                print(f"   {match}")
            return False
        
        # Find all proper threadpool calls
        pattern = r'await\s+run_in_threadpool\(get_chat_response'
        threadpool_calls = re.findall(pattern, content)
        
        print(f"✅ Found {len(threadpool_calls)} proper threadpool calls to get_chat_response")
        print("✅ No direct await calls found - the fix is correct!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Validating get_chat_response calls...")
    print("=" * 50)
    
    if validate_get_chat_response_calls():
        print("\n🎉 All get_chat_response calls are properly handled!")
        print("The 'object str can't be used in await expression' error should be fixed.")
        sys.exit(0)
    else:
        print("\n❌ Issues found that need to be addressed.")
        sys.exit(1)
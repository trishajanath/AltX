#!/usr/bin/env python3
"""Test scanner import and functionality"""

try:
    from scanner import scan_url
    print("✅ Scanner module imports successfully")
    
    # Test the function
    result = scan_url('https://google.com')
    print(f"✅ scan_url function works - Security Score: {result.get('security_score', 'N/A')}")
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

import json
import asyncio
from main import provide_local_fix_suggestion

# Test the fix functionality with a detailed issue
async def test_detailed_fix():
    # Create a realistic test issue
    test_issue = {
        'file': 'config/database.py',
        'type': 'hardcoded_credential',
        'description': 'Hardcoded database password detected',
        'line': 15,
        'severity': 'Critical',
        'vulnerable_code': 'DB_PASSWORD = "admin123"'
    }
    
    print('Testing detailed fix generation...')
    result = await provide_local_fix_suggestion(test_issue)
    
    print('\n=== FIX GENERATION RESULT ===')
    print(f"Success: {result.get('success')}")
    print(f"Fix Summary: {result.get('fix_summary')}")
    print(f"Security Impact: {result.get('security_impact')}")
    print(f"\nSuggested Code:")
    print(result.get('suggested_code', 'None provided'))
    print(f"\nExplanation:")
    print(result.get('explanation', 'None provided'))
    print(f"\nPrevention Tips:")
    for tip in result.get('prevention_tips', []):
        print(f"  - {tip}")

# Run the test
asyncio.run(test_detailed_fix())
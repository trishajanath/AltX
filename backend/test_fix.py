import json
import asyncio
from main import propose_fix
from pydantic import BaseModel

# Define the request model
class FixRequest(BaseModel):
    repo_url: str
    issue: dict
    branch_name: str = None

# Test the fix functionality with a sample issue
async def test_fix():
    # Create a test issue
    test_issue = {
        'file': 'test.py',
        'type': 'security',
        'description': 'Hardcoded password detected',
        'line': 10,
        'severity': 'High',
        'vulnerable_code': 'password = "hardcoded123"'
    }
    
    # Create request for a test repo (use a non-existent one for local testing)
    request = FixRequest(
        repo_url='test_local_analysis',  # This will trigger local analysis
        issue=test_issue
    )
    
    print('Testing propose_fix functionality...')
    result = await propose_fix(request)
    print('Fix result:')
    print(json.dumps(result, indent=2)[:1000])

# Run the test
asyncio.run(test_fix())
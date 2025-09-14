import asyncio
import tempfile
import os
from main import propose_fix
from pydantic import BaseModel

class FixRequest(BaseModel):
    repo_url: str
    issue: dict
    branch_name: str = None

async def test_github_fix():
    # Create a realistic test issue with vulnerable code
    test_issue = {
        'file': 'backend/config.py',
        'type': 'hardcoded_credential', 
        'description': 'Hardcoded API key detected',
        'line': 5,
        'severity': 'Critical',
        'vulnerable_code': 'API_KEY = "sk-1234567890abcdef"'
    }
    
    # Test with a mock GitHub URL (will trigger local processing for demo)
    request = FixRequest(
        repo_url='test_local_repo',  # This will trigger local analysis 
        issue=test_issue
    )
    
    print('=== TESTING GITHUB FIX GENERATION ===')
    print(f'Issue: {test_issue["description"]}')
    print(f'File: {test_issue["file"]}')
    print(f'Vulnerable code: {test_issue["vulnerable_code"]}')
    print()
    
    # Create a temporary file with vulnerable content to simulate real scenario
    temp_dir = tempfile.mkdtemp()
    test_file_path = os.path.join(temp_dir, 'config.py')
    
    # Create the vulnerable file content
    vulnerable_content = '''# Configuration file
import requests

# Database settings
DB_HOST = "localhost"
API_KEY = "sk-1234567890abcdef"  # This is the vulnerable line
DEBUG = True

def get_api_client():
    return requests.Session()
'''
    
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    with open(test_file_path, 'w') as f:
        f.write(vulnerable_content)
    
    print(f'Created test file with vulnerable content at: {test_file_path}')
    print('Original content:')
    print(vulnerable_content)
    print()
    
    try:
        result = await propose_fix(request)
        print('=== FIX RESULT ===')
        print(f'Success: {result.get("success")}')
        print(f'Message: {result.get("message", "No message")}')
        
        if result.get('code_comparison'):
            print('\n=== CODE COMPARISON ===')
            comparison = result['code_comparison']
            print(f'Original length: {comparison.get("content_length_before", 0)} chars')
            print(f'Fixed length: {comparison.get("content_length_after", 0)} chars')
            print(f'Character changes: {comparison.get("character_changes", 0)}')
            
            print('\n--- FIXED CONTENT ---')
            print(comparison.get('fixed_content', 'No fixed content available')[:1000])
            
    except Exception as e:
        print(f'Error during fix generation: {e}')
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        os.rmdir(temp_dir)

asyncio.run(test_github_fix())
from ai_assistant import get_chat_response
import asyncio

async def test_ai_directly():
    prompt = """
    You are a security expert. Fix this hardcoded password issue:
    
    Vulnerable Code: DB_PASSWORD = "admin123"
    
    Provide a JSON response with:
    {
        "fix_summary": "Replace hardcoded password with environment variable",
        "security_impact": "Prevents credential exposure in source code",
        "suggested_code": "import os\\nDB_PASSWORD = os.getenv('DB_PASSWORD')",
        "explanation": "Detailed explanation here",
        "prevention_tips": ["Use environment variables", "Never commit secrets"]
    }
    """
    
    result = get_chat_response([
        {'role': 'user', 'content': prompt}
    ], 'smart')
    
    print('AI Response:', result[:1000])

asyncio.run(test_ai_directly())
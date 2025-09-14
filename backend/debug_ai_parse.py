from ai_assistant import get_chat_response
import asyncio
import re
import json

async def test_ai_and_parse():
    prompt = """
    You are a security expert. Fix this hardcoded password issue:
    
    Vulnerable Code: DB_PASSWORD = "admin123"
    
    Respond with ONLY a valid JSON object in this exact format:
    {"fix_summary": "description", "security_impact": "impact", "suggested_code": "code", "explanation": "explanation", "prevention_tips": ["tip1", "tip2"]}
    """
    
    result = get_chat_response([
        {'role': 'user', 'content': prompt}
    ], 'smart')
    
    print('=== FULL AI RESPONSE ===')
    print(result)
    print('\n=== ATTEMPTING TO PARSE ===')
    
    # Try different parsing approaches
    try:
        # Method 1: Direct JSON parse
        parsed = json.loads(result)
        print('✅ Direct JSON parsing worked!')
        print(parsed)
        return
    except Exception as e:
        print(f'❌ Direct parsing failed: {e}')
    
    try:
        # Method 2: Extract from code blocks
        json_block = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
        if json_block:
            json_text = json_block.group(1)
            parsed = json.loads(json_text)
            print('✅ Code block parsing worked!')
            print(parsed)
            return
    except Exception as e:
        print(f'❌ Code block parsing failed: {e}')
    
    try:
        # Method 3: Find JSON boundaries
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_text = result[json_start:json_end]
            print(f'Found JSON text: {json_text[:200]}...')
            parsed = json.loads(json_text)
            print('✅ Boundary parsing worked!')
            print(parsed)
            return
    except Exception as e:
        print(f'❌ Boundary parsing failed: {e}')
    
    print('❌ All parsing methods failed')

asyncio.run(test_ai_and_parse())
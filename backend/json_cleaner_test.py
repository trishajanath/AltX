import json
import re

def clean_and_parse_json(text):
    """Clean and parse JSON from AI response"""
    try:
        # First try to find JSON in ```json blocks
        json_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_block:
            json_text = json_block.group(1)
            
            # Clean the JSON text by removing problematic characters
            # Replace newlines in string values with \n
            json_text = re.sub(r'(?<=["\s])\n(?=[^"}])', '\\n', json_text)
            json_text = re.sub(r'(?<=["\s])\r(?=[^"}])', '\\r', json_text)
            json_text = re.sub(r'(?<=["\s])\t(?=[^"}])', '\\t', json_text)
            
            # Try parsing
            return json.loads(json_text)
    except Exception as e:
        print(f"JSON cleaning attempt failed: {e}")
    
    # Try different fallback approaches
    try:
        # Method: Extract between first { and last }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            json_text = text[start:end]
            # Simple cleanup
            json_text = json_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            # Remove extra whitespace
            json_text = re.sub(r'\s+', ' ', json_text)
            return json.loads(json_text)
    except Exception as e:
        print(f"Fallback parsing failed: {e}")
    
    return None

# Test with sample problematic JSON
test_text = '''🧠 **Comprehensive Analysis** (Smart Model)

```json
{
  "fix_summary": "Replace the hardcoded password with environment variable
and secure loading method.",
  "security_impact": "Prevents credential exposure in source code
which could lead to unauthorized database access.",
  "suggested_code": "import os
DB_PASSWORD = os.getenv('DB_PASSWORD')",
  "explanation": "This is a detailed explanation
with multiple lines of text.",
  "prevention_tips": ["Use environment variables", "Regular audits"]
}
```'''

result = clean_and_parse_json(test_text)
print("Result:", result)
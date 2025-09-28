"""
Debug Gemini Response - See what Gemini actually returns
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_gemini_response():
    """Test what Gemini actually returns"""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found")
        return
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """
Analyze this user's app idea and create a detailed project plan: "A todo app with priority levels"

You need to determine:
1. The base app type (todo, chat, ecommerce, blog, dashboard, or custom)
2. What additional fields/features the user wants beyond the basic template
3. Custom UI requirements or special behaviors
4. Additional API endpoints needed

Respond with a JSON object following this structure:
{
    "app_type": "todo|chat|ecommerce|blog|dashboard|custom",
    "name": "extracted or generated app name",
    "description": "clean description of what this app does",
    "custom_features": [
        "list of features not in the base template"
    ],
    "additional_fields": [
        {
            "model": "model_name",
            "field_name": "field_name",
            "field_type": "python_type",
            "required": true,
            "description": "what this field does"
        }
    ],
    "ui_requirements": [
        "specific UI behaviors or components mentioned"
    ],
    "custom_logic": {
        "feature_name": "description of custom logic needed"
    }
}

Examples:
- "todo app with priority levels" -> add priority field to Task model
- "chat with file sharing" -> add file_url field to Message model
- "ecommerce with reviews" -> add Review model and rating field to Product

Focus on extracting SPECIFIC requirements from the user's idea, not generic features.
"""
    
    try:
        print("🤖 Sending request to Gemini...")
        response = model.generate_content(prompt)
        
        print("✅ Response received!")
        print("📄 Raw response:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        
        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(response.text)
            print("✅ JSON parsing successful!")
            print(f"App Type: {parsed.get('app_type')}")
            print(f"Name: {parsed.get('name')}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_gemini_response()
"""
Check available Gemini models
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def list_available_models():
    """List all available Gemini models"""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found")
        return
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    print("🔍 Available Gemini Models:")
    print("=" * 40)
    
    try:
        models = genai.list_models()
        for model in models:
            print(f"• {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                methods = [method for method in model.supported_generation_methods]
                print(f"  Supported methods: {methods}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_available_models()
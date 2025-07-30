import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# List all available models
print("\n=== Available Gemini Models ===")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"\nModel: {m.name}")
        print(f"Display name: {m.display_name}")
        print(f"Generation methods: {m.supported_generation_methods}")
        print("---")
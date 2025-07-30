import google.generativeai as genai
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Available models configuration
AVAILABLE_MODELS = {
    'fast': 'models/gemini-2.5-flash',
    'smart': 'models/gemini-2.5-pro'
}

# Initialize models dictionary
models = {}

# Initialize Gemini API
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set GOOGLE_API_KEY environment variable.")
    
    genai.configure(api_key=api_key)
    
    # Initialize both models
    for model_type, model_name in AVAILABLE_MODELS.items():
        try:
            models[model_type] = genai.GenerativeModel(model_name)
            print(f"✅ Initialized {model_type} model ({model_name})")
        except Exception as e:
            print(f"❌ Failed to initialize {model_type} model: {e}")
            
except Exception as e:
    print(f"❌ Error initializing Gemini API: {e}")

def get_model(model_type: str = 'fast') -> Optional[genai.GenerativeModel]:
    """Get the specified model instance."""
    return models.get(model_type)

def analyze_scan_with_llm(https: bool, flags: List[str], headers: Dict[str, str], model_type: str = 'fast') -> str:
    model = get_model(model_type)
    if model is None:
        return f"AI model ({model_type}) is not available"

    system_prompt = "You are a web security expert. Analyze these scan results and provide specific, actionable recommendations."
    user_prompt = f"""
    Security Scan Results:
    - HTTPS enabled: {https}
    - Missing/insecure headers: {flags}
    - Present headers: {headers}
    
    Please provide:
    1. Security posture analysis
    2. Specific improvement recommendations
    3. Example header configurations
    """

    try:
        response = model.generate_content(system_prompt + "\n\n" + user_prompt)
        return response.text.strip()
    except Exception as e:
        return f"API Error: {str(e)}"

def get_chat_response(history: List[Dict], model_type: str = 'fast') -> str:
    model = get_model(model_type)
    if model is None:
        return f"AI model ({model_type}) is not available"

    try:
        # Convert history to the format Gemini expects
        formatted_history = []
        for msg in history:
            if isinstance(msg.get('parts'), list):
                content = msg['parts'][0]
            else:
                content = msg.get('user') or msg.get('ai') or msg.get('content', '')
            
            formatted_history.append({
                'parts': [{'text': content}],
                'role': 'user' if msg.get('type') == 'user' else 'model'
            })

        # Create chat session with formatted history
        chat = model.start_chat(history=formatted_history)
        
        # Get the last user message
        last_message = history[-1]['parts'][0] if isinstance(history[-1].get('parts'), list) else history[-1].get('content', '')
        
        # Send message and get response
        response = chat.send_message(last_message)
        return response.text.strip()
    except Exception as e:
        return f"Chat Error: {str(e)}"
"""
🤖 Google Gemini Setup Guide for AI-Enhanced Code Generation

QUICK START GUIDE
================================================================================

1. GET GEMINI API KEY
   • Visit: https://makersuite.google.com/app/apikey
   • Click "Create API Key"  
   • Copy your API key

2. SET ENVIRONMENT VARIABLE
   # Windows (PowerShell)
   $env:GOOGLE_API_KEY="your_gemini_api_key_here"
   
   # Windows (Command Prompt)
   set GOOGLE_API_KEY=your_gemini_api_key_here
   
   # Linux/Mac
   export GOOGLE_API_KEY=your_gemini_api_key_here

3. INSTALL DEPENDENCIES
   pip install google-generativeai>=0.3.0

4. TEST INTEGRATION
   python test_gemini_integration.py

DETAILED SETUP
================================================================================

📦 DEPENDENCIES
Update your requirements.txt:
```
google-generativeai==0.3.0
python-dotenv==1.0.0
```

🔧 ENVIRONMENT CONFIGURATION  
Create or update .env file:
```
GOOGLE_API_KEY=your_gemini_api_key_here
AI_GENERATION_ENABLED=true
AI_MODEL=gemini-1.5-flash
MAX_AI_COST_PER_PROJECT=0.10
```

💰 COST COMPARISON: GEMINI vs OPENAI
================================================================================

GOOGLE GEMINI:
• Cost per 1K tokens: $0.00015 (input), $0.0006 (output)
• Average cost per project: $0.05 - $0.15
• Rate limits: 60 requests per minute
• Context window: 128K tokens
• Speed: Very fast responses

OPENAI GPT-4:
• Cost per 1K tokens: $0.03 (input), $0.06 (output) 
• Average cost per project: $0.50 - $1.50
• Rate limits: Varies by tier
• Context window: 128K tokens
• Speed: Moderate responses

GEMINI ADVANTAGES:
✅ 10-20x cheaper than OpenAI
✅ Faster response times
✅ Generous free tier (1500 requests/day)
✅ Google's latest AI technology
✅ Built-in safety features

🔄 MIGRATION FROM OPENAI TO GEMINI
================================================================================

OLD (OpenAI):
```python
import openai
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = await client.chat.completions.acreate(
    model="gpt-4o-mini", 
    messages=[{"role": "user", "content": prompt}]
)
result = response.choices[0].message.content
```

NEW (Gemini):
```python
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
client = genai.GenerativeModel('gemini-1.5-flash')
response = client.generate_content(prompt)
result = response.text
```

🚀 USAGE EXAMPLES
================================================================================

BASIC AI ANALYSIS:
```python
from ai_enhanced_generator import AIEnhancedGenerator

generator = AIEnhancedGenerator()
plan = await generator.analyze_user_idea("A todo app with priority levels")
print(f"Detected features: {plan.features}")
```

FULL PROJECT GENERATION:
```python
files = await generator.generate_project(
    Path("./my_project"),
    "A chat app with file sharing and emoji reactions", 
    "Team Chat Pro"
)
print(f"Generated {len(files)} files")
```

🎯 GEMINI-SPECIFIC OPTIMIZATIONS
================================================================================

PROMPT ENGINEERING:
• Gemini responds well to structured JSON requests
• Use clear examples in prompts
• Be specific about output format requirements
• Include safety instructions for code generation

PERFORMANCE TIPS:
• Use gemini-1.5-flash for fast, cost-effective generation
• Use gemini-1.5-pro for complex analysis tasks  
• Cache responses for similar requests
• Batch multiple small requests when possible

ERROR HANDLING:
• Handle rate limits gracefully
• Implement automatic retry with exponential backoff
• Always have template fallback for reliability
• Monitor API usage and costs

🛠️ INTEGRATION WITH EXISTING SYSTEM
================================================================================

UPDATE main.py:
```python
@app.post("/create-project")
async def create_complete_project_structure(
    idea: str, 
    project_name: str,
    use_ai: bool = True
):
    if use_ai and os.getenv("GOOGLE_API_KEY"):
        # Use Gemini AI generation
        generator = AIEnhancedGenerator()
        result = await generator.generate_project(...)
        return {"method": "gemini-enhanced", "files": result}
    else:
        # Fallback to templates
        generator = ModernProjectGenerator() 
        result = await generator.generate_project(...)
        return {"method": "template-based", "files": result}
```

📊 MONITORING & ANALYTICS
================================================================================

TRACK AI USAGE:
```python
import time
start_time = time.time()
plan = await generator.analyze_user_idea(idea)
duration = time.time() - start_time

# Log metrics
logger.info({
    "ai_provider": "gemini",
    "response_time": duration,
    "tokens_used": len(prompt) + len(response.text),
    "success": True
})
```

COST MONITORING:
• Track API calls per day/month
• Monitor token usage patterns  
• Set up alerts for unusual spending
• Use free tier limits effectively

🔒 SECURITY & BEST PRACTICES
================================================================================

API KEY SECURITY:
• Never commit API keys to version control
• Use environment variables or secure vaults
• Rotate keys regularly
• Restrict API key permissions

CODE SAFETY:
• Validate all AI-generated code
• Maintain array safety patterns
• Include error handling in generated code
• Test generated applications thoroughly

RATE LIMITING:
• Implement client-side rate limiting
• Use exponential backoff for retries
• Queue requests during high traffic
• Cache responses to reduce API calls

🎉 READY TO USE GEMINI!
================================================================================

Your AI-enhanced generator is now configured for Google Gemini:

✅ 10-20x more cost effective than OpenAI
✅ Faster response times  
✅ Same high-quality code generation
✅ Reliable fallback to templates
✅ Production-ready error handling

Next steps:
1. Get your Gemini API key
2. Run the test script
3. Update your main.py integration
4. Deploy with confidence!
"""

def show_setup_status():
    """Show current setup status"""
    import os
    
    print("🔍 Current Setup Status")
    print("=" * 30)
    
    # Check API key
    if os.getenv("GOOGLE_API_KEY"):
        print("✅ GOOGLE_API_KEY found in environment")
    else:
        print("❌ GOOGLE_API_KEY not set")
        print("   Set with: set GOOGLE_API_KEY=your_key_here")
    
    # Check packages
    try:
        import google.generativeai
        print("✅ google-generativeai package installed")
    except ImportError:
        print("❌ google-generativeai not installed")
        print("   Install with: pip install google-generativeai")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv package installed")
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Install with: pip install python-dotenv")
    
    # Check files
    from pathlib import Path
    files_to_check = [
        "ai_enhanced_generator.py",
        "test_gemini_integration.py"
    ]
    
    for file in files_to_check:
        if Path(file).exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")

if __name__ == "__main__":
    print(__doc__)
    show_setup_status()
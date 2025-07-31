from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from starlette.concurrency import run_in_threadpool
from ai_assistant import analyze_github_repo, get_chat_response, RepoAnalysis
from scanner import scan_url
from crawler import crawl_site
from nlp_suggester import suggest_fixes
import ai_assistant

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Models ---
class ScanRequest(BaseModel):
    url: str
    model_type: str = 'fast'

class ChatRequest(BaseModel):
    history: List[Dict]
    model_type: str = 'fast'

class AIChatRequest(BaseModel):
    question: str
    context: str = 'general'

class RepoAnalysisRequest(BaseModel):
    repo_url: str
    model_type: str = 'smart'

# --- Endpoints ---
@app.post("/scan")
async def scan(request: ScanRequest):
    """Scan a website for security vulnerabilities"""
    url = request.url
    
    pages = await run_in_threadpool(crawl_site, url)
    scan_result = await run_in_threadpool(scan_url, url)
    suggestions = await run_in_threadpool(suggest_fixes, scan_result['headers'])
    ai_advice = await run_in_threadpool(
        ai_assistant.analyze_scan_with_llm,
        scan_result["https"],
        scan_result["flags"],
        scan_result["headers"],
        request.model_type
    )
    
    # Create a summary for the chatbot
    summary = f"""🔒 **Security Scan Complete**

📊 **Scan Results Summary:**
• Target: {url}
• HTTPS: {'✅ Enabled' if scan_result["https"] else '❌ Disabled'}
• Vulnerabilities: {len(scan_result["flags"])} issues found
• Pages Crawled: {len(pages)} pages
• Security Headers: {len(scan_result["headers"])} detected

🚨 **Key Issues Found:**
{chr(10).join([f'• {flag}' for flag in scan_result["flags"][:5]]) if scan_result["flags"] else '• No critical issues detected'}

💡 **Ready to help with specific security questions about this scan!**"""
    
    return {
        "url": url,
        "pages": pages,
        "scan_result": scan_result,
        "suggestions": suggestions,
        "ai_assistant_advice": ai_advice,
        "summary": summary
    }

@app.post("/analyze-repo")
async def analyze_repo(request: RepoAnalysisRequest):
    """Analyze a GitHub repository for security issues"""
    analysis = await run_in_threadpool(
        analyze_github_repo,
        request.repo_url,
        request.model_type
    )
    
    # Create a summary if repository analysis was successful
    summary = ""
    if RepoAnalysis.latest_analysis:
        repo_info = RepoAnalysis.latest_analysis
        summary = f"""📂 **Repository Analysis Complete**

🔍 **Repository Summary:**
• Name: {repo_info.repo_name}
• Language: {repo_info.language}
• Files Scanned: {len(repo_info.files_scanned)}
• Open Issues: {repo_info.open_issues}

🛡️ **Security Findings:**
{chr(10).join([f'• {finding}' for finding in repo_info.security_findings[:5]]) if repo_info.security_findings else '• No security issues detected'}

💬 **Ask me specific questions about this repository's security!**"""
    
    return {
        "analysis": analysis,
        "summary": summary
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat about security analysis results"""
    try:
        # Validate request has history
        if not request.history or len(request.history) == 0:
            raise HTTPException(
                status_code=400,
                detail="No conversation history provided"
            )
        
        # Check the last message format and extract text safely
        last_msg = request.history[-1]
        message_text = ""
        
        if 'parts' in last_msg and isinstance(last_msg['parts'], list) and len(last_msg['parts']) > 0:
            if isinstance(last_msg['parts'][0], dict):
                message_text = last_msg['parts'][0].get('text', '').lower()
            else:
                message_text = str(last_msg['parts'][0]).lower()
        elif 'message' in last_msg:
            message_text = last_msg['message'].lower()
        
        # Check if trying to discuss repository without analysis
        if not RepoAnalysis.latest_analysis and any(
            word in message_text 
            for word in ['repository', 'repo', 'github']
        ):
            return {
                "reply": "I don't have any repository analysis data yet. Please analyze a repository first using the Deploy page, then I can help you with specific questions about the security findings."
            }
        
        response = await run_in_threadpool(
            get_chat_response,
            request.history,
            request.model_type
        )
        return {"reply": response}
        
    except Exception as e:
        print(f"Chat endpoint error: {str(e)}")
        return {"reply": "I'm having trouble processing your request. Please try again."}

@app.post("/ai-chat")
async def ai_chat(request: AIChatRequest):
    """AI chat endpoint for frontend integration"""
    try:
        # Convert the simple question format to the expected history format
        history = [
            {
                "role": "user",
                "parts": [{"text": request.question}]
            }
        ]
        
        response = await run_in_threadpool(
            get_chat_response,
            history,
            'fast'  # Use fast model for chat
        )
        
        return {"response": response}
        
    except Exception as e:
        print(f"AI Chat endpoint error: {str(e)}")
        return {"response": "I'm here to help with security questions. Could you please rephrase your question?"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}
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
    
    # Create enhanced summary with better formatting
    security_level = scan_result.get("security_level", "Unknown")
    security_score = scan_result.get("security_score", 0)
    
    summary = f"""🔒 **Security Scan Complete**

📊 **Scan Results Summary:**
• Target: {url}
• Security Score: {security_score}/100 ({security_level})
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
    # Check if trying to discuss repository without analysis
    if not RepoAnalysis.latest_analysis and any(
        word in request.history[-1]['parts'][0].lower() 
        for word in ['repository', 'repo', 'github']
    ):
        raise HTTPException(
            status_code=400,
            detail="Please analyze a repository first using /analyze-repo endpoint"
        )
    
    response = await run_in_threadpool(
        get_chat_response,
        request.history,
        request.model_type
    )
    return {"reply": response}

@app.post("/ai-chat")
async def ai_chat(request: dict):
    """Enhanced AI chat endpoint with better context handling"""
    try:
        question = request.get('question', '')
        context = request.get('context', 'general')
        scan_result = request.get('scan_result', None)
        
        # Create enhanced context based on the type of question
        enhanced_context = f"""
**CONTEXT:** {context}
**USER QUESTION:** {question}

**AVAILABLE INFORMATION:**
"""
        
        if scan_result:
            enhanced_context += f"""
**SCAN RESULTS:**
• Target URL: {scan_result.get('url', 'N/A')}
• HTTPS Status: {'✅ Enabled' if scan_result.get('https', False) else '❌ Disabled'}
• Security Headers: {len(scan_result.get('headers', {}))} detected
• Vulnerabilities Found: {len(scan_result.get('flags', []))} issues
• Security Score: {scan_result.get('security_score', 'N/A')}/100

**SPECIFIC ISSUES:**
{chr(10).join([f'• {flag}' for flag in scan_result.get('flags', [])]) if scan_result.get('flags') else '• No specific issues detected'}
"""
        
        # Create history for the AI
        history = [{
            'type': 'user',
            'parts': [enhanced_context + f"\n\nPlease provide a helpful, user-friendly response to: {question}"]
        }]
        
        response = await run_in_threadpool(
            get_chat_response,
            history,
            request.get('model_type', 'fast')
        )
        
        return {"response": response}
        
    except Exception as e:
        return {"response": f"❌ **Error processing your question:** {str(e)}\n\nPlease try rephrasing your question or contact support if the issue persists."}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}
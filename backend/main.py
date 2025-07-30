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
    
    return {
        "url": url,
        "pages": pages,
        "scan_result": scan_result,
        "suggestions": suggestions,
        "ai_assistant_advice": ai_advice
    }

@app.post("/analyze-repo")
async def analyze_repo(request: RepoAnalysisRequest):
    """Analyze a GitHub repository for security issues"""
    analysis = await run_in_threadpool(
        analyze_github_repo,
        request.repo_url,
        request.model_type
    )
    return {"analysis": analysis}

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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}
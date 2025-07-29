# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool  # <-- IMPORT THIS
from pydantic import BaseModel
from typing import List, Dict

# Your other imports
from scanner import scan_url
from crawler import crawl_site
from nlp_suggester import suggest_fixes
from ai_assistant import analyze_scan_with_llm, get_chat_response

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    history: List[Dict]

@app.post("/scan")
async def scan(request: ScanRequest):
    url = request.url
    
    # MODIFIED: Run each blocking function in a thread pool
    # This prevents your server from freezing while waiting for network requests
    pages = await run_in_threadpool(crawl_site, url)
    scan_result = await run_in_threadpool(scan_url, url)
    suggestions = await run_in_threadpool(suggest_fixes, scan_result['headers'])
    ai_advice = await run_in_threadpool(
        analyze_scan_with_llm,
        scan_result["https"],
        scan_result["flags"],
        scan_result["headers"]
    )

    return {
        "https": scan_result['https'],
        "headers": scan_result['headers'],
        "suggestions": suggestions,
        "crawled_pages": pages,
        "ai_assistant_advice": ai_advice,
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    This endpoint handles follow-up questions from the user.
    """
    # MODIFIED: The AI call is also blocking, so run it in a thread pool
    reply = await run_in_threadpool(get_chat_response, request.history)
    return {"reply": reply}
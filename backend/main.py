from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from starlette.concurrency import run_in_threadpool
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

class ChatRequest(BaseModel):
    history: List[Dict]
    model_type: str = 'fast'  # default to fast model

class ScanRequest(BaseModel):
    url: str
    model_type: str = 'fast'  # default to fast model
@app.post("/scan")
async def scan(request: ScanRequest):
    url = request.url
    
    pages = await run_in_threadpool(crawl_site, url)
    scan_result = await run_in_threadpool(scan_url, url)
    suggestions = await run_in_threadpool(suggest_fixes, scan_result['headers'])
    ai_advice = await run_in_threadpool(
        analyze_scan_with_llm,
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

@app.post("/chat")
async def chat(request: ChatRequest):
    response = await run_in_threadpool(
        get_chat_response,
        request.history,
        request.model_type
    )
    return {"reply": response}


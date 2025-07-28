from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from scanner import scan_url
from crawler import crawl_site
from nlp_suggester import suggest_fixes

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

@app.post("/scan")
async def scan(request: ScanRequest):
    url = request.url
    pages = crawl_site(url)
    scan_result = scan_url(url)
    suggestions = suggest_fixes(scan_result['headers'])

    return {
        "https": scan_result['https'],
        "headers": scan_result['headers'],
        "suggestions": suggestions,
        "crawled_pages": pages
    }

from fastapi import FastAPI
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    url: str

@app.post("/scan")
async def scan_website(data: ScanRequest):
    
    try:
        url=data.url
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5)
            headers = response.headers

            result = {
                "https": url.startswith("https"),
                "headers": {
                    "content-security-policy": "present" if "content-security-policy" in headers else "missing",
                    "x-powered-by": headers.get("x-powered-by", "missing"),
                    "strict-transport-security": "present" if "strict-transport-security" in headers else "missing"
                },
                "suggestions": []
            }

            if "x-powered-by" in headers:
                result["suggestions"].append("Remove 'X-Powered-By' header to hide backend.")
            if "content-security-policy" not in headers:
                result["suggestions"].append("Add a CSP header to mitigate XSS.")
            if "strict-transport-security" not in headers:
                result["suggestions"].append("Add HSTS header to force HTTPS.")
            if "content-security-policy-report-only" in headers:
                result["suggestions"].append("Upgrade to CSP report only to enforcement mode.")

            return result
    except Exception:
        return {"error": "Could not scan site. Try a valid URL."}


    
import requests

def scan_url(url):
    result = {
    "https": url.startswith("https"),
    "headers": {},
    "flags": [],
    }
    try:
        res = requests.get(url, timeout=5)
        headers = res.headers
        result["headers"] = dict(headers)

        # Basic header checks
        if "Content-Security-Policy" not in headers:
            result["flags"].append("Missing Content-Security-Policy header")
        if "Strict-Transport-Security" not in headers:
            result["flags"].append("Missing Strict-Transport-Security header")
        if "X-Frame-Options" not in headers:
            result["flags"].append("Missing X-Frame-Options header")
        if "X-XSS-Protection" not in headers:
            result["flags"].append("Missing X-XSS-Protection header")
        if "X-Content-Type-Options" not in headers:
            result["flags"].append("Missing X-Content-Type-Options header")
        if "Referrer-Policy" not in headers:
            result["flags"].append("Missing Referrer-Policy header")
        if not result["https"]:
            result["flags"].append("Website does not use HTTPS")
    except Exception as e:
        result["flags"].append(f"Request failed: {e}")

    return result

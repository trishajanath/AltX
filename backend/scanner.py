import requests

def scan_url(url):
    try:
        res = requests.get(url, timeout=5)
        headers = res.headers
        https = url.startswith("https://")
        return {"headers": headers, "https": https}
    except:
        return {"headers": {}, "https": False}

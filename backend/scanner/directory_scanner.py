# scanner/directory_scanner.py

import httpx
from typing import List

# A list of common paths to check for
COMMON_PATHS = [
    "/admin", "/login", "/dashboard", "/admin/login", "/wp-admin",
    "/administrator", "/panel", "/user/login", "/auth", "/api",
    "/.git/config", "/.env", "/backup", "/config"
]

async def scan_common_paths(url: str) -> List[dict]:
    """
    Scans a website for common, accessible administrative or sensitive paths.
    """
    found_paths = []
    # Ensure the base URL doesn't have a trailing slash
    base_url = url.rstrip('/')

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for path in COMMON_PATHS:
            try:
                target_url = base_url + path
                response = await client.get(target_url)
                
                # A 200 OK status means the page is accessible
                # We also check that it's not a generic redirect to the homepage
                if response.status_code == 200 and len(response.content) > 200:
                    print(f"✅ Found accessible path: {target_url}")
                    found_paths.append({
                        "path": path,
                        "status_code": response.status_code,
                        "url": target_url
                    })

            except httpx.RequestError as e:
                # Ignore connection errors for specific paths
                print(f"⚠️  Could not connect to {target_url}: {e}")
                continue
    
    return found_paths
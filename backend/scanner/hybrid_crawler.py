# scanner/hybrid_crawler.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from typing import List, Set

# --- Helper Function 1: Your existing static crawler ---
def _crawl_static(url: str, session: requests.Session) -> List[str]:
    """
    Performs a simple, fast crawl using requests.
    Returns a list of found URLs on the same domain.
    """
    found_urls = []
    try:
        response = session.get(url, timeout=5)
        response.raise_for_status() # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_netloc = urlparse(url).netloc

        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get('href')
            full_url = urljoin(url, href).split('#')[0] # Clean URL
            
            # Stay on the same domain
            if urlparse(full_url).netloc == base_netloc:
                found_urls.append(full_url)
    except requests.RequestException as e:
        print(f"Static crawl failed for {url}: {e}")
    
    return found_urls


# --- Helper Function 2: The Playwright crawler ---
async def _crawl_dynamic(url: str) -> List[str]:
    """
    Performs an advanced crawl using a headless browser.
    """
    found_urls: Set[str] = set()
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(4000) # Wait 4 seconds for JS to load

            hrefs = await page.eval_on_selector_all("a", "elements => elements.map(el => el.href)")
            
            base_netloc = urlparse(url).netloc
            for href in hrefs:
                full_url = urljoin(url, href).split('#')[0]
                if urlparse(full_url).netloc == base_netloc:
                    found_urls.add(full_url)
            
            await browser.close()
        except Exception as e:
            print(f"Dynamic crawl failed for {url}: {e}")

    return list(found_urls)


# --- Main Hybrid Function ---
async def crawl_hybrid(start_url: str, max_pages: int = 10) -> List[str]:
    """
    Crawls a website using a hybrid approach, switching to a headless browser
    if the initial static crawl finds few links.
    """
    print(f"🚀 Starting hybrid crawl for {start_url}")
    
    # Use a session for performance
    session = requests.Session()
    session.headers.update({'User-Agent': 'SecurityCrawler/1.0'})

    # First, try the fast static crawl on the starting URL
    initial_links = _crawl_static(start_url, session)
    
    # Heuristic: If we find fewer than 3 links, it's likely an SPA.
    # Switch to the dynamic, headless browser crawler.
    if len(initial_links) < 3:
        print("⚠️ Static crawl found few links. Switching to dynamic (headless browser) mode.")
        dynamic_links = await _crawl_dynamic(start_url)
        return list(set([start_url] + dynamic_links))[:max_pages]

    # Otherwise, proceed with the fast static crawl
    print("✅ Static crawl successful. Proceeding with fast mode.")
    visited = {start_url}
    to_visit = initial_links

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        
        new_links = _crawl_static(url, session)
        visited.add(url)
        
        for link in new_links:
            if link not in visited:
                to_visit.append(link)

    return list(visited)
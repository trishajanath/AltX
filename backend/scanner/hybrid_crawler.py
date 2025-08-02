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
    Performs an advanced crawl using a headless browser with enhanced error handling.
    """
    found_urls: Set[str] = set()
    
    try:
        async with async_playwright() as p:
            try:
                # Try different browser engines if available
                browser = None
                for browser_type in [p.chromium, p.firefox, p.webkit]:
                    try:
                        browser = await browser_type.launch(
                            headless=True,
                            args=['--no-sandbox', '--disable-dev-shm-usage'] if browser_type == p.chromium else []
                        )
                        print(f"✅ Successfully launched {browser_type.name} browser")
                        break
                    except Exception as browser_error:
                        print(f"⚠️ Failed to launch {browser_type.name}: {browser_error}")
                        continue
                
                if not browser:
                    raise Exception("All browser engines failed to launch")
                
                page = await browser.new_page()
                
                # Set a reasonable timeout and user agent
                page.set_default_timeout(10000)
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)  # Reduced wait time

                # Extract links with error handling
                try:
                    hrefs = await page.evaluate("""
                        () => {
                            const links = Array.from(document.querySelectorAll('a[href]'));
                            return links.map(link => link.href).filter(href => href && href.trim() !== '');
                        }
                    """)
                except Exception as eval_error:
                    print(f"⚠️ JavaScript evaluation failed: {eval_error}")
                    hrefs = []
                
                base_netloc = urlparse(url).netloc
                for href in hrefs:
                    try:
                        full_url = urljoin(url, href).split('#')[0]
                        if urlparse(full_url).netloc == base_netloc:
                            found_urls.add(full_url)
                    except Exception:
                        continue
                
                await browser.close()
                
            except Exception as browser_error:
                print(f"⚠️ Browser operation failed: {browser_error}")
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                        
    except Exception as playwright_error:
        print(f"⚠️ Playwright initialization failed: {playwright_error}")
        print("💡 This might be due to missing browser binaries. Try running: playwright install")
        
        # Fallback to static crawling if Playwright fails
        print("🔄 Falling back to enhanced static crawling...")
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Try to get more links through static analysis
        try:
            response = session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            base_netloc = urlparse(url).netloc
            
            # Look for various link patterns
            link_selectors = ['a[href]', 'link[href]', '[data-href]']
            for selector in link_selectors:
                for element in soup.select(selector):
                    href = element.get('href') or element.get('data-href')
                    if href:
                        try:
                            full_url = urljoin(url, href).split('#')[0]
                            if urlparse(full_url).netloc == base_netloc:
                                found_urls.add(full_url)
                        except:
                            continue
                            
        except Exception as fallback_error:
            print(f"⚠️ Fallback static crawl also failed: {fallback_error}")

    return list(found_urls)


# --- Main Hybrid Function ---
async def crawl_hybrid(start_url: str, max_pages: int = 10) -> List[str]:
    """
    Crawls a website using a hybrid approach, switching to a headless browser
    if the initial static crawl finds few links. Enhanced with better error handling.
    """
    print(f"🚀 Starting hybrid crawl for {start_url}")
    
    # Use a session for performance
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    # First, try the fast static crawl on the starting URL
    initial_links = _crawl_static(start_url, session)
    
    # Heuristic: If we find fewer than 3 links, it's likely an SPA.
    # Switch to the dynamic, headless browser crawler.
    if len(initial_links) < 3:
        print("⚠️ Static crawl found few links. Switching to dynamic (headless browser) mode.")
        try:
            dynamic_links = await _crawl_dynamic(start_url)
            if dynamic_links:
                print(f"✅ Dynamic crawl found {len(dynamic_links)} links")
                return list(set([start_url] + dynamic_links))[:max_pages]
            else:
                print("⚠️ Dynamic crawl returned no additional links")
        except Exception as dynamic_error:
            print(f"❌ Dynamic crawl completely failed: {dynamic_error}")
        
        # If dynamic crawl fails, return what we have from static crawl
        print("🔄 Returning static crawl results as fallback")
        return list(set([start_url] + initial_links))[:max_pages]

    # Otherwise, proceed with the fast static crawl
    print("✅ Static crawl successful. Proceeding with fast mode.")
    visited = {start_url}
    to_visit = initial_links.copy()

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        
        try:
            new_links = _crawl_static(url, session)
            visited.add(url)
            
            for link in new_links:
                if link not in visited and link not in to_visit:
                    to_visit.append(link)
        except Exception as crawl_error:
            print(f"⚠️ Failed to crawl {url}: {crawl_error}")
            visited.add(url)  # Mark as visited to avoid retry
            continue

    print(f"✅ Crawl completed. Found {len(visited)} unique pages")
    return list(visited)[:max_pages]
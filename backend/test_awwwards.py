"""Test Awwwards scraping with the correct URL"""
import requests
from bs4 import BeautifulSoup

url = 'https://www.awwwards.com/websites/sites_of_the_day/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

print(f"Testing URL: {url}")
response = requests.get(url, headers=headers, timeout=15)
print(f'Status: {response.status_code}')
print(f'Content length: {len(response.content)} bytes')

# Check if we got actual content
if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('title')
    print(f'Title: {title.text if title else "No title"}')
    
    # Look for site items - various selectors
    site_items = soup.find_all('li', class_='js-collectable')
    print(f'Found {len(site_items)} js-collectable items')
    
    # Look for other content divs
    articles = soup.find_all('article')
    print(f'Found {len(articles)} articles')
    
    # Look for cards or project elements
    cards = soup.find_all(class_='box-item')
    print(f'Found {len(cards)} box-item elements')
    
    # Look for figure elements (common for showcases)
    figures = soup.find_all('figure')
    print(f'Found {len(figures)} figures')
    
    # Look for any divs with 'site' or 'project' in class
    site_divs = soup.find_all(lambda tag: tag.name == 'div' and tag.get('class') and any('site' in c.lower() or 'project' in c.lower() for c in tag.get('class', [])))
    print(f'Found {len(site_divs)} site/project divs')
    
    # Print first 500 chars of body to understand structure
    body = soup.find('body')
    if body:
        print("\n=== BODY PREVIEW (first 1000 chars) ===")
        print(str(body)[:1000])
else:
    print(f"Failed to fetch: HTTP {response.status_code}")

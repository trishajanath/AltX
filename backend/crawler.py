import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def crawl_site(start_url, max_pages=5):
    visited = set()
    to_visit = [start_url]

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True)]

            for link in links:
                full_link = urljoin(url, link)
                if full_link.startswith(start_url):
                    to_visit.append(full_link)
        except:
            continue

    return list(visited)

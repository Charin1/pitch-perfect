# From: backend/app/services/crawler.py
# ----------------------------------------
import asyncio
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings

# --- Configuration ---
MAX_PAGES_TO_CRAWL = 25 # Increased slightly to improve chances of finding blogs
TEAM_PAGE_KEYWORDS = ["about", "team", "leadership", "management", "who-we-are", "board", "executive"]
BLOG_NEWS_KEYWORDS = ["blog", "news", "insights", "resources", "press", "article", "publication"]

async def crawl_website(initial_url: str) -> tuple[list[dict], list[str]]:
    """
    Performs a breadth-first crawl of a website up to configured limits.
    Returns a tuple containing:
    - A list of dictionaries, each with the URL and HTML of a crawled page.
    - A list of all successfully crawled URLs for logging purposes.
    """
    headers = {"User-Agent": "PitchPerfectBot/1.0"}
    async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
        queue = [(initial_url, 0)]
        visited_urls = set()
        crawled_pages = []
        successfully_crawled_urls = []
        base_domain = urlparse(initial_url).netloc

        while queue and len(crawled_pages) < settings.CRAWLER_MAX_PAGES:
            url, depth = queue.pop(0)
            if url in visited_urls or depth > settings.CRAWLER_MAX_DEPTH:
                continue

            print(f"Crawling (Depth: {depth}): {url}")
            visited_urls.add(url)

            try:
                response = await client.get(url)
                response.raise_for_status()
                crawled_pages.append({"url": url, "html": response.text})
                successfully_crawled_urls.append(url)

                if depth < settings.CRAWLER_MAX_DEPTH:
                    soup = BeautifulSoup(response.text, "html.parser")
                    for a_tag in soup.find_all("a", href=True):
                        link = urljoin(url, a_tag['href'])
                        if urlparse(link).netloc == base_domain and link not in visited_urls:
                            queue.append((link, depth + 1))
            
            except Exception as e:
                print(f"Failed to crawl {url}: {e}")

        return crawled_pages, successfully_crawled_urls
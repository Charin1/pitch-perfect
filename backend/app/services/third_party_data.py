# From: backend/app/services/third_party_data.py
# ----------------------------------------
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus, parse_qs
from app.core.config import GROWTH_DATA_SOURCES_LIST

async def _fetch_and_parse_url(url: str, client: httpx.AsyncClient) -> str | None:
    """Helper function to fetch a single URL and parse its text."""
    print(f"    - Reading content from: {url}")
    try:
        response = await client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        page_text = soup.get_text(separator=' ', strip=True)
        return f"--- Data from {urlparse(url).netloc} ---\n{page_text[:2000]}\n\n"
    except Exception as e:
        print(f"    - Failed to read content from {url}: {e}")
        return None

async def _search_and_fetch_top_result(search_template: str, company_name: str, client: httpx.AsyncClient) -> str | None:
    """
    Performs a Google search, finds the top result link, and fetches its content.
    """
    search_url = f"{search_template}+{quote_plus(company_name)}"
    print(f"  -> Searching: {search_url}")
    
    try:
        # 1. Search Google
        search_response = await client.get(search_url)
        search_response.raise_for_status()
        soup = BeautifulSoup(search_response.text, "html.parser")

        # 2. Find the top result link. This is brittle and may need adjustment.
        # We look for the first link inside a div that Google often uses for organic results.
        top_result_link = None
        for link in soup.select("div.g a"): # A common selector for Google results
            href = link.get('href')
            if href and href.startswith('/url?q='):
                # Extract the actual URL from Google's redirect link
                top_result_link = parse_qs(urlparse(href).query).get('q', [None])[0]
                if top_result_link:
                    break
        
        if not top_result_link:
            print("    - Could not find a valid result link on the search page.")
            return None

        # 3. Click & Read: Fetch the content from the found link
        return await _fetch_and_parse_url(top_result_link, client)

    except Exception as e:
        print(f"  -> Failed during search for {company_name}: {e}")
        return None

async def fetch_growth_data(company_name: str) -> str:
    """
    Performs targeted searches for financial/growth data by finding and
    reading the top search result for each data source.
    """
    print(f"Fetching third-party growth data for: {company_name}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    async with httpx.AsyncClient(timeout=25, headers=headers, follow_redirects=True) as client:
        tasks = []
        for url_template in GROWTH_DATA_SOURCES_LIST:
            tasks.append(_search_and_fetch_top_result(url_template, company_name, client))

        results = await asyncio.gather(*tasks)
        consolidated_text = "".join([text for text in results if text])

    if not consolidated_text:
        return "Could not retrieve any third-party growth data. The search may have been blocked or returned no relevant results."
        
    return consolidated_text
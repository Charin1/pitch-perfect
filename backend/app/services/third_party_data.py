# From: backend/app/services/third_party_data.py
# ----------------------------------------
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus

# --- THIS IS THE NEW, MORE RELIABLE CONFIGURATION ---
# We will now construct the URLs directly.
GROWTH_DATA_SOURCES = {
    "crunchbase": "https://www.crunchbase.com/organization/{company_name}",
    "growjo": "https://www.growjo.com/company/{company_name}",
    "owler": "https://www.owler.com/company/{company_name}",
    "yahoo_finance": "https://finance.yahoo.com/quote/{company_name}"
}

async def _fetch_and_parse_url(url: str, client: httpx.AsyncClient) -> str | None:
    """Helper function to fetch a single URL and parse its text."""
    print(f"  -> Fetching: {url}")
    try:
        response = await client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        page_text = soup.get_text(separator=' ', strip=True)
        return f"--- Data from {urlparse(url).netloc} ---\n{page_text[:2500]}\n\n"
    except Exception as e:
        print(f"  -> Failed to fetch {url}: {e}")
        return None

async def fetch_growth_data(company_name: str) -> str:
    """
    Performs targeted fetches for financial/growth data by constructing
    direct URLs to third-party data providers.
    """
    print(f"Fetching third-party growth data for: {company_name}")
    
    url_friendly_name = company_name.lower().replace(' ', '-').replace('.', '')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    async with httpx.AsyncClient(timeout=25, headers=headers, follow_redirects=True) as client:
        tasks = []
        for source, url_template in GROWTH_DATA_SOURCES.items():
            final_url = url_template.format(company_name=url_friendly_name)
            tasks.append(_fetch_and_parse_url(final_url, client))

        results = await asyncio.gather(*tasks)
        consolidated_text = "".join([text for text in results if text])

    if not consolidated_text:
        return "Could not retrieve any third-party growth data. The target sites may be blocking automated requests or the company may not be listed."
        
    return consolidated_text
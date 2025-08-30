import httpx
from bs4 import BeautifulSoup

async def fetch_html(url: str, timeout: int = 15) -> str | None:
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent":"PitchPerfectBot/1.0"}) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

async def extract_text(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name":"description"})
    desc = desc_tag["content"] if desc_tag and desc_tag.get("content") else ""
    
    # Get text from main content areas, fall back to body
    main_content = soup.find("main") or soup.find("article") or soup.body
    body_text = " ".join(p.get_text(strip=True) for p in main_content.find_all("p", limit=30))
    
    return {"title": title, "description": desc, "body": body_text}

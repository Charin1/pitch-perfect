# From: backend/app/workers/tasks.py
# ----------------------------------------
import asyncio
import json
import logging
from celery import Celery
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from app.core.config import settings
from app.db.base import SessionLocal
from app.db.models import Lead, Pitch, LeadStatus
from app.services.crawler import crawl_website, BLOG_NEWS_KEYWORDS, TEAM_PAGE_KEYWORDS
from app.services.generative_ai import ai_service

logger = logging.getLogger(__name__)
celery = Celery("workers", broker=settings.REDIS_URL)

# We can remove the keyword lists from here as they are now imported from the crawler service

def run_async(func):
    return asyncio.run(func)

@celery.task
def process_lead_website(lead_id: int, url: str):
    db: Session = SessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        db.close()
        return

    try:
        lead.status = LeadStatus.CRAWLING
        db.commit()
        
        crawled_pages, crawled_urls = run_async(crawl_website(url))
        
        # ... (Logging block is the same) ...

        if not crawled_pages:
            raise ValueError("Crawling failed.")

        # --- Step 2: Intelligent Text Selection (Now with Blog/News) ---
        general_text, team_text, blog_news_text = _select_and_prioritize_text(crawled_pages)

        lead.status = LeadStatus.ANALYZING
        db.commit()

        # --- Step 3: The Final, Comprehensive AI Prompt ---
        analysis_prompt = _create_analysis_prompt(general_text, team_text, blog_news_text)
        
        analysis_result_str = run_async(ai_service.generate_text(analysis_prompt))
        
        clean_json_str = analysis_result_str.strip().replace("```json", "").replace("```", "")
        analysis_data = json.loads(clean_json_str)
        
        # ... (Saving logic is the same) ...
        lead.analysis_json = json.dumps(analysis_data)
        lead.summary = analysis_data.get("summary")
        lead.bullet_points = json.dumps(analysis_data.get("bullet_points", []))
        
        initial_pitch_content = analysis_data.get("simple_pitch")
        if initial_pitch_content:
            db.add(Pitch(lead_id=lead.id, content=initial_pitch_content))

        lead.status = LeadStatus.COMPLETED
        db.commit()

    except Exception as e:
        logger.error(f"Error processing lead {lead_id}: {e}", exc_info=True)
        lead.status = LeadStatus.FAILED
        db.commit()
    finally:
        db.close()

def _select_and_prioritize_text(crawled_pages: list[dict]) -> tuple[str, str, str]:
    """Helper function to consolidate text into three distinct, prioritized corpuses."""
    general_text = ""
    team_text = ""
    blog_news_text = ""

    # Homepage text is always our baseline general text
    homepage_html = crawled_pages[0]['html']
    soup = BeautifulSoup(homepage_html, "html.parser")
    general_text = " ".join(p.get_text(strip=True) for p in soup.find_all("p", limit=30))

    # Consolidate text from all relevant pages
    for page in crawled_pages:
        page_soup = BeautifulSoup(page['html'], "html.parser")
        main_content = page_soup.find("main") or page_soup.find("article") or page_soup.body
        page_text = " ".join(tag.get_text(strip=True) for tag in main_content.find_all(["p", "h1", "h2", "h3", "div"]))
        
        if any(keyword in page['url'] for keyword in TEAM_PAGE_KEYWORDS):
            team_text += page_text + " "
        
        if any(keyword in page['url'] for keyword in BLOG_NEWS_KEYWORDS):
            blog_news_text += page_text + " "

    if not team_text: team_text = general_text
    if not blog_news_text: blog_news_text = general_text
    
    return general_text, team_text, blog_news_text

def _create_analysis_prompt(general_text: str, team_text: str, blog_news_text: str) -> str:
    """Helper function to create the final, comprehensive AI prompt."""
    return f"""
    Analyze the provided website content from three sources: General, Team, and Blog/News.
    General Content: "{general_text[:4000]}"
    Team Page Content: "{team_text[:8000]}"
    Blog/News Content: "{blog_news_text[:8000]}"

    Provide a comprehensive business analysis in a raw JSON format. The JSON object must contain these keys:
    1. "summary": A concise summary based on the General Content.
    2. "bullet_points": An array of 10 key business points.
    3. "swot_analysis": An object with "strengths", "weaknesses", "opportunities", "threats".
    4. "detailed_analysis": An object with "business_model", "target_audience", etc.
    5. "key_persons": An array of objects with "name" and "title", found in the Team Page Content.
    6. "tech_and_trends": An object based on the Blog/News Content with three keys:
       - "recurring_themes": An array of 3-5 recurring technological themes or keywords.
       - "market_trends": An array of 2-3 key market trends the company is focused on.
       - "thought_leadership_position": A one-sentence summary of their public-facing thought leadership stance.

    Return ONLY the raw JSON object.
    """

@celery.task
def generate_pitch_task(lead_id: int, user_product: str) -> str:
    """
    A task to generate a custom pitch on-demand.
    """
    db: Session = SessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead or not lead.summary:
        db.close()
        return "Error: Lead or its analysis not found."

    async def _generate_pitch_async():
        prompt = f"""
        You are a professional B2B sales expert. Write a short, personalized, and compelling sales pitch.

        MY PRODUCT/SERVICE: "{user_product}"

        TARGET COMPANY NAME: {lead.company_name}
        TARGET COMPANY'S BUSINESS (based on their website): {lead.summary}
        TARGET COMPANY'S KEY OFFERINGS: {lead.bullet_points}

        Draft a concise and impactful pitch that connects my product to their specific business needs. Start with a strong opening that shows you've done your research.
        """
        return await ai_service.generate_text(prompt)

    try:
        # Use the same safe async pattern here
        return asyncio.run(_generate_pitch_async())
    except Exception as e:
        logger.error(f"Error generating pitch for lead {lead_id}: {e}", exc_info=True)
        return "Failed to generate pitch due to an internal error."
    finally:
        db.close()
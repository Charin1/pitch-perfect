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
from app.services.crawler import crawl_website
from app.services.generative_ai import ai_service

# Configure a logger for this module to provide clear output in the Celery console
logger = logging.getLogger(__name__)

# Initialize Celery, pointing it to the Redis instance defined in your .env file
celery = Celery("workers", broker=settings.REDIS_URL)

# --- Keyword Lists for Intelligent Text Selection ---
HIGH_PRIORITY_KEYWORDS = ["team", "leadership", "management", "board", "executive","about_us"]
GENERAL_ABOUT_KEYWORDS = ["about", "company", "who-we-are"]

@celery.task
def process_lead_website(lead_id: int, url: str):
    """
    Synchronous Celery task that orchestrates the async processing of a lead.
    """
    db: Session = SessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        db.close()
        return

    try:
        # Define a single async function to handle all network I/O (crawling and AI calls).
        # This ensures all async operations run on the same event loop.
        async def _process_lead_async():
            # Step 1: CRAWLING (Async)
            crawled_pages, crawled_urls = await crawl_website(url)
            
            log_message = f"\n{'='*50}\nCRAWL SUMMARY FOR LEAD ID: {lead_id} ({url})\nSuccessfully crawled {len(crawled_urls)} pages:\n"
            for crawled_url in crawled_urls:
                log_message += f"  - {crawled_url}\n"
            log_message += f"{'='*50}\n"
            logger.info(log_message)

            if not crawled_pages:
                raise ValueError("Crawling failed, no pages were retrieved.")

            # Step 2: TEXT SELECTION (Sync, but done within the async block)
            general_text, team_text = _select_prioritized_text(crawled_pages)

            # Step 3: AI ANALYSIS (Async)
            analysis_prompt = _create_analysis_prompt(general_text, team_text)
            analysis_result_str = await ai_service.generate_text(analysis_prompt)
            
            clean_json_str = analysis_result_str.strip().replace("```json", "").replace("```", "")
            analysis_data = json.loads(clean_json_str)
            
            return analysis_data

        # --- Run the single async function once ---
        lead.status = LeadStatus.CRAWLING
        db.commit()
        
        analysis_data = asyncio.run(_process_lead_async())

        # Step 4: SAVING (Sync)
        # This part runs after all async operations are successfully completed.
        lead.status = LeadStatus.COMPLETED
        lead.analysis_json = json.dumps(analysis_data)
        lead.summary = analysis_data.get("summary")
        lead.bullet_points = json.dumps(analysis_data.get("bullet_points", []))
        
        initial_pitch_content = analysis_data.get("simple_pitch")
        if initial_pitch_content:
            db.add(Pitch(lead_id=lead.id, content=initial_pitch_content))
        
        db.commit()

    except Exception as e:
        logger.error(f"Error processing lead {lead_id}: {e}", exc_info=True)
        lead.status = LeadStatus.FAILED
        db.commit()
    finally:
        db.close()

def _select_prioritized_text(crawled_pages: list[dict]) -> tuple[str, str]:
    """Helper function to consolidate text with prioritization."""
    general_text = ""
    high_priority_text = ""
    general_about_text = ""

    homepage_html = crawled_pages[0]['html']
    soup = BeautifulSoup(homepage_html, "html.parser")
    general_text = " ".join(p.get_text(strip=True) for p in soup.find_all("p", limit=30))

    for page in crawled_pages:
        page_soup = BeautifulSoup(page['html'], "html.parser")
        main_content = page_soup.find("main") or page_soup.find("article") or page_soup.body
        page_text = " ".join(tag.get_text(strip=True) for tag in main_content.find_all(["p", "h1", "h2", "h3", "div"]))
        
        if any(keyword in page['url'] for keyword in HIGH_PRIORITY_KEYWORDS):
            high_priority_text += page_text + " "
        elif any(keyword in page['url'] for keyword in GENERAL_ABOUT_KEYWORDS):
            general_about_text += page_text + " "

    team_text = high_priority_text + general_about_text
    if not team_text:
        team_text = general_text
    
    return general_text, team_text

def _create_analysis_prompt(general_text: str, team_text: str) -> str:
    """Helper function to create the AI prompt."""
    return f"""
    Analyze the provided website content.
    General Content: "{general_text[:4000]}"
    Team Page Content: "{team_text[:8000]}"

    Provide a comprehensive business analysis in a raw JSON format. The JSON object must contain these keys:
    1. "summary": A concise, one-paragraph summary of the company's primary business.
    2. "bullet_points": An array of exactly 10 key bullet points about their products or services.
    3. "simple_pitch": A very short, one-sentence opening pitch line.
    4. "swot_analysis": An object with four keys: "strengths", "weaknesses", "opportunities", and "threats". Each key should have an array of 2-3 descriptive strings.
    5. "detailed_analysis": An object with the following keys:
       - "business_model": A string describing how the company likely makes money.
       - "target_audience": A string describing their ideal customer profile.
       - "value_proposition": A string explaining their unique value.
       - "company_tone": A string describing the voice and style of their website copy.
       - "potential_needs": An array of 2-3 strings describing potential business challenges they might face.
    6. "key_persons": An array of objects, where each object has a "name" and "title" key. Find C-suite level individuals (CEO, CTO, CMO, COO, VP, Head of, etc.) from the "Team Page Content". If no C-suite members are found, return an empty array [].

    Return ONLY the raw JSON object without any markdown formatting.
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
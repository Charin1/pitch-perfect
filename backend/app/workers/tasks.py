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

# --- Prioritized Keyword Lists for Intelligent Text Selection ---
# Pages with these keywords are most likely to contain C-suite/leadership info.
HIGH_PRIORITY_KEYWORDS = ["team", "leadership", "management", "board", "executive","about_us"]
# Pages with these keywords provide good general context.
GENERAL_ABOUT_KEYWORDS = ["about", "company", "who-we-are"]

def run_async(func):
    """A helper function to run async functions within a sync Celery task."""
    return asyncio.run(func)

@celery.task
def process_lead_website(lead_id: int, url: str):
    """
    The main background task to process a new lead. It orchestrates the entire
    deep crawling and intelligent, prioritized analysis pipeline.
    """
    db: Session = SessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        db.close()
        return

    try:
        # Step 1: CRAWLING
        lead.status = LeadStatus.CRAWLING
        db.commit()
        
        crawled_pages, crawled_urls = run_async(crawl_website(url))
        
        # Log a formatted summary of the crawl results to the Celery worker console.
        log_message = f"\n{'='*50}\nCRAWL SUMMARY FOR LEAD ID: {lead_id} ({url})\nSuccessfully crawled {len(crawled_urls)} pages:\n"
        for crawled_url in crawled_urls:
            log_message += f"  - {crawled_url}\n"
        log_message += f"{'='*50}\n"
        logger.info(log_message)

        if not crawled_pages:
            raise ValueError("Crawling failed, no pages were retrieved from the website.")

        # Step 2: PRIORITIZED TEXT CONSOLIDATION
        general_text = ""
        high_priority_text = ""
        general_about_text = ""

        homepage_html = crawled_pages[0]['html']
        soup = BeautifulSoup(homepage_html, "html.parser")
        general_text = " ".join(p.get_text(strip=True) for p in soup.find_all("p", limit=30))

        # First pass: Collect text from high-priority pages to ensure it's not truncated.
        logger.info(f"Prioritizing pages with keywords: {HIGH_PRIORITY_KEYWORDS}")
        for page in crawled_pages:
            if any(keyword in page['url'] for keyword in HIGH_PRIORITY_KEYWORDS):
                logger.info(f"  -> Found high-priority page: {page['url']}")
                page_soup = BeautifulSoup(page['html'], "html.parser")
                main_content = page_soup.find("main") or page_soup.find("article") or page_soup.body
                high_priority_text += " ".join(tag.get_text(strip=True) for tag in main_content.find_all(["p", "h1", "h2", "h3", "div"])) + " "

        # Second pass: Collect text from general-priority pages.
        for page in crawled_pages:
            if any(keyword in page['url'] for keyword in GENERAL_ABOUT_KEYWORDS):
                page_soup = BeautifulSoup(page['html'], "html.parser")
                main_content = page_soup.find("main") or page_soup.find("article") or page_soup.body
                general_about_text += " ".join(tag.get_text(strip=True) for tag in main_content.find_all(["p", "h1", "h2", "h3", "div"])) + " "

        # Combine the text, ensuring high-priority content comes first.
        team_text = high_priority_text + general_about_text
        if not team_text:
            team_text = general_text

        # Step 3: ANALYZING
        lead.status = LeadStatus.ANALYZING
        db.commit()

        analysis_prompt = f"""
        Analyze the provided website content.
        General Content: "{general_text[:4000]}"
        Team Page Content: "{team_text[:15000]}"

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
        
        analysis_result_str = run_async(ai_service.generate_text(analysis_prompt))
        
        clean_json_str = analysis_result_str.strip().replace("```json", "").replace("```", "")
        analysis_data = json.loads(clean_json_str)
        
        # Step 4: SAVING
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

@celery.task
def generate_pitch_task(lead_id: int, user_product: str) -> str:
    """
    A task to generate a custom pitch on-demand based on the user's product
    description and the already-completed analysis of a lead.
    """
    db: Session = SessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead or not lead.summary:
        db.close()
        return "Error: Lead or its analysis not found."

    prompt = f"""
    You are a professional B2B sales expert. Write a short, personalized, and compelling sales pitch.

    MY PRODUCT/SERVICE: "{user_product}"

    TARGET COMPANY NAME: {lead.company_name}
    TARGET COMPANY'S BUSINESS (based on their website): {lead.summary}
    TARGET COMPANY'S KEY OFFERINGS: {lead.bullet_points}

    Draft a concise and impactful pitch that connects my product to their specific business needs. Start with a strong opening that shows you've done your research.
    """
    
    try:
        pitch_content = run_async(ai_service.generate_text(prompt))
        return pitch_content
    except Exception as e:
        logger.error(f"Error generating pitch for lead {lead_id}: {e}", exc_info=True)
        return "Failed to generate pitch due to an internal error."
    finally:
        db.close()
# From: backend/app/workers/tasks.py
# ----------------------------------------
import asyncio
import json
import logging
import re
from celery import Celery
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from app.core.config import settings
from app.db.base import SessionLocal
from app.db.models import Lead, Pitch, LeadStatus
from app.services.crawler import crawl_website
from app.services.generative_ai import ai_service
from app.services.third_party_data import fetch_growth_data

# Configure a logger for this module
logger = logging.getLogger(__name__)

# Initialize Celery, pointing it to the Redis instance defined in your .env file
celery = Celery("workers", broker=settings.REDIS_URL)

# --- Keyword Lists for Intelligent Text Selection ---
HIGH_PRIORITY_KEYWORDS = ["team", "leadership", "management", "board", "executive"]
GENERAL_ABOUT_KEYWORDS = ["about", "company", "who-we-are"]
BLOG_NEWS_KEYWORDS = ["blog", "news", "insights", "resources", "press", "article", "publication"]


# --- Robust Async Runner for Celery ---
def run_async_in_worker(async_func):
    """
    A safe way to run an async function from a synchronous Celery task.
    It gets or creates an event loop, runs the task, and avoids the
    "Event loop is closed" error caused by asyncio.run().
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'get_running_loop' fails if no loop is running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(async_func)


# --- Bulletproof, Regex-Powered AI Helper Functions ---

async def _safe_ai_json_parse(prompt: str, task_name: str, default_value: dict) -> dict:
    """
    A truly robust wrapper for making an AI call and extracting/parsing JSON.
    It uses regular expressions to find the JSON block and is guaranteed to
    always return a dictionary.
    """
    try:
        raw_result = await ai_service.generate_text(prompt)

        if not raw_result or not raw_result.strip():
            logger.warning(f"AI task '{task_name}' returned a completely empty response.")
            return default_value

        match = re.search(r"```json\s*(\{.*?\})\s*```", raw_result, re.DOTALL)
        json_string = ""
        if match:
            json_string = match.group(1)
        else:
            match = re.search(r"(\{.*\})", raw_result, re.DOTALL)
            if match:
                json_string = match.group(1)

        if not json_string:
            logger.warning(f"AI task '{task_name}' could not find a valid JSON block in the response. Raw Response: '{raw_result}'")
            logger.debug(f"Failed Prompt for '{task_name}':\n{prompt}")
            return default_value

        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.error(f"AI task '{task_name}' failed to decode extracted JSON. Error: {e}. Extracted String: {json_string}")
            return default_value

    except Exception as e:
        logger.error(f"An unexpected error occurred in AI task '{task_name}': {e}", exc_info=True)
        return default_value

async def get_overview_analysis(text: str) -> dict:
    prompt = f"""You are a helpful business analyst. Analyze the following general website content. If the content is empty or irrelevant, you must return a JSON object with empty strings or arrays for the values.
    Content: "{text}"
    Provide a raw JSON object with three keys: "summary", "bullet_points", and "simple_pitch".
    Return ONLY the raw JSON object."""
    return await _safe_ai_json_parse(prompt, "Overview", {"summary": "", "bullet_points": [], "simple_pitch": ""})

async def get_detailed_and_swot_analysis(text: str) -> dict:
    prompt = f"""You are a helpful business analyst. Analyze the following comprehensive company text. If you cannot find information for a field, you must return an empty string or array for that value.
    Content: "{text}"
    Provide a raw JSON object with two keys: "detailed_analysis" and "swot_analysis".
    Return ONLY the raw JSON object."""
    return await _safe_ai_json_parse(prompt, "Detailed/SWOT", {"detailed_analysis": {}, "swot_analysis": {}})

async def get_key_persons_analysis(text: str) -> dict:
    prompt = f"""You are a helpful research assistant. Analyze the following text from a company's team/leadership pages.
    Content: "{text}"
    Provide a raw JSON object with one key: "key_persons". This should be an array of objects, where each object has a "name" and "title" key. Find C-suite level individuals (CEO, CTO, CMO, etc.). If none are found, you MUST return an empty array [].
    Return ONLY the raw JSON object."""
    return await _safe_ai_json_parse(prompt, "Key Persons", {"key_persons": []})

async def get_tech_trends_analysis(text: str) -> dict:
    prompt = f"""You are a helpful technology analyst. Analyze the following text from a company's blog/news pages. If you cannot find information for a field, you must return an empty string or array for that value.
    Content: "{text}"
    Provide a raw JSON object with one key: "tech_and_trends". This object should contain three keys: "recurring_themes", "market_trends", and "thought_leadership_position".
    Return ONLY the raw JSON object."""
    return await _safe_ai_json_parse(prompt, "Tech/Trends", {"tech_and_trends": {}})

async def get_growth_analysis(text: str) -> dict:
    """
    AI task to analyze third-party data with a multi-layer backend safety net
    to ensure the stability rating is always a valid integer.
    """
    prompt = f"""You are a helpful financial analyst. Analyze the following third-party data.
    Content: "{text}"
    Provide a raw JSON object with one key: "growth_analysis". This object must contain keys "funding_summary", "revenue_estimate", "stability_rating", and "report".
    CRITICAL INSTRUCTION: The "stability_rating" field MUST be an integer between 0 and 10. It must NEVER be a string. If you cannot find enough data to make a confident assessment, the rating MUST be 0.
    Return ONLY the raw JSON object."""
    
    default = {"growth_analysis": {"funding_summary": "N/A", "revenue_estimate": "N/A", "stability_rating": 0, "report": "Could not retrieve or analyze third-party growth data."}}
    
    parsed_json = await _safe_ai_json_parse(prompt, "Growth Analysis", default)
    
    growth_data = parsed_json.get("growth_analysis")
    if not growth_data:
        return default

    rating = growth_data.get("stability_rating")
    
    if isinstance(rating, str):
        logger.warning(f"AI returned a non-integer stability rating: '{rating}'. Attempting to parse.")
        try:
            found_numbers = re.findall(r'\d+', rating)
            rating = int(found_numbers[0]) if found_numbers else 0
        except (ValueError, TypeError):
            rating = 0

    if not isinstance(rating, int) or not 0 <= rating <= 10:
        logger.warning(f"AI rating '{rating}' is invalid or out of range. Forcing to 0.")
        rating = 0

    report_text = growth_data.get("report", "").lower()
    if "could not" in report_text or "not found" in report_text or "unable to determine" in report_text:
        if rating > 2:
            logger.info(f"Report indicates no data, but rating was {rating}. Overriding to 1.")
            rating = 1

    growth_data["stability_rating"] = rating
    parsed_json["growth_analysis"] = growth_data

    return parsed_json

@celery.task
def process_lead_website(lead_id: int, url: str):
    """
    Main Celery task to orchestrate the entire lead analysis pipeline.
    """
    db: Session = SessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        db.close()
        return

    try:
        async def _process_lead_async():
            company_name = lead.company_name
            
            website_crawl_task = crawl_website(url)
            growth_data_task = fetch_growth_data(company_name)
            results = await asyncio.gather(website_crawl_task, growth_data_task)
            
            crawled_pages, crawled_urls = results[0]
            growth_data_text = results[1]
            
            log_message = f"\n{'='*50}\nCRAWL SUMMARY FOR LEAD ID: {lead_id}\nCrawled {len(crawled_urls)} pages.\n{'='*50}\n"
            logger.info(log_message)

            if not crawled_pages: raise ValueError("Crawling failed.")

            general_text, team_text, blog_news_text = _select_and_prioritize_text(crawled_pages)
            comprehensive_text = f"{general_text}\n{team_text}\n{blog_news_text}"
            budget = settings.AI_CONTEXT_BUDGET
            
            ai_tasks = [
                get_overview_analysis(general_text[:budget]),
                get_detailed_and_swot_analysis(comprehensive_text[:budget]),
                get_key_persons_analysis(team_text[:budget]),
                get_tech_trends_analysis(comprehensive_text[:budget]),
                get_growth_analysis(growth_data_text[:budget])
            ]
            ai_results = await asyncio.gather(*ai_tasks)
            
            final_analysis = {}
            for result in ai_results:
                if result is not None:
                    final_analysis.update(result)
            
            return final_analysis

        lead.status = LeadStatus.CRAWLING
        db.commit()
        
        analysis_data = run_async_in_worker(_process_lead_async())
        
        lead.status = LeadStatus.COMPLETED
        lead.analysis_json = json.dumps(analysis_data)
        lead.summary = analysis_data.get("summary")
        lead.bullet_points = json.dumps(analysis_data.get("bullet_points", []))
        initial_pitch_content = analysis_data.get("simple_pitch")
        if initial_pitch_content:
            db.add(Pitch(lead_id=lead.id, content=initial_pitch_content))
        db.commit()

    except Exception as e:
        logger.error(f"Error in main task for lead {lead_id}: {e}", exc_info=True)
        lead.status = LeadStatus.FAILED
        db.commit()
    finally:
        db.close()

def _select_and_prioritize_text(crawled_pages: list[dict]) -> tuple[str, str, str]:
    """
    Consolidates text with prioritization and smarter, less greedy extraction.
    """
    general_text = ""
    high_priority_text = ""
    general_about_text = ""
    blog_news_text = ""

    def get_clean_text(soup_area):
        tags = soup_area.find_all(["p", "h1", "h2", "h3", "h4", "li", "span", "td"])
        return " ".join(tag.get_text(strip=True) for tag in tags)

    homepage_html = crawled_pages[0]['html']
    soup = BeautifulSoup(homepage_html, "html.parser")
    general_text = " ".join(p.get_text(strip=True) for p in soup.find_all("p", limit=30))

    for page in crawled_pages:
        page_soup = BeautifulSoup(page['html'], "html.parser")
        content_area = page_soup.find("main") or page_soup.find("article") or page_soup.body
        page_text = get_clean_text(content_area) + " "
        
        if any(keyword in page['url'] for keyword in HIGH_PRIORITY_KEYWORDS):
            high_priority_text += page_text
        elif any(keyword in page['url'] for keyword in GENERAL_ABOUT_KEYWORDS):
            general_about_text += page_text
        
        if any(keyword in page['url'] for keyword in BLOG_NEWS_KEYWORDS):
            blog_news_text += page_text

    team_text = high_priority_text + general_about_text
    if not team_text: team_text = general_text
    if not blog_news_text: blog_news_text = general_text
    
    return general_text, team_text, blog_news_text

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
        return run_async_in_worker(_generate_pitch_async())
    except Exception as e:
        logger.error(f"Error generating pitch for lead {lead_id}: {e}", exc_info=True)
        return "Failed to generate pitch due to an internal error."
    finally:
        db.close()
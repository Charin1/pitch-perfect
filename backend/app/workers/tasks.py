# From: backend/app/workers/tasks.py
# ----------------------------------------
import asyncio
from celery import Celery
from sqlalchemy.orm import Session
import json

from app.core.config import settings
from app.db.base import SessionLocal
from app.db.models import Lead, Pitch, LeadStatus
from app.services.crawler import fetch_html, extract_text
from app.services.generative_ai import ai_service

# Initialize Celery, pointing it to the Redis instance defined in your .env file
celery = Celery("workers", broker=settings.REDIS_URL)

def run_async(func):
    """A helper function to run async functions within a sync Celery task."""
    return asyncio.run(func)

@celery.task
def process_lead_website(lead_id: int, url: str):
    """
    The main background task to process a new lead.
    It crawls the website, sends the content to the AI for analysis,
    and populates the database with the results.
    """
    db: Session = SessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        db.close()
        return

    try:
        # Step 1: CRAWLING - Update status and fetch website content
        lead.status = LeadStatus.CRAWLING
        db.commit()
        
        html = run_async(fetch_html(url))
        if not html:
            raise ValueError("Failed to fetch HTML content from the URL.")
        
        data = run_async(extract_text(html))
        
        lead.page_title = data.get('title')
        lead.page_description = data.get('description')
        db.commit()

        # Step 2: ANALYZING - Update status and call the Generative AI service
        lead.status = LeadStatus.ANALYZING
        db.commit()

        # This is the enhanced prompt asking for a detailed analysis in JSON format.
        analysis_prompt = f"""
        Analyze the website content for the company '{data.get('title', 'Unknown')}'.
        Content: "{data.get('body', '')[:4000]}"

        Provide a detailed business analysis in a raw JSON format. The JSON object must contain the following keys:
        1. "summary": A concise, one-paragraph summary of the company's primary business.
        2. "bullet_points": An array of exactly 10 key bullet points about their products or services.
        3. "simple_pitch": A very short, one-sentence opening pitch line.
        4. "swot_analysis": An object containing four keys: "strengths", "weaknesses", "opportunities", and "threats". Each key should have an array of 2-3 descriptive strings.

        Return ONLY the raw JSON object.
        """
        
        analysis_result_str = run_async(ai_service.generate_text(analysis_prompt))
        
        # Clean and parse the JSON result from the AI
        clean_json_str = analysis_result_str.strip().replace("```json", "").replace("```", "")
        analysis_data = json.loads(clean_json_str)
        
        # --- SAVE TO THE NEW AND OLD COLUMNS ---
        lead.analysis_json = json.dumps(analysis_data) # Store the full object

        # For backward compatibility and quick access
        lead.summary = analysis_data.get("summary")
        lead.bullet_points = json.dumps(analysis_data.get("bullet_points", []))
        
        # Create an initial pitch from the AI's "simple_pitch" suggestion
        initial_pitch_content = analysis_data.get("simple_pitch")
        if initial_pitch_content:
            db.add(Pitch(lead_id=lead.id, content=initial_pitch_content))


        # Step 3: COMPLETED - The process was successful
        lead.status = LeadStatus.COMPLETED
        db.commit()

    except Exception as e:
        print(f"Error processing lead {lead_id}: {e}")
        lead.status = LeadStatus.FAILED
        db.commit()
    finally:
        # Always close the database session to prevent connection leaks
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
        print(f"Error generating pitch for lead {lead_id}: {e}")
        return "Failed to generate pitch due to an internal error."
    finally:
        db.close()
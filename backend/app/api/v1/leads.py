# From: backend/app/api/v1/leads.py
# ----------------------------------------
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.db.base import get_db
from app.schemas import lead as lead_schema
from app.schemas import pitch as pitch_schema
from app.workers.tasks import process_lead_website, generate_pitch_task

# Initialize the API Router for this module
router = APIRouter()

@router.post("/", response_model=lead_schema.LeadRead, status_code=201)
def create_lead(lead: lead_schema.LeadCreate, db: Session = Depends(get_db)):
    """
    Create a new lead.
    This endpoint accepts a company name and a website URL, creates a new lead
    in the database, and triggers a background task to crawl and analyze the website.
    """
    # Check if a lead with the same URL already exists to avoid duplicates.
    db_lead = db.query(models.Lead).filter(models.Lead.website_url == str(lead.website_url)).first()
    if db_lead:
        raise HTTPException(status_code=400, detail="Website URL already exists in the database")
    
    # Create the new SQLAlchemy model instance, converting HttpUrl to a string.
    new_lead = models.Lead(company_name=lead.company_name, website_url=str(lead.website_url))
    
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    # Dispatch the long-running task to the Celery worker.
    process_lead_website.delay(lead_id=new_lead.id, url=new_lead.website_url)
    
    return new_lead

@router.get("/", response_model=List[lead_schema.LeadRead])
def read_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all leads from the database.
    Supports pagination with skip and limit parameters.
    """
    leads = db.query(models.Lead).order_by(models.Lead.created_at.desc()).offset(skip).limit(limit).all()
    return leads

@router.get("/{lead_id}", response_model=lead_schema.LeadRead)
def read_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the details of a single lead by its ID.
    """
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db_lead

@router.post("/{lead_id}/generate-pitch", response_model=pitch_schema.PitchRead)
def generate_pitch_for_lead(lead_id: int, request: pitch_schema.PitchCreateRequest, db: Session = Depends(get_db)):
    """
    Generate a new, custom pitch for a specific lead.
    This is the new, RESTful endpoint for this action.
    """
    # First, ensure the lead exists.
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # A pitch can only be generated if the AI analysis is complete.
    if lead.status != models.LeadStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Lead analysis is not yet complete. Please wait.")

    # Call the synchronous Celery task to get the pitch content.
    # Note: For very long generations, this could also be a background task.
    pitch_content = generate_pitch_task(
        lead_id=lead.id, 
        user_product=request.user_product_description
    )
    
    # Create and save the new pitch to the database.
    new_pitch = models.Pitch(
        lead_id=lead.id,
        content=pitch_content
    )
    db.add(new_pitch)
    db.commit()
    db.refresh(new_pitch)
    
    return new_pitch

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific lead by its ID.
    """
    # First, find the lead in the database.
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    
    # If the lead doesn't exist, return a 404 Not Found error.
    if db_lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    
    # If found, delete it from the database session.
    db.delete(db_lead)
    db.commit()
    
    # Return a 204 No Content response, which is standard for successful deletions.
    # The Response object is used here to ensure no body is sent back.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
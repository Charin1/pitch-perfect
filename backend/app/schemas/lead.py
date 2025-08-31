# From: backend/app/schemas/lead.py
# ----------------------------------------
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from app.db.models import LeadStatus

class LeadBase(BaseModel):
    company_name: str
    website_url: HttpUrl

class LeadCreate(LeadBase):
    pass

class LeadRead(LeadBase):
    id: int
    status: LeadStatus
    page_title: Optional[str] = None
    summary: Optional[str] = None
    bullet_points: Optional[str] = None
    analysis_json: Optional[str] = None # <-- ADD THIS LINE
    created_at: datetime

    class Config:
        orm_mode = True
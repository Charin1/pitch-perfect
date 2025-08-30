import enum
from sqlalchemy import (Column, Integer, String, Text, DateTime, ForeignKey, Enum)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class LeadStatus(str, enum.Enum):
    PENDING = "PENDING"
    CRAWLING = "CRAWLING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    website_url = Column(String, unique=True, index=True)
    status = Column(Enum(LeadStatus), default=LeadStatus.PENDING, nullable=False)
    
    page_title = Column(String, nullable=True)
    page_description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    bullet_points = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    pitches = relationship("Pitch", back_populates="lead", cascade="all, delete-orphan")

class Pitch(Base):
    __tablename__ = "pitches"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    lead = relationship("Lead", back_populates="pitches")
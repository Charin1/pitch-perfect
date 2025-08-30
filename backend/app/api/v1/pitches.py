# From: backend/app/api/v1/pitches.py
# ----------------------------------------
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.db.base import get_db
from app.schemas import pitch as pitch_schema

# Initialize the API Router for this module
router = APIRouter()

# --- NOTE ---
# The endpoint for generating/creating a new pitch has been moved to the
# `leads.py` router to follow a more RESTful pattern:
#
#   POST /api/v1/leads/{lead_id}/generate-pitch
#
# This file can be used for other pitch-specific actions in the future.
# For example:

@router.get("/{pitch_id}", response_model=pitch_schema.PitchRead)
def read_pitch(pitch_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single pitch by its unique ID.
    (Example of a future endpoint)
    """
    pitch = db.query(models.Pitch).filter(models.Pitch.id == pitch_id).first()
    if pitch is None:
        raise HTTPException(status_code=404, detail="Pitch not found")
    return pitch

@router.delete("/{pitch_id}", status_code=204)
def delete_pitch(pitch_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific pitch by its ID.
    (Example of a future endpoint)
    """
    pitch = db.query(models.Pitch).filter(models.Pitch.id == pitch_id).first()
    if pitch is None:
        raise HTTPException(status_code=404, detail="Pitch not found")
    
    db.delete(pitch)
    db.commit()
    return {"ok": True} # Response body will not be sent for 204 status code
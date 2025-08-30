# From: backend/app/schemas/pitch.py
# ----------------------------------------
from pydantic import BaseModel
from datetime import datetime

class PitchBase(BaseModel):
    content: str

# NEW SCHEMA for the request body of our new endpoint
class PitchCreateRequest(BaseModel):
    user_product_description: str

# This schema is now only used for the old endpoint, we can keep it for reference
class PitchGenerate(BaseModel):
    lead_id: int
    user_product_description: str

class PitchRead(PitchBase):
    id: int
    lead_id: int
    created_at: datetime

    class Config:
        orm_mode = True
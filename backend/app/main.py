from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base import Base, engine
from app.api.v1 import leads, pitches

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PitchPerfect API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router, prefix="/api/v1/leads", tags=["Leads"])
app.include_router(pitches.router, prefix="/api/v1/pitches", tags=["Pitches"])

@app.get("/", tags=["Health Check"])
async def health():
    return {"status": "ok", "message": "Welcome to PitchPerfect API"}
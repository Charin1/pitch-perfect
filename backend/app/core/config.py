# From: backend/app/core/config.py
# ----------------------------------------
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load the .env file so os.getenv and pydantic-settings can find the variables
load_dotenv()

class Settings(BaseSettings):
    """
    Defines all configuration for the application.
    pydantic-settings will automatically read values from environment variables.
    """
    # --- Core Settings ---
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    GOOGLE_API_KEY: str

    # --- Crawler Settings ---
    CRAWLER_MAX_PAGES: int = 20
    CRAWLER_MAX_DEPTH: int = 3

    # --- Growth Analysis Settings ---
    # STEP 1: Read the problematic variable as a simple, raw string.
    # The field name now EXACTLY matches the variable name in the .env file.
    GROWTH_DATA_SOURCES: str = ""

    # --- AI Settings ---
    AI_CONTEXT_BUDGET: int = 100000 # Increased budget

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create the settings instance. This will now succeed without errors.
settings = Settings()

# STEP 2: Manually parse the raw string into the list we actually need.
# This is simple, explicit Python that bypasses the Pydantic error.
GROWTH_DATA_SOURCES_LIST = []
if settings.GROWTH_DATA_SOURCES:
    GROWTH_DATA_SOURCES_LIST = [
        item.strip() for item in settings.GROWTH_DATA_SOURCES.split(';') if item.strip()
    ]
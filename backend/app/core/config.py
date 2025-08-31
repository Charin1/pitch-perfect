import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")

    # --- NEW: Crawler Settings ---
    CRAWLER_MAX_PAGES: int = int(os.getenv("CRAWLER_MAX_PAGES", 20))
    CRAWLER_MAX_DEPTH: int = int(os.getenv("CRAWLER_MAX_DEPTH", 3))

    class Config:
        env_file = ".env"

settings = Settings()
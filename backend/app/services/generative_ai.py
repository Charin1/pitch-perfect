# From: backend/app/services/generative_ai.py
# ----------------------------------------
from google import genai
from app.core.config import settings

# Configure the SDK using the new library's method
try:
    # The new library uses a Client object
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    print(f"Error configuring Google Gen AI Client: {e}")
    client = None

class GenerativeAIService:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        # The client is already initialized, we just reference the model by name
        self.model_name = model_name
        self.client = client

    async def generate_text(self, prompt: str) -> str:
        if not self.client:
            return "Error: Generative AI service not configured."
        try:
            # The new library uses client.models.generate_content
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error during text generation: {e}")
            return f"Error: Could not generate content. Details: {e}"

# Singleton instance for use across the application
ai_service = GenerativeAIService()
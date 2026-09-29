from google import genai
from google.genai import types

from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)


def generate_text(prompt: str, system_instruction: str | None = None) -> str:
    """Send one prompt to Gemini and return its plain text reply."""
    response = _client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,  # low: we want consistent classification, not creative variation
        ),
    )
    return response.text
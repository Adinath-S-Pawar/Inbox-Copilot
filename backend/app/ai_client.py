import re
import time

from google import genai
from google.genai import errors, types

from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

MAX_RETRIES = 3
FALLBACK_DELAY_SECONDS = 5


def _extract_retry_delay(exc: errors.APIError) -> float:
    """Read Google's suggested wait time from a 429 error, else use a fallback."""
    message = str(exc)
    match = re.search(r"retryDelay['\"]?\s*:\s*['\"](\d+)", message)
    return float(match.group(1)) + 1 if match else FALLBACK_DELAY_SECONDS


def generate_text(prompt: str, system_instruction: str | None = None) -> str:
    """Send one prompt to Gemini and return its plain text reply.

    Retries on transient overload (503) and rate limiting (429), waiting the
    exact time Google's error tells us to when it's given, since the free
    tier enforces a strict requests-per-minute limit.
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = _client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                ),
            )
            return response.text
        except errors.ClientError as exc:
            last_error = exc
            if "RESOURCE_EXHAUSTED" in str(exc) and attempt < MAX_RETRIES - 1:
                time.sleep(_extract_retry_delay(exc))
            else:
                raise
        except errors.ServerError as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(FALLBACK_DELAY_SECONDS * (attempt + 1))
    raise last_error
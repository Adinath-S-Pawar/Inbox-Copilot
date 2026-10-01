import json

from app.ai_client import generate_text

DEADLINE_SYSTEM_INSTRUCTION = """You extract due dates from emails for a deadline tracker.
For EACH email, find the single most important due date mentioned (a deadline, submission
date, or expiry). Convert it to ISO format YYYY-MM-DD. Assume the current year is 2026 unless
the email states otherwise. If no clear date is mentioned, use null.

Respond with ONLY a JSON array, no markdown, matching the input order:
[{"id": "<same id as input>", "due_date": "YYYY-MM-DD" or null}, ...]
"""


class DeadlineError(Exception):
    """Raised when Gemini's response can't be parsed as valid deadline output."""


def extract_deadlines(actions: list[dict]) -> dict[str, str | None]:
    """Extract a due date for each action in one batched call. Returns {email_id: due_date}."""
    if not actions:
        return {}

    numbered = "\n\n".join(
        f"id: {a['email_id']}\nSubject: {a['subject']}\nMessage: {a.get('body') or a['reason']}"
        for a in actions
    )
    raw = generate_text(numbered, system_instruction=DEADLINE_SYSTEM_INSTRUCTION)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise DeadlineError(f"Gemini did not return a valid JSON array: {raw!r}") from exc

    return {item["id"]: item.get("due_date") for item in parsed if "id" in item}
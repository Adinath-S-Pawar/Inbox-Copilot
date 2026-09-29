import json

from app.ai_client import generate_text

TRIAGE_SYSTEM_INSTRUCTION = """You triage emails for a busy student/freelancer.
Classify each email into exactly one category:
- "reply": needs a written response (a question, a request, feedback to acknowledge)
- "schedule": is proposing or asking about a meeting, call, or interview slot
- "deadline": mentions a due date, submission date, or expiry the user must track
- "ignore": newsletters, promotions, automated digests, or anything needing no action

Respond with ONLY a JSON object, no markdown, no explanation:
{"category": "reply" | "schedule" | "deadline" | "ignore", "reason": "one short sentence"}
"""


class TriageError(Exception):
    """Raised when Gemini's response can't be parsed as a valid triage result."""


VALID_CATEGORIES = {"reply", "schedule", "deadline", "ignore"}


def triage_email(email: dict) -> dict:
    """Classify one (already known non-sensitive) email using Gemini."""
    prompt = (
        f"Subject: {email['subject']}\n"
        f"From: {email['sender_name']} <{email['sender_email']}>\n"
        f"Body: {email['body']}"
    )
    raw = generate_text(prompt, system_instruction=TRIAGE_SYSTEM_INSTRUCTION)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise TriageError(f"Gemini did not return valid JSON: {raw!r}") from exc

    category = result.get("category")
    if category not in VALID_CATEGORIES:
        raise TriageError(f"Gemini returned an unknown category: {result!r}")

    return {"category": category, "reason": result.get("reason", "")}

BATCH_SYSTEM_INSTRUCTION = """You triage a batch of emails for a busy student/freelancer.
For EACH email, classify into exactly one category:
- "reply": needs a written response (a question, a request, feedback to acknowledge)
- "schedule": is proposing or asking about a meeting, call, or interview slot
- "deadline": mentions a due date, submission date, or expiry the user must track
- "ignore": newsletters, promotions, automated digests, or anything needing no action

Respond with ONLY a JSON array, no markdown, matching the input order:
[{"id": "<same id as input>", "category": "...", "reason": "one short sentence"}, ...]
"""


def triage_batch(emails: list[dict]) -> dict[str, dict]:
    """Classify several emails in one Gemini call. Returns {id: {category, reason}}."""
    if not emails:
        return {}

    numbered = "\n\n".join(
        f"id: {e['id']}\nSubject: {e['subject']}\nFrom: {e['sender_name']} <{e['sender_email']}>\nBody: {e['body']}"
        for e in emails
    )
    raw = generate_text(numbered, system_instruction=BATCH_SYSTEM_INSTRUCTION)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise TriageError(f"Gemini did not return a valid JSON array: {raw!r}") from exc

    results = {}
    for item in parsed:
        category = item.get("category")
        if category in VALID_CATEGORIES and "id" in item:
            results[item["id"]] = {"category": category, "reason": item.get("reason", "")}
    return results
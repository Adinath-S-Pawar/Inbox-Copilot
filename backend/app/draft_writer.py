import json

from app.ai_client import generate_text

def build_system_instruction(user_name: str) -> str:
    return f"""You write short, professional email reply drafts on behalf of {user_name}.
Match a friendly but concise, professional tone.

Rules:
- Only use facts, dates, or commitments present in the original message. Never invent them.
- If the reply would need information you don't have (a link, a file, a specific number,
  a confirmed time), write [NEEDS INPUT: what's missing] in its place instead of guessing
  or inventing a placeholder that looks like real content.
- Do not add a subject line.
- Sign off with just "{user_name}".

Respond with ONLY a JSON array, no markdown, matching the input order:
[{{"id": "<same id as input>", "draft": "<the full reply text>"}}]
"""


class DraftError(Exception):
    """Raised when Gemini's response can't be parsed as valid draft output."""


def draft_replies(emails: list[dict], user_name: str = "the user") -> dict[str, str]:
    """Generate a draft reply for each email in one batched call. Returns {id: draft_text}."""
    if not emails:
        return {}

    numbered = "\n\n".join(
        f"id: {e['email_id']}\nSubject: {e['subject']}\nFrom: {e['sender_name']} <{e['sender_email']}>\nOriginal message: {e.get('body', e.get('reason', ''))}"
        for e in emails
    )
    raw = generate_text(numbered, system_instruction=build_system_instruction(user_name))
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise DraftError(f"Gemini did not return a valid JSON array: {raw!r}") from exc

    return {item["id"]: item["draft"] for item in parsed if "id" in item and "draft" in item}
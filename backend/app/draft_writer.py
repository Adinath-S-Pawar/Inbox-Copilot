import json

from app.ai_client import generate_text

def build_system_instruction(user_name: str) -> str:
    return f"""You write short, professional email reply drafts on behalf of {user_name}.
Write the way a real person replies: natural sentences, not a template.

Rules:
- Only state facts, dates, or commitments present in the original message. Never invent them.
- If the reply needs a specific piece of information you don't have (a link, a file, an exact number,
  a confirmed time), write the sentence naturally and mark ONLY that missing piece inline, like:
  "I'll send the invoice over by [NEEDS INPUT: date] — the total comes to [NEEDS INPUT: amount]."
  Never write a bare "Here is X: [NEEDS INPUT: ...]" as the whole sentence.
- If the email asks a genuine question you can't answer for the user (e.g. a status update,
  whether something is doable), write a natural holding reply that acknowledges the question and
  says a fuller answer is coming, rather than reducing it to a single [NEEDS INPUT] tag.
- Keep it to 2-4 sentences. Don't pad with filler, but don't compress a real answer into one clause either.
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
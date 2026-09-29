import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "sample_inbox.json"


def load_sample_emails(include_expected: bool = False) -> list[dict]:
    """Load the sample inbox in the same shape as real Gmail emails.

    The 'expected' label is hidden by default so the app (and the AI) can never
    see the answers. Tests and the accuracy report pass include_expected=True.
    """
    with open(DATA_FILE, encoding="utf-8") as f:
        raw = json.load(f)

    emails = []
    for item in raw:
        email = {
            "id": item["id"],
            "thread_id": item["id"],
            "message_id": f"<{item['id']}@sample.local>",
            "sender_name": item["sender_name"],
            "sender_email": item["sender_email"],
            "subject": item["subject"],
            "date": item["date"],
            "snippet": item["body"][:100],
            "body": item["body"],
        }
        if include_expected:
            email["expected"] = item["expected"]
        emails.append(email)
    return emails
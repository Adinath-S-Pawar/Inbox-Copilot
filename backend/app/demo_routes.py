from fastapi import APIRouter

from app.sample_data import load_sample_emails
from app.sensitive_filter import is_sensitive

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/emails")
def demo_emails():
    emails = load_sample_emails()
    for email in emails:
        email["sensitive"] = is_sensitive(email)
        if email["sensitive"]:
            email["body"] = None
    return {"count": len(emails), "emails": emails}
from fastapi import APIRouter

from app.sample_data import load_sample_emails

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/emails")
def demo_emails():
    emails = load_sample_emails()
    return {"count": len(emails), "emails": emails}
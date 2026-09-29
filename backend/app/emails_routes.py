from fastapi import APIRouter, HTTPException, Query
from googleapiclient.errors import HttpError

from app import gmail_service
from app.sensitive_filter import is_sensitive

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("")
def list_emails(limit: int = Query(10, ge=1, le=50), unread_only: bool = True):
    try:
        emails = gmail_service.fetch_emails(limit=limit, unread_only=unread_only)
    except gmail_service.NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="Not signed in. Visit /auth/login first.")
    except HttpError as exc:
        raise HTTPException(status_code=502, detail=f"Gmail API error: {exc.status_code}")

    for email in emails:
        email["sensitive"] = is_sensitive(email)
        if email["sensitive"]:
            email["body"] = None

    return {"count": len(emails), "emails": emails}
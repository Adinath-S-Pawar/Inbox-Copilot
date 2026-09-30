from fastapi import APIRouter, HTTPException, Query
from googleapiclient.errors import HttpError

from app import gmail_service
from app.sample_data import load_sample_emails
from app.sensitive_filter import is_sensitive
from app.triage import BATCH_SYSTEM_INSTRUCTION, TriageError, triage_batch
from app.triage_sync import sync_emails_to_queue

router = APIRouter(prefix="/triage", tags=["triage"])

CHUNK_SIZE = 25

def _triage_batch(emails: list[dict]) -> list[dict]:
    safe_emails, sensitive_ids = [], set()
    entries = {}

    for email in emails:
        sensitive = is_sensitive(email)
        entries[email["id"]] = {
            "id": email["id"], "subject": email["subject"],
            "sender_email": email["sender_email"], "sensitive": sensitive,
        }
        if sensitive:
            sensitive_ids.add(email["id"])
            entries[email["id"]]["category"] = "sensitive"
            entries[email["id"]]["reason"] = "Contains an OTP, verification code, or financial alert; skipped for privacy."
        else:
            safe_emails.append(email)

    for i in range(0, len(safe_emails), CHUNK_SIZE):
        chunk = safe_emails[i:i + CHUNK_SIZE]
        try:
            results = triage_batch(chunk)
        except Exception as exc:
            results = {}
            for email in chunk:
                entries[email["id"]]["category"] = "error"
                entries[email["id"]]["reason"] = f"Triage temporarily unavailable: {exc}"
            continue
        for email in chunk:
            result = results.get(email["id"])
            if result:
                entries[email["id"]].update(result)
            else:
                entries[email["id"]]["category"] = "error"
                entries[email["id"]]["reason"] = "Missing from Gemini's batch response."

    return [entries[e["id"]] for e in emails]


@router.get("")
def triage_real_emails(limit: int = Query(10, ge=1, le=25), unread_only: bool = True):
    try:
        emails = gmail_service.fetch_emails(limit=limit, unread_only=unread_only)
    except gmail_service.NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="Not signed in. Visit /auth/login first.")
    except HttpError as exc:
        raise HTTPException(status_code=502, detail=f"Gmail API error: {exc.status_code}")
    return {"count": len(emails), "results": _triage_batch(emails)}


@router.get("/demo")
def triage_demo_emails():
    emails = load_sample_emails()
    return {"count": len(emails), "results": _triage_batch(emails)}

@router.post("/sync")
def sync_real_emails(limit: int = Query(10, ge=1, le=25), unread_only: bool = True):
    try:
        emails = gmail_service.fetch_emails(limit=limit, unread_only=unread_only)
    except gmail_service.NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="Not signed in. Visit /auth/login first.")
    except HttpError as exc:
        raise HTTPException(status_code=502, detail=f"Gmail API error: {exc.status_code}")
    return sync_emails_to_queue(emails, source="real")


@router.post("/sync/demo")
def sync_demo_emails():
    emails = load_sample_emails()
    return sync_emails_to_queue(emails, source="demo")
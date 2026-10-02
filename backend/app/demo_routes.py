from fastapi import APIRouter

from app.sample_data import load_sample_emails
from app.sensitive_filter import is_sensitive
from app.draft_writer import draft_replies
from app.triage_sync import ACTIONABLE_CATEGORIES
from app.triage import triage_batch

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/emails")
def demo_emails():
    emails = load_sample_emails()
    for email in emails:
        email["sensitive"] = is_sensitive(email)
        if email["sensitive"]:
            email["body"] = None
    return {"count": len(emails), "emails": emails}

@router.get("/actions")
def demo_actions():
    """Compute the full demo pipeline (triage + drafts) fresh, with no database writes.
    Every call is independent and stateless — safe for any number of concurrent visitors."""
    emails = load_sample_emails()
    safe_emails = [e for e in emails if not is_sensitive(e)]
    triage_results = triage_batch(safe_emails)

    actions = []
    for email in safe_emails:
        result = triage_results.get(email["id"])
        category = result["category"] if result else "error"
        if category not in ACTIONABLE_CATEGORIES:
            continue
        actions.append({
            "id": email["id"], "source": "demo", "category": category,
            "subject": email["subject"], "sender_name": email["sender_name"],
            "sender_email": email["sender_email"], "reason": result["reason"] if result else "",
            "draft_text": None, "proposed_time": None,
        })

    reply_actions = [a for a in actions if a["category"] == "reply"]
    if reply_actions:
        drafts = draft_replies(
            [{"email_id": a["id"], "subject": a["subject"], "sender_name": a["sender_name"],
               "sender_email": a["sender_email"], "body": next(e["body"] for e in safe_emails if e["id"] == a["id"])}
              for a in reply_actions],
            user_name="Aarav Mehta",
        )
        for a in reply_actions:
            a["draft_text"] = drafts.get(a["id"])

    return {"count": len(actions), "actions": actions}
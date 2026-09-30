from app.actions_repo import create_pending_action
from app.sensitive_filter import is_sensitive
from app.triage import triage_batch

# Only these categories become queued actions; "ignore" and "sensitive" emails
# are informational only and never enter the approval queue.
ACTIONABLE_CATEGORIES = {"reply", "schedule", "deadline"}


def sync_emails_to_queue(emails: list[dict], source: str) -> dict:
    """Triage a batch of emails and queue a pending action for each actionable one.

    Already-queued emails (same source + email_id) are skipped automatically
    by create_pending_action's duplicate guard, so this is safe to call
    repeatedly (e.g. a refresh button) without creating duplicate actions.
    """
    safe_emails = [e for e in emails if not is_sensitive(e)]
    results = triage_batch(safe_emails) if safe_emails else {}

    queued, skipped_existing, skipped_not_actionable, sensitive_count = 0, 0, 0, 0

    for email in emails:
        if is_sensitive(email):
            sensitive_count += 1
            continue

        result = results.get(email["id"])
        category = result["category"] if result else "error"
        reason = result["reason"] if result else "Triage did not return a result for this email."

        if category not in ACTIONABLE_CATEGORIES:
            skipped_not_actionable += 1
            continue

        action_id = create_pending_action(
            source=source, email_id=email["id"], category=category,
            subject=email["subject"], sender_name=email["sender_name"],
            sender_email=email["sender_email"], reason=reason,
        )
        if action_id is not None:
            queued += 1
        else:
            skipped_existing += 1

    return {
        "queued": queued,
        "skipped_existing": skipped_existing,
        "skipped_not_actionable": skipped_not_actionable,
        "sensitive_skipped": sensitive_count,
    }
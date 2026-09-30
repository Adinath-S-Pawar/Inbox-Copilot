import pytest

from app import db, triage_sync
from app.triage_sync import sync_emails_to_queue


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    from dataclasses import replace
    monkeypatch.setattr(db, "settings", replace(db.settings, database_file=str(tmp_path / "test.db")))
    db.init_db()


def _email(email_id, subject="Hi", body="Can we talk?", sender="alex@example.com"):
    return {"id": email_id, "subject": subject, "sender_name": "Alex",
            "sender_email": sender, "body": body}


def test_sensitive_emails_never_reach_triage_or_queue(monkeypatch):
    called = []
    monkeypatch.setattr(triage_sync, "triage_batch", lambda emails: called.append(emails) or {})
    otp_email = _email("s01", subject="Your OTP", body="Your OTP is 482913.")
    result = sync_emails_to_queue([otp_email], source="demo")
    assert result["sensitive_skipped"] == 1
    assert result["queued"] == 0
    assert called == []  # triage_batch was never called — the only email was sensitive


def test_actionable_categories_get_queued(monkeypatch):
    emails = [_email("s02"), _email("s03"), _email("s04")]
    monkeypatch.setattr(triage_sync, "triage_batch", lambda batch: {
        "s02": {"category": "reply", "reason": "needs a reply"},
        "s03": {"category": "ignore", "reason": "newsletter"},
        "s04": {"category": "schedule", "reason": "wants a call"},
    })
    result = sync_emails_to_queue(emails, source="demo")
    assert result["queued"] == 2  # s02 and s04; s03 is "ignore", not actionable
    assert result["skipped_not_actionable"] == 1


def test_sync_is_idempotent(monkeypatch):
    emails = [_email("s02")]
    monkeypatch.setattr(triage_sync, "triage_batch", lambda batch: {
        "s02": {"category": "reply", "reason": "needs a reply"},
    })
    first = sync_emails_to_queue(emails, source="demo")
    second = sync_emails_to_queue(emails, source="demo")
    assert first["queued"] == 1
    assert second["queued"] == 0
    assert second["skipped_existing"] == 1
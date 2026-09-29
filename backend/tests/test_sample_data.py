import re
from collections import Counter

from app.sample_data import load_sample_emails

CATEGORIES = {"reply", "schedule", "deadline", "ignore", "sensitive"}
REQUIRED_KEYS = {"id", "thread_id", "message_id", "sender_name", "sender_email",
                 "subject", "date", "snippet", "body"}


def test_loads_25_unique_emails():
    emails = load_sample_emails()
    assert len(emails) == 25
    assert len({e["id"] for e in emails}) == 25


def test_emails_have_required_fields():
    for email in load_sample_emails():
        assert REQUIRED_KEYS <= email.keys()
        assert email["body"].strip()


def test_expected_label_hidden_by_default():
    assert all("expected" not in e for e in load_sample_emails())


def test_labels_are_valid_and_balanced():
    counts = Counter(e["expected"] for e in load_sample_emails(include_expected=True))
    assert set(counts) == CATEGORIES
    assert all(n >= 4 for n in counts.values())


def test_sensitive_emails_contain_numeric_codes():
    sensitive = [e for e in load_sample_emails(include_expected=True) if e["expected"] == "sensitive"]
    assert len(sensitive) == 5
    assert all(re.search(r"\d{4,}", e["body"]) for e in sensitive)
import pytest

from app.sample_data import load_sample_emails
from app.sensitive_filter import is_sensitive
from app.triage import triage_batch

pytestmark = pytest.mark.accuracy  # excluded from normal `pytest` runs; see pytest.ini


def test_triage_accuracy_on_sample_inbox():
    emails = load_sample_emails(include_expected=True)
    safe_emails = [e for e in emails if not is_sensitive(e)]

    results = triage_batch(safe_emails)  # one batched call, matching triage_routes.py

    correct = 0
    mismatches = []
    for email in emails:
        expected = email["expected"]
        if is_sensitive(email):
            actual = "sensitive"
        else:
            actual = results.get(email["id"], {}).get("category", "missing")

        if actual == expected:
            correct += 1
        else:
            mismatches.append((email["id"], expected, actual))

    accuracy = correct / len(emails)
    print(f"\nTriage accuracy: {correct}/{len(emails)} = {accuracy:.0%}")
    if mismatches:
        print("Mismatches:", mismatches)

    assert accuracy >= 0.8, f"Accuracy {accuracy:.0%} is below the 80% bar"
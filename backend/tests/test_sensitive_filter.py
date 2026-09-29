from app.sample_data import load_sample_emails
from app.sensitive_filter import filter_emails, is_sensitive


def test_all_sample_sensitive_emails_are_caught():
    emails = load_sample_emails(include_expected=True)
    for email in emails:
        result = is_sensitive(email)
        if email["expected"] == "sensitive":
            assert result is True, f"missed sensitive email: {email['id']}"


def test_no_normal_email_is_wrongly_flagged():
    emails = load_sample_emails(include_expected=True)
    for email in emails:
        result = is_sensitive(email)
        if email["expected"] != "sensitive":
            assert result is False, f"false positive on: {email['id']} ({email['expected']})"


def test_filter_emails_splits_correctly():
    emails = load_sample_emails(include_expected=True)
    safe, sensitive = filter_emails(emails)
    assert len(safe) + len(sensitive) == len(emails)
    assert len(sensitive) == 5
    assert all(e["expected"] == "sensitive" for e in sensitive)


def test_plain_otp_email_flagged():
    email = {"sender_email": "hello@example.com", "subject": "Hi",
              "body": "Your OTP is 918273 for login."}
    assert is_sensitive(email) is True


def test_ordinary_reply_not_flagged():
    email = {"sender_email": "priya@brightcraft.example", "subject": "Question",
              "body": "Could you send me the invoice for the project?"}
    assert is_sensitive(email) is False
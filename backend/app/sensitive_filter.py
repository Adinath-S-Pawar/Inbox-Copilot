import re

# Senders whose mail is treated as sensitive regardless of content.
SENSITIVE_SENDER_PATTERNS = [
    r"\bno-?reply\b",
    r"\balerts?\b",
    r"\bsecurity\b",
    r"\botp\b",
]

# Phrases that strongly signal an OTP, verification code, or financial alert.
SENSITIVE_BODY_PATTERNS = [
    r"\botp\b",
    r"one[- ]time password",
    r"verification code",
    r"password reset code",
    r"\bdebit(ed)?\b",
    r"\bcredit(ed)?\b",
    r"account (ending|no\.?|number)",
    r"card ending",
    r"transaction (of|alert)",
    r"upi reference",
    r"available balance",
    r"\bcvv\b",
]

# A 4+ digit run within ~15 characters of one of these words is almost always
# an actual code (e.g. "OTP is 482913"), not incidental text like "source code"
# appearing near an unrelated number such as a year.
CODE_NEAR_DIGITS = re.compile(
    r"(?:code|otp|password|pin)\D{0,15}\d{4,}|\d{4,}\D{0,15}(?:code|otp|password|pin)",
    re.IGNORECASE,
)

_sender_re = re.compile("|".join(SENSITIVE_SENDER_PATTERNS), re.IGNORECASE)
_body_re = re.compile("|".join(SENSITIVE_BODY_PATTERNS), re.IGNORECASE)


def is_sensitive(email: dict) -> bool:
    """Return True if this email must never be sent to the LLM."""
    sender = email.get("sender_email", "")
    body = email.get("body", "")
    subject = email.get("subject", "")
    text = f"{subject} {body}"

    if _sender_re.search(sender):
        return True
    if _body_re.search(text):
        return True
    if CODE_NEAR_DIGITS.search(text):
        return True
    return False


def filter_emails(emails: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split emails into (safe, sensitive) without altering either list's contents."""
    safe, sensitive = [], []
    for email in emails:
        (sensitive if is_sensitive(email) else safe).append(email)
    return safe, sensitive
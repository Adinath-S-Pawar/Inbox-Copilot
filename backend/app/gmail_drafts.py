import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app import google_auth
from app.gmail_service import NotAuthenticatedError


def _service():
    creds = google_auth.load_credentials()
    if creds is None:
        raise NotAuthenticatedError()
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def create_gmail_draft(*, to: str, subject: str, body: str, thread_id: str | None = None,
                         in_reply_to: str | None = None) -> str:
    """Create a real Gmail draft (never sent). Returns the created draft's id.

    thread_id and in_reply_to, when given, keep the draft attached to the
    original email's thread so it appears as a reply, not a new message.
    """
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = in_reply_to

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body_payload = {"message": {"raw": raw}}
    if thread_id:
        body_payload["message"]["threadId"] = thread_id

    service = _service()
    try:
        result = service.users().drafts().create(userId="me", body=body_payload).execute()
    except HttpError as exc:
        raise RuntimeError(f"Gmail draft creation failed: {exc.status_code}") from exc
    return result["id"]
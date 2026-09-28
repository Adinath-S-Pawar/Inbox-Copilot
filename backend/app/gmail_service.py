from googleapiclient.discovery import build

from app import google_auth
from app.email_parser import parse_message


class NotAuthenticatedError(Exception):
    """Raised when there is no valid saved Google login."""


def _service():
    creds = google_auth.load_credentials()
    if creds is None:
        raise NotAuthenticatedError()
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def fetch_emails(limit: int = 10, unread_only: bool = True) -> list[dict]:
    """Fetch the latest inbox emails and return them as clean dictionaries."""
    service = _service()
    query = "in:inbox is:unread" if unread_only else "in:inbox"
    listing = service.users().messages().list(userId="me", q=query, maxResults=limit).execute()
    emails = []
    for ref in listing.get("messages", []):
        raw = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        emails.append(parse_message(raw))
    return emails
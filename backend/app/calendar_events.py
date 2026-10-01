from datetime import datetime, timedelta

from googleapiclient.errors import HttpError

from app.calendar_service import SLOT_DURATION_MINUTES, _service


def create_tentative_event(*, summary: str, start_iso: str, attendee_email: str) -> str:
    """Create a tentative calendar event starting at start_iso. Returns the event id."""
    start = datetime.fromisoformat(start_iso)
    end = start + timedelta(minutes=SLOT_DURATION_MINUTES)
    body = {
        "summary": summary,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
        "attendees": [{"email": attendee_email}],
        "status": "tentative",
        "description": "Proposed by Inbox Copilot. Confirm with the attendee before finalizing.",
    }
    service = _service()
    try:
        result = service.events().insert(calendarId="primary", body=body, sendUpdates="none").execute()
    except HttpError as exc:
        raise RuntimeError(f"Calendar event creation failed: {exc.status_code}") from exc
    return result["id"]
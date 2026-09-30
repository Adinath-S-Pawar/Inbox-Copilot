from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app import google_auth
from app.gmail_service import NotAuthenticatedError

# Only suggest slots within normal working hours.
WORK_START_HOUR = 9
WORK_END_HOUR = 18
LOOKAHEAD_DAYS = 7
SLOT_DURATION_MINUTES = 30


def _service():
    creds = google_auth.load_credentials()
    if creds is None:
        raise NotAuthenticatedError()
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _fetch_busy_periods(service, time_min: datetime, time_max: datetime) -> list[tuple[datetime, datetime]]:
    body = {
        "timeMin": time_min.isoformat(),
        "timeMax": time_max.isoformat(),
        "items": [{"id": "primary"}],
    }
    try:
        result = service.freebusy().query(body=body).execute()
    except HttpError as exc:
        raise RuntimeError(f"Calendar free/busy check failed: {exc.status_code}") from exc

    busy = result["calendars"]["primary"]["busy"]
    return [(datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])) for b in busy]


def _overlaps_any(start: datetime, end: datetime, busy_periods: list[tuple[datetime, datetime]]) -> bool:
    return any(start < b_end and end > b_start for b_start, b_end in busy_periods)


def find_free_slots(max_slots: int = 3) -> list[dict]:
    """Return up to max_slots candidate meeting times within working hours,
    over the next LOOKAHEAD_DAYS, that don't overlap anything on the calendar."""
    service = _service()
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(days=LOOKAHEAD_DAYS)
    busy_periods = _fetch_busy_periods(service, now, time_max)

    slots = []
    day_cursor = now.replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
    if day_cursor < now:
        day_cursor += timedelta(days=1)
        day_cursor = day_cursor.replace(hour=WORK_START_HOUR, minute=0)

    while len(slots) < max_slots and day_cursor < time_max:
        day_end = day_cursor.replace(hour=WORK_END_HOUR, minute=0)
        slot_start = day_cursor
        while slot_start + timedelta(minutes=SLOT_DURATION_MINUTES) <= day_end and len(slots) < max_slots:
            slot_end = slot_start + timedelta(minutes=SLOT_DURATION_MINUTES)
            if slot_start > now and not _overlaps_any(slot_start, slot_end, busy_periods):
                slots.append({"start": slot_start.isoformat(), "end": slot_end.isoformat()})
            slot_start += timedelta(minutes=SLOT_DURATION_MINUTES)
        day_cursor = (day_cursor + timedelta(days=1)).replace(hour=WORK_START_HOUR, minute=0)

    return slots
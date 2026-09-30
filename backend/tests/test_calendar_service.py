from datetime import datetime, timedelta, timezone

from app.calendar_service import _overlaps_any


def test_overlapping_slot_detected():
    busy = [(datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc), datetime(2026, 10, 1, 10, 30, tzinfo=timezone.utc))]
    slot_start = datetime(2026, 10, 1, 10, 15, tzinfo=timezone.utc)
    slot_end = slot_start + timedelta(minutes=30)
    assert _overlaps_any(slot_start, slot_end, busy) is True


def test_non_overlapping_slot_is_free():
    busy = [(datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc), datetime(2026, 10, 1, 10, 30, tzinfo=timezone.utc))]
    slot_start = datetime(2026, 10, 1, 11, 0, tzinfo=timezone.utc)
    slot_end = slot_start + timedelta(minutes=30)
    assert _overlaps_any(slot_start, slot_end, busy) is False


def test_adjacent_slot_is_not_overlapping():
    """A slot that ends exactly when a busy period starts should count as free."""
    busy = [(datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc), datetime(2026, 10, 1, 10, 30, tzinfo=timezone.utc))]
    slot_start = datetime(2026, 10, 1, 9, 30, tzinfo=timezone.utc)
    slot_end = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
    assert _overlaps_any(slot_start, slot_end, busy) is False


def test_empty_busy_list_never_overlaps():
    slot_start = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
    slot_end = slot_start + timedelta(minutes=30)
    assert _overlaps_any(slot_start, slot_end, []) is False
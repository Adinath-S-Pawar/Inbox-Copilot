import pytest
from fastapi.testclient import TestClient

from app import approval_routes, calendar_routes, db, schedule_routes
from app.actions_repo import create_pending_action, get_action
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    from dataclasses import replace
    monkeypatch.setattr(db, "settings", replace(db.settings, database_file=str(tmp_path / "test.db")))
    db.init_db()


def _schedule_action(source="demo"):
    return create_pending_action(source=source, email_id="s03", category="schedule", subject="Call to discuss phase 2",
                                   sender_name="Rohan", sender_email="rohan@example.com", reason="wants a call")


def test_propose_time_attaches_a_real_slot(monkeypatch):
    monkeypatch.setattr(schedule_routes, "find_free_slots",
                          lambda max_slots: [{"start": "2026-10-02T09:00:00+05:30", "end": "2026-10-02T09:30:00+05:30"}])
    action_id = _schedule_action()
    response = client.post(f"/actions/{action_id}/propose-time")
    assert response.json()["proposed_time"] == "2026-10-02T09:00:00+05:30"
    assert get_action(action_id)["proposed_time"] == "2026-10-02T09:00:00+05:30"


def test_approve_schedule_without_proposed_time_fails():
    action_id = _schedule_action()
    response = client.post(f"/actions/{action_id}/approve")
    assert response.status_code == 400


def test_approve_demo_schedule_never_calls_calendar(monkeypatch):
    called = []
    monkeypatch.setattr(approval_routes, "create_tentative_event", lambda **kw: called.append(kw) or "fake-event")
    monkeypatch.setattr(schedule_routes, "find_free_slots",
                          lambda max_slots: [{"start": "2026-10-02T09:00:00+05:30", "end": "2026-10-02T09:30:00+05:30"}])
    action_id = _schedule_action(source="demo")
    client.post(f"/actions/{action_id}/propose-time")
    response = client.post(f"/actions/{action_id}/approve")
    assert response.json()["status"] == "approved"
    assert called == []


def test_approve_real_schedule_creates_event(monkeypatch):
    monkeypatch.setattr(approval_routes, "create_tentative_event", lambda **kw: "real-event-456")
    monkeypatch.setattr(schedule_routes, "find_free_slots",
                          lambda max_slots: [{"start": "2026-10-02T09:00:00+05:30", "end": "2026-10-02T09:30:00+05:30"}])
    action_id = _schedule_action(source="real")
    client.post(f"/actions/{action_id}/propose-time")
    response = client.post(f"/actions/{action_id}/approve")
    assert response.json()["calendar_event_id"] == "real-event-456"
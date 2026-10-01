import pytest
from fastapi.testclient import TestClient

from app import db, deadline_routes
from app.actions_repo import create_pending_action, list_deadlines
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    from dataclasses import replace
    monkeypatch.setattr(db, "settings", replace(db.settings, database_file=str(tmp_path / "test.db")))
    db.init_db()


def test_sync_extracts_and_stores_deadlines(monkeypatch):
    create_pending_action(source="demo", email_id="s05", category="deadline", subject="Internship deadline",
                            sender_name="Office", sender_email="office@example.com", reason="closes 10 October")
    monkeypatch.setattr(deadline_routes, "extract_deadlines", lambda actions: {"s05": "2026-10-10"})
    response = client.post("/deadlines/sync?source=demo")
    assert response.json() == {"synced": 1, "requested": 1}
    stored = list_deadlines(source="demo")
    assert stored[0]["due_date"] == "2026-10-10"


def test_deadlines_sorted_soonest_first(monkeypatch):
    create_pending_action(source="demo", email_id="s09", category="deadline", subject="Later deadline",
                            sender_name="A", sender_email="a@example.com", reason="due 20 October")
    create_pending_action(source="demo", email_id="s18", category="deadline", subject="Sooner deadline",
                            sender_name="B", sender_email="b@example.com", reason="due 5 October")
    monkeypatch.setattr(deadline_routes, "extract_deadlines",
                          lambda actions: {"s09": "2026-10-20", "s18": "2026-10-05"})
    client.post("/deadlines/sync?source=demo")
    response = client.get("/deadlines?source=demo")
    dates = [d["due_date"] for d in response.json()["deadlines"]]
    assert dates == ["2026-10-05", "2026-10-20"]


def test_sync_is_idempotent(monkeypatch):
    create_pending_action(source="demo", email_id="s05", category="deadline", subject="Internship deadline",
                            sender_name="Office", sender_email="office@example.com", reason="closes 10 October")
    monkeypatch.setattr(deadline_routes, "extract_deadlines", lambda actions: {"s05": "2026-10-10"})
    client.post("/deadlines/sync?source=demo")
    second = client.post("/deadlines/sync?source=demo")
    assert second.json()["synced"] == 1  # the action is still "pending" so it's requested again...
    assert len(list_deadlines(source="demo")) == 1  # ...but create_deadline's UNIQUE guard prevents a duplicate row
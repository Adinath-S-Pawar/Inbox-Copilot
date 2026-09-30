import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    from dataclasses import replace
    monkeypatch.setattr(db, "settings", replace(db.settings, database_file=str(tmp_path / "test.db")))
    db.init_db()


def _seed():
    from app.actions_repo import create_pending_action
    create_pending_action(source="demo", email_id="s02", category="reply", subject="Invoice",
                            sender_name="Priya", sender_email="priya@example.com", reason="needs reply")
    create_pending_action(source="real", email_id="r01", category="schedule", subject="Call",
                            sender_name="Rohan", sender_email="rohan@example.com", reason="wants a call")


def test_list_all_actions():
    _seed()
    response = client.get("/actions")
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_filter_by_source():
    _seed()
    response = client.get("/actions?source=demo")
    assert response.json()["count"] == 1
    assert response.json()["actions"][0]["email_id"] == "s02"


def test_rejects_invalid_source():
    response = client.get("/actions?source=nonsense")
    assert response.status_code == 422


def test_get_single_action_found():
    _seed()
    action_id = client.get("/actions?source=demo").json()["actions"][0]["id"]
    response = client.get(f"/actions/{action_id}")
    assert response.status_code == 200
    assert response.json()["subject"] == "Invoice"


def test_get_single_action_not_found():
    response = client.get("/actions/9999")
    assert response.status_code == 404
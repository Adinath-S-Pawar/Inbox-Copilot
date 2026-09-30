import pytest
from fastapi.testclient import TestClient

from app import approval_routes, db
from app.actions_repo import create_pending_action, get_action
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    from dataclasses import replace
    monkeypatch.setattr(db, "settings", replace(db.settings, database_file=str(tmp_path / "test.db")))
    db.init_db()


def _reply_action(source="demo", draft_text="Hi, thanks!\nAarav"):
    return create_pending_action(source=source, email_id="s02", category="reply", subject="Invoice",
                                   sender_name="Priya", sender_email="priya@example.com",
                                   reason="needs reply", draft_text=draft_text)


def test_approve_demo_reply_never_calls_gmail(monkeypatch):
    called = []
    monkeypatch.setattr(approval_routes, "create_gmail_draft", lambda **kw: called.append(kw) or "fake-id")
    action_id = _reply_action(source="demo")
    response = client.post(f"/actions/{action_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert called == []  # Gmail was never touched for a demo action
    assert get_action(action_id)["status"] == "approved"


def test_approve_real_reply_calls_gmail_and_records_draft_id(monkeypatch):
    monkeypatch.setattr(approval_routes, "create_gmail_draft",
                          lambda **kw: "real-draft-123")
    action_id = _reply_action(source="real")
    response = client.post(f"/actions/{action_id}/approve")
    body = response.json()
    assert body["status"] == "approved"
    assert body["gmail_draft_id"] == "real-draft-123"


def test_approve_reply_without_draft_fails():
    action_id = _reply_action(draft_text=None)
    response = client.post(f"/actions/{action_id}/approve")
    assert response.status_code == 400


def test_approve_twice_is_rejected():
    action_id = _reply_action()
    client.post(f"/actions/{action_id}/approve")
    second = client.post(f"/actions/{action_id}/approve")
    assert second.status_code == 409


def test_reject_never_calls_gmail(monkeypatch):
    called = []
    monkeypatch.setattr(approval_routes, "create_gmail_draft", lambda **kw: called.append(kw) or "x")
    action_id = _reply_action(source="real")
    response = client.post(f"/actions/{action_id}/reject")
    assert response.json()["status"] == "rejected"
    assert called == []


def test_approve_nonexistent_action_404s():
    response = client.post("/actions/9999/approve")
    assert response.status_code == 404
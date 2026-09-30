import pytest
from fastapi.testclient import TestClient

from app import db, draft_routes
from app.actions_repo import create_pending_action, get_action
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    from dataclasses import replace
    monkeypatch.setattr(db, "settings", replace(db.settings, database_file=str(tmp_path / "test.db")))
    db.init_db()


def test_generate_drafts_fills_reply_actions(monkeypatch):
    action_id = create_pending_action(source="demo", email_id="s02", category="reply",
                                        subject="Invoice", sender_name="Priya",
                                        sender_email="priya@example.com", reason="needs reply")
    monkeypatch.setattr(draft_routes, "draft_replies",
                           lambda actions, **kwargs: {"s02": "Hi Priya, here it is.\nAarav"})
    response = client.post("/drafts/generate?source=demo")
    assert response.json() == {"drafted": 1, "requested": 1}
    assert get_action(action_id)["draft_text"] == "Hi Priya, here it is.\nAarav"


def test_generate_drafts_skips_when_none_pending():
    response = client.post("/drafts/generate?source=demo")
    assert response.json()["drafted"] == 0


def test_generate_drafts_does_not_redo_existing(monkeypatch):
    create_pending_action(source="demo", email_id="s02", category="reply", subject="Invoice",
                            sender_name="Priya", sender_email="priya@example.com",
                            reason="needs reply", draft_text="already drafted")
    called = []
    monkeypatch.setattr(draft_routes, "draft_replies", lambda actions, **kwargs: called.append(1) or {})
    client.post("/drafts/generate?source=demo")
    assert called == []  # nothing pending needed a draft, so Gemini was never called
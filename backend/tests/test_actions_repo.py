import pytest

from app import db
from app.actions_repo import create_pending_action, get_action, list_actions, update_action_status


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    """Point every test at a throwaway database file, never the real one."""
    from dataclasses import replace
    monkeypatch.setattr(db, "settings", replace(db.settings, database_file=str(tmp_path / "test.db")))
    db.init_db()


def _sample(**overrides):
    data = dict(source="demo", email_id="s01", category="reply", subject="Hi",
                sender_name="Alex", sender_email="alex@example.com", reason="asks a question")
    data.update(overrides)
    return data


def test_create_and_get_action():
    action_id = create_pending_action(**_sample())
    assert action_id is not None
    action = get_action(action_id)
    assert action["status"] == "pending"
    assert action["subject"] == "Hi"


def test_duplicate_email_is_ignored():
    first_id = create_pending_action(**_sample())
    second_id = create_pending_action(**_sample())  # same source + email_id
    assert first_id is not None
    assert second_id is None
    assert len(list_actions()) == 1


def test_list_actions_filters_by_status_and_source():
    create_pending_action(**_sample(email_id="s01"))
    create_pending_action(**_sample(email_id="s02", source="real"))
    assert len(list_actions(source="demo")) == 1
    assert len(list_actions(status="pending")) == 2
    assert len(list_actions(status="approved")) == 0


def test_update_action_status():
    action_id = create_pending_action(**_sample())
    assert update_action_status(action_id, "approved") is True
    assert get_action(action_id)["status"] == "approved"
    assert update_action_status(9999, "approved") is False  # non-existent id
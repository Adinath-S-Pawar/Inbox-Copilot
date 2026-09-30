import pytest

from app import draft_writer
from app.draft_writer import DraftError, draft_replies


def test_draft_replies_parses_batch(monkeypatch):
    fake_response = '[{"id": "s02", "draft": "Hi Priya, sending the invoice shortly.\\nAarav"}]'
    monkeypatch.setattr(draft_writer, "generate_text", lambda *a, **k: fake_response)
    result = draft_replies([{"email_id": "s02", "subject": "Invoice", "sender_name": "Priya",
                               "sender_email": "priya@example.com", "reason": "needs reply"}])
    assert result == {"s02": "Hi Priya, sending the invoice shortly.\nAarav"}


def test_draft_replies_empty_input_skips_call(monkeypatch):
    called = []
    monkeypatch.setattr(draft_writer, "generate_text", lambda *a, **k: called.append(1))
    assert draft_replies([]) == {}
    assert called == []


def test_draft_replies_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(draft_writer, "generate_text", lambda *a, **k: "not json")
    with pytest.raises(DraftError):
        draft_replies([{"email_id": "s02", "subject": "Hi", "sender_name": "A",
                          "sender_email": "a@example.com", "reason": "x"}])
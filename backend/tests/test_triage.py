import json

import pytest

from app import triage
from app.triage import TriageError, triage_email


def _fake_email(**overrides):
    email = {"subject": "Hi", "sender_name": "Alex", "sender_email": "alex@example.com",
              "body": "Can we talk?"}
    email.update(overrides)
    return email


def test_triage_parses_clean_json(monkeypatch):
    monkeypatch.setattr(triage, "generate_text", lambda *a, **k: '{"category": "reply", "reason": "asks a question"}')
    result = triage_email(_fake_email())
    assert result == {"category": "reply", "reason": "asks a question"}


def test_triage_strips_markdown_fence(monkeypatch):
    fenced = '```json\n{"category": "schedule", "reason": "proposes a call"}\n```'
    monkeypatch.setattr(triage, "generate_text", lambda *a, **k: fenced)
    result = triage_email(_fake_email())
    assert result["category"] == "schedule"


def test_triage_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(triage, "generate_text", lambda *a, **k: "not json at all")
    with pytest.raises(TriageError):
        triage_email(_fake_email())


def test_triage_rejects_unknown_category(monkeypatch):
    monkeypatch.setattr(triage, "generate_text", lambda *a, **k: '{"category": "spam", "reason": "x"}')
    with pytest.raises(TriageError):
        triage_email(_fake_email())
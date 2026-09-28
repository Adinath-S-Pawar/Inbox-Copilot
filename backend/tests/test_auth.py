from fastapi.testclient import TestClient

from app import google_auth
from app.main import app

client = TestClient(app)


def test_status_false_when_no_token(monkeypatch, tmp_path):
    monkeypatch.setattr(google_auth, "TOKEN_FILE", str(tmp_path / "missing.json"))
    response = client.get("/auth/status")
    assert response.json() == {"authenticated": False}


def test_callback_rejects_unknown_state():
    response = client.get("/auth/callback?state=bad&code=x", follow_redirects=False)
    assert response.status_code == 400
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_emails_work_without_login():
    response = client.get("/demo/emails")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 25
    assert "expected" not in body["emails"][0]
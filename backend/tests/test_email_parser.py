import base64

from app.email_parser import MAX_BODY_CHARS, parse_message


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


def _headers(**kw):
    return [{"name": k.replace("_", "-"), "value": v} for k, v in kw.items()]


def test_parses_headers_and_plain_body():
    msg = {
        "id": "1", "threadId": "t1", "snippet": "Can we talk",
        "payload": {
            "mimeType": "text/plain",
            "headers": _headers(From="Riya Shah <Riya@Example.com>", Subject="Call?",
                                Date="Mon, 28 Sep 2026 10:00:00 +0530", Message_ID="<abc@mail>"),
            "body": {"data": _b64("Can we talk tomorrow?")},
        },
    }
    result = parse_message(msg)
    assert result["sender_name"] == "Riya Shah"
    assert result["sender_email"] == "riya@example.com"
    assert result["subject"] == "Call?"
    assert result["message_id"] == "<abc@mail>"
    assert result["body"] == "Can we talk tomorrow?"


def test_prefers_plain_over_html():
    msg = {"id": "2", "payload": {
        "mimeType": "multipart/alternative", "headers": [],
        "parts": [
            {"mimeType": "text/plain", "body": {"data": _b64("plain version")}},
            {"mimeType": "text/html", "body": {"data": _b64("<p>html version</p>")}},
        ]}}
    assert parse_message(msg)["body"] == "plain version"


def test_falls_back_to_stripped_html():
    html = "<p>Hello <b>there</b></p><script>x()</script>"
    msg = {"id": "3", "payload": {"mimeType": "text/html", "headers": [],
                                  "body": {"data": _b64(html)}}}
    assert parse_message(msg)["body"] == "Hello there"


def test_handles_missing_subject_and_body():
    msg = {"id": "4", "payload": {"headers": []}}
    result = parse_message(msg)
    assert result["subject"] == "(no subject)"
    assert result["body"] == ""


def test_truncates_long_body():
    msg = {"id": "5", "payload": {"mimeType": "text/plain", "headers": [],
                                  "body": {"data": _b64("a" * 10000)}}}
    assert len(parse_message(msg)["body"]) == MAX_BODY_CHARS
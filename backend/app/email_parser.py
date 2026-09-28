import base64
import re
from email.utils import parseaddr
from html import unescape

MAX_BODY_CHARS = 4000  # keeps LLM prompts small and cheap later


def _decode(data: str) -> str:
    """Gmail uses URL-safe base64 without padding; fix the padding and decode."""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    """Remove scripts/styles and tags, keep readable text."""
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _collect(payload: dict, found: dict) -> None:
    """Walk the nested message parts and gather text/plain and text/html bodies."""
    mime = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data")
    if data and mime in ("text/plain", "text/html"):
        found.setdefault(mime, []).append(_decode(data))
    for part in payload.get("parts") or []:
        _collect(part, found)


def extract_body(payload: dict) -> str:
    """Prefer plain text; fall back to HTML converted to text."""
    found: dict = {}
    _collect(payload, found)
    if found.get("text/plain"):
        return re.sub(r"\n{3,}", "\n\n", "\n".join(found["text/plain"])).strip()
    if found.get("text/html"):
        return _strip_html("\n".join(found["text/html"]))
    return ""


def parse_message(msg: dict) -> dict:
    """Convert a raw Gmail API message into the clean shape the app uses."""
    payload = msg.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    name, address = parseaddr(headers.get("from", ""))
    return {
        "id": msg["id"],
        "thread_id": msg.get("threadId"),
        "message_id": headers.get("message-id"),  
        "sender_name": name,
        "sender_email": address.lower(),
        "subject": headers.get("subject", "(no subject)"),
        "date": headers.get("date", ""),
        "snippet": unescape(msg.get("snippet", "")),
        "body": extract_body(payload)[:MAX_BODY_CHARS],
    }
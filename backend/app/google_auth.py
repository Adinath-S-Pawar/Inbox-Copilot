import os

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.config import settings

# Allow plain http://localhost during local development only.
if settings.google_redirect_uri.startswith("http://localhost"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
# Google may return scopes in a different order; don't fail on that.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]

TOKEN_FILE = settings.google_token_file
_pending_flows: dict = {}


def create_flow() -> Flow:
    return Flow.from_client_secrets_file(
        settings.google_credentials_file,
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


def start_login() -> str:
    """Build the Google consent URL and remember the flow for the callback."""
    flow = create_flow()
    url, state = flow.authorization_url(
        access_type="offline", prompt="consent", include_granted_scopes="true"
    )
    _pending_flows[state] = flow
    return url


def finish_login(state: str, code: str) -> None:
    """Exchange the code Google sent back for tokens and save them locally."""
    flow = _pending_flows.pop(state, None)
    if flow is None:
        raise ValueError("Unknown or expired login attempt")
    flow.fetch_token(code=code)
    with open(TOKEN_FILE, "w") as f:
        f.write(flow.credentials.to_json())


def load_credentials() -> Credentials | None:
    """Return valid saved credentials, refreshing them if needed, else None."""
    if not os.path.exists(TOKEN_FILE):
        return None
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            return None
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds if creds.valid else None


def clear_credentials() -> None:
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
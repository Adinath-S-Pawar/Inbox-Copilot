import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    google_credentials_file: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    google_token_file: str = os.getenv("GOOGLE_TOKEN_FILE", "token.json")


settings = Settings()
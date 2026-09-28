from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app import google_auth
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login():
    return RedirectResponse(google_auth.start_login())


@router.get("/callback")
def callback(state: str | None = None, code: str | None = None, error: str | None = None):
    if error or not code or not state:
        return RedirectResponse(f"{settings.frontend_origin}?login=denied")
    try:
        google_auth.finish_login(state, code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse(f"{settings.frontend_origin}?login=success")


@router.get("/status")
def status():
    return {"authenticated": google_auth.load_credentials() is not None}


@router.post("/logout")
def logout():
    google_auth.clear_credentials()
    return {"authenticated": False}
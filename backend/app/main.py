from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth_routes import router as auth_router
from app.config import settings
from app.emails_routes import router as emails_router
from app.demo_routes import router as demo_router
from app.ai_routes import router as ai_router
from app.triage_routes import router as triage_router
from app.db import init_db
from app.actions_routes import router as actions_router
from app.draft_routes import router as draft_router
from app.approval_routes import router as approval_router

app = FastAPI(title="Inbox Copilot API", version="0.1.0")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(emails_router)
app.include_router(demo_router)
app.include_router(ai_router)
app.include_router(triage_router)
app.include_router(actions_router)
app.include_router(draft_router)
app.include_router(approval_router)

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "inbox-copilot"}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth_routes import router as auth_router
from app.config import settings
from app.emails_routes import router as emails_router
from app.demo_routes import router as demo_router

app = FastAPI(title="Inbox Copilot API", version="0.1.0")

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

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "inbox-copilot"}
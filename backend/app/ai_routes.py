from fastapi import APIRouter, HTTPException

from app.ai_client import generate_text

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/ping")
def ping():
    try:
        text = generate_text("Reply with exactly the word: pong")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini call failed: {exc}")
    return {"reply": text.strip()}
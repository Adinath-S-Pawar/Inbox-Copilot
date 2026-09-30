from fastapi import APIRouter, HTTPException

from app.calendar_service import find_free_slots
from app.gmail_service import NotAuthenticatedError

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/free-slots")
def get_free_slots(count: int = 3):
    try:
        slots = find_free_slots(max_slots=count)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="Not signed in. Visit /auth/login first.")
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"count": len(slots), "slots": slots}
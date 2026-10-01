from fastapi import APIRouter, HTTPException

from app.actions_repo import get_action, set_proposed_time
from app.calendar_service import find_free_slots
from app.gmail_service import NotAuthenticatedError

router = APIRouter(prefix="/actions", tags=["schedule"])


@router.post("/{action_id}/propose-time")
def propose_time(action_id: int, slot_index: int = 0):
    """Attach one of the next few free slots to a pending 'schedule' action."""
    action = get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    if action["category"] != "schedule":
        raise HTTPException(status_code=400, detail="Action is not a schedule action")
    if action["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Action is already {action['status']}")

    try:
        slots = find_free_slots(max_slots=slot_index + 1)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="Not signed in. Visit /auth/login first.")
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if slot_index >= len(slots):
        raise HTTPException(status_code=404, detail="No free slot at that index")

    chosen = slots[slot_index]
    set_proposed_time(action_id, chosen["start"])
    return {"id": action_id, "proposed_time": chosen["start"], "proposed_end": chosen["end"]}
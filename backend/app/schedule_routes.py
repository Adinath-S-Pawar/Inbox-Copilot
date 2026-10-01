from fastapi import APIRouter, HTTPException

from app.actions_repo import get_action, set_proposed_time, list_proposed_times
from app.calendar_service import find_free_slots
from app.gmail_service import NotAuthenticatedError

router = APIRouter(prefix="/actions", tags=["schedule"])

@router.post("/{action_id}/propose-time")
def propose_time(action_id: int, slot_index: int = 0):
    """Attach a free slot to a pending 'schedule' action, skipping times
    already proposed to other pending schedule actions in the same source."""
    action = get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    if action["category"] != "schedule":
        raise HTTPException(status_code=400, detail="Action is not a schedule action")
    if action["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Action is already {action['status']}")

    try:
        raw_slots = find_free_slots(max_slots=slot_index + 10)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="Not signed in. Visit /auth/login first.")
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    taken = set(list_proposed_times(source=action["source"], exclude_id=action_id))
    available = [s for s in raw_slots if s["start"] not in taken]

    if slot_index >= len(available):
        raise HTTPException(status_code=404, detail="No free slot at that index")

    chosen = available[slot_index]
    set_proposed_time(action_id, chosen["start"])
    return {"id": action_id, "proposed_time": chosen["start"], "proposed_end": chosen["end"]}
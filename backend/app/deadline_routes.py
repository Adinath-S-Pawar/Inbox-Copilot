from fastapi import APIRouter, HTTPException

from app.actions_repo import create_deadline, list_actions, list_deadlines
from app.deadline_extractor import DeadlineError, extract_deadlines

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


@router.post("/sync")
def sync_deadlines(source: str = "demo"):
    """Extract due dates for pending 'deadline' actions and store them in the tracker."""
    pending = [a for a in list_actions(source=source, status="pending") if a["category"] == "deadline"]
    if not pending:
        return {"synced": 0, "message": "No pending deadline actions to sync."}

    try:
        extracted = extract_deadlines(pending)
    except DeadlineError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    synced = 0
    for action in pending:
        due_date = extracted.get(str(action["email_id"]))
        deadline_id = create_deadline(source=source, email_id=action["email_id"],
                                        subject=action["subject"], due_date=due_date)
        if deadline_id is not None:
            synced += 1

    return {"synced": synced, "requested": len(pending)}


@router.get("")
def get_deadlines(source: str | None = None):
    deadlines = list_deadlines(source=source)
    return {"count": len(deadlines), "deadlines": deadlines}


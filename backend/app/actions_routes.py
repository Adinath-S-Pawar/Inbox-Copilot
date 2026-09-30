from fastapi import APIRouter, HTTPException, Query

from app.actions_repo import get_action, list_actions

router = APIRouter(prefix="/actions", tags=["actions"])

VALID_SOURCES = {"real", "demo"}
VALID_STATUSES = {"pending", "approved", "rejected"}


@router.get("")
def get_actions(source: str | None = Query(None), status: str | None = Query(None)):
    if source is not None and source not in VALID_SOURCES:
        raise HTTPException(status_code=422, detail=f"source must be one of {VALID_SOURCES}")
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {VALID_STATUSES}")
    actions = list_actions(source=source, status=status)
    return {"count": len(actions), "actions": actions}


@router.get("/{action_id}")
def get_single_action(action_id: int):
    action = get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    return action
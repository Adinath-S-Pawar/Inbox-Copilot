from fastapi import APIRouter, HTTPException

from app.actions_repo import list_actions, set_draft_text
from app.draft_writer import DraftError, draft_replies

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("/generate")
def generate_drafts(source: str = "demo"):
    """Generate draft text for every pending 'reply' action that doesn't have one yet."""
    pending = [a for a in list_actions(source=source, status="pending")
               if a["category"] == "reply" and not a["draft_text"]]
    if not pending:
        return {"drafted": 0, "message": "No pending reply actions need a draft."}

    try:
        drafts = draft_replies(pending, user_name="Aarav Mehta")
    except DraftError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    drafted = 0
    for action in pending:
        draft_text = drafts.get(str(action["email_id"]))
        if draft_text:
            set_draft_text(action["id"], draft_text)
            drafted += 1

    return {"drafted": drafted, "requested": len(pending)}
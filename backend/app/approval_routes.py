from fastapi import APIRouter, HTTPException

from app.actions_repo import get_action, set_action_error, update_action_status
from app.gmail_drafts import create_gmail_draft
from app.gmail_service import NotAuthenticatedError
from app.calendar_events import create_tentative_event

router = APIRouter(prefix="/actions", tags=["approval"])


@router.post("/{action_id}/approve")
def approve_action(action_id: int):
    action = get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    if action["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Action is already {action['status']}")

    if action["category"] == "reply":
        if not action["draft_text"]:
            raise HTTPException(status_code=400, detail="No draft text to approve. Generate a draft first.")
        if action["source"] != "real":
            # Demo actions are for testing/showing the flow; they never touch a real inbox.
            update_action_status(action_id, "approved")
            return {"id": action_id, "status": "approved", "note": "Demo action: no real Gmail draft created."}
        try:
            gmail_draft_id = create_gmail_draft(
                to=action["sender_email"], subject=action["subject"], body=action["draft_text"],
            )
        except NotAuthenticatedError:
            raise HTTPException(status_code=401, detail="Not signed in. Visit /auth/login first.")
        except RuntimeError as exc:
            set_action_error(action_id, str(exc))
            raise HTTPException(status_code=502, detail=str(exc))
        update_action_status(action_id, "approved")
        return {"id": action_id, "status": "approved", "gmail_draft_id": gmail_draft_id}

    if action["category"] == "schedule":
        if not action["proposed_time"]:
            raise HTTPException(status_code=400, detail="Please propose a time before approving this meeting.")
        if action["source"] != "real":
            update_action_status(action_id, "approved")
            return {"id": action_id, "status": "approved", "note": "Demo action: no real calendar event created."}
        try:
            event_id = create_tentative_event(
                summary=f"Re: {action['subject']}",
                start_iso=action["proposed_time"],
                attendee_email=action["sender_email"],
            )
        except NotAuthenticatedError:
            raise HTTPException(status_code=401, detail="Not signed in. Visit /auth/login first.")
        except RuntimeError as exc:
            set_action_error(action_id, str(exc))
            raise HTTPException(status_code=502, detail=str(exc))
        update_action_status(action_id, "approved")
        return {"id": action_id, "status": "approved", "calendar_event_id": event_id}

    # deadline actions: tracked in Step 19, no external side effect to approve here.
    update_action_status(action_id, "approved")
    return {"id": action_id, "status": "approved"}


@router.post("/{action_id}/reject")
def reject_action(action_id: int):
    action = get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    if action["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Action is already {action['status']}")
    update_action_status(action_id, "rejected")
    return {"id": action_id, "status": "rejected"}
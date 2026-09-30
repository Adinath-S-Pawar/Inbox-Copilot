from app.db import db_session


def create_pending_action(*, source: str, email_id: str, category: str, subject: str,
                            sender_name: str, sender_email: str, reason: str,
                            draft_text: str | None = None, proposed_time: str | None = None) -> int | None:
    """Insert a new pending action. Returns its id, or None if one already exists
    for this (source, email_id) — triage can be re-run safely without duplicating."""
    with db_session() as conn:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO actions
               (source, email_id, category, subject, sender_name, sender_email, reason, draft_text, proposed_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source, email_id, category, subject, sender_name, sender_email, reason, draft_text, proposed_time),
        )
        return cursor.lastrowid if cursor.rowcount else None


def list_actions(*, source: str | None = None, status: str | None = None) -> list[dict]:
    query = "SELECT * FROM actions WHERE 1=1"
    params: list = []
    if source:
        query += " AND source = ?"
        params.append(source)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_action(action_id: int) -> dict | None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM actions WHERE id = ?", (action_id,)).fetchone()
        return dict(row) if row else None


def update_action_status(action_id: int, status: str) -> bool:
    with db_session() as conn:
        cursor = conn.execute("UPDATE actions SET status = ? WHERE id = ?", (status, action_id))
        return cursor.rowcount > 0
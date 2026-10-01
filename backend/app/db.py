import sqlite3
from contextlib import contextmanager

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL CHECK (source IN ('real', 'demo')),
    email_id TEXT NOT NULL,
    category TEXT NOT NULL,
    subject TEXT NOT NULL,
    sender_name TEXT NOT NULL,
    sender_email TEXT NOT NULL,
    reason TEXT NOT NULL,
    draft_text TEXT,
    proposed_time TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source, email_id)
);

CREATE TABLE IF NOT EXISTS deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL CHECK (source IN ('real', 'demo')),
    email_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    due_date TEXT,
    body TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source, email_id)
);
"""

def _migrate_existing_tables(conn) -> None:
    """Add columns to tables that existed before this column was introduced."""
    columns = [row[1] for row in conn.execute("PRAGMA table_info(actions)").fetchall()]
    if "body" not in columns:
        conn.execute("ALTER TABLE actions ADD COLUMN body TEXT")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_file)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["status"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        _migrate_existing_tables(conn)


@contextmanager
def db_session():
    """Yield a connection and commit on success, roll back on error, always close."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
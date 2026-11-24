import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "data/helpdesk.db")


@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    with get_conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Open',
                session_id TEXT DEFAULT 'default',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                detail TEXT DEFAULT '',
                created_at TEXT
            )
        """)
        # ticket ids start from 101
        c.execute("""
            INSERT INTO sqlite_sequence(name, seq)
            SELECT 'tickets', 100
            WHERE NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name='tickets')
        """)


def audit(action: str, detail: str = "") -> None:
    with get_conn() as c:
        c.execute("INSERT INTO audit_log(action, detail, created_at) VALUES (?,?,?)",
                  (action, detail, now()))


def add_ticket(title: str, description: str = "", priority: str = "Medium",
               session_id: str = "default") -> dict:
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO tickets(title, description, priority, status, session_id, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (title, description, priority, "Open", session_id, now(), now()),
        )
        ticket_id = cur.lastrowid
    audit("create_ticket", f"#{ticket_id} {title} ({priority})")
    return get_ticket(ticket_id)


def get_ticket(ticket_id: int) -> dict | None:
    with get_conn() as c:
        row = c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    return dict(row) if row else None


def list_tickets() -> list[dict]:
    with get_conn() as c:
        rows = c.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def update_status(ticket_id: int, status: str) -> dict | None:
    with get_conn() as c:
        c.execute("UPDATE tickets SET status=?, updated_at=? WHERE id=?",
                  (status, now(), ticket_id))
    audit("update_status", f"#{ticket_id} -> {status}")
    return get_ticket(ticket_id)
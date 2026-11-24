


import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


# ------------------------------------
# DATABASE CONFIGURATION
# ------------------------------------

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")


def conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is missing. Check your .env or Docker environment."
        )

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


# ------------------------------------
# DATABASE INITIALIZATION
# ------------------------------------

def init_db():
    with conn() as c:

        # Tickets table
        c.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Open',
                thread_id TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        c.execute("""
            ALTER TABLE tickets
            ADD COLUMN IF NOT EXISTS session_id TEXT
        """)

        c.execute("""
            ALTER TABLE tickets
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ
        """)

        c.execute("""
            ALTER TABLE tickets
            ADD COLUMN IF NOT EXISTS source_ticket_id INTEGER
        """)

        c.execute("""
            ALTER TABLE tickets
            ADD COLUMN IF NOT EXISTS source_database TEXT
        """)

        c.execute("""
            UPDATE tickets
            SET session_id = thread_id
            WHERE session_id IS NULL AND thread_id IS NOT NULL
        """)

        c.execute("""
            UPDATE tickets
            SET updated_at = created_at
            WHERE updated_at IS NULL
        """)

        # Audit log table
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id BIGSERIAL PRIMARY KEY,
                action TEXT NOT NULL,
                detail TEXT DEFAULT '',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                source_audit_id INTEGER,
                source_database TEXT
            )
        """)

        # Notifications table
        c.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id BIGSERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                message TEXT DEFAULT '',
                type TEXT DEFAULT 'system',
                target TEXT DEFAULT 'tickets',
                session_id TEXT DEFAULT 'default',
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Add ticket_id to existing notification tables.
        c.execute("""
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS ticket_id INTEGER
        """)

        # Notification index
        c.execute("""
            CREATE INDEX IF NOT EXISTS notifications_session_created_idx
            ON notifications(session_id, created_at DESC)
        """)

        # Source tracking indexes
        c.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS tickets_source_tracking_unique
            ON tickets(source_database, source_ticket_id)
            WHERE source_database IS NOT NULL
              AND source_ticket_id IS NOT NULL
        """)

        c.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS audit_source_tracking_unique
            ON audit_log(source_database, source_audit_id)
            WHERE source_database IS NOT NULL
              AND source_audit_id IS NOT NULL
        """)

        # Add a default ticket only when the table is empty.
        n = c.execute(
            "SELECT COUNT(*) AS n FROM tickets"
        ).fetchone()["n"]

        if n == 0:
            c.execute("""
                INSERT INTO tickets(id, title, priority)
                VALUES (101, 'Password reset not working', 'Low')
            """)

            c.execute("""
                SELECT setval(
                    pg_get_serial_sequence('tickets', 'id'), 101
                )
            """)


# ------------------------------------
# NOTIFICATIONS
# ------------------------------------

def create_notification(
    title,
    message="",
    notification_type="system",
    target="tickets",
    session_id="default",
    ticket_id=None
):
    with conn() as c:
        return c.execute("""
            INSERT INTO notifications(
                title,
                message,
                type,
                target,
                session_id,
                ticket_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            title,
            message,
            notification_type,
            target,
            session_id or "default",
            ticket_id
        )).fetchone()


def list_notifications(session_id="default"):
    with conn() as c:
        return c.execute("""
            SELECT *
            FROM notifications
            WHERE session_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 100
        """, (
            session_id or "default",
        )).fetchall()


def mark_notification_read(notification_id, session_id="default"):
    with conn() as c:
        return c.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE id = %s AND session_id = %s
            RETURNING *
        """, (
            notification_id,
            session_id or "default"
        )).fetchone()


def mark_all_notifications_read(session_id="default"):
    with conn() as c:
        result = c.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE session_id = %s
              AND is_read = FALSE
        """, (
            session_id or "default",
        ))

        return {
            "updated": result.rowcount
        }


# ------------------------------------
# TICKETS
# ------------------------------------

def create_ticket(
    title,
    description="",
    priority="Medium",
    thread_id=None,
    session_id=None
):
    session_ref = session_id or thread_id or "default"

    with conn() as c:

        # Create ticket
        ticket = c.execute("""
            INSERT INTO tickets(
                title,
                description,
                priority,
                thread_id,
                session_id,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """, (
            title,
            description,
            priority,
            thread_id or session_ref,
            session_ref
        )).fetchone()

        # Save audit log
        c.execute("""
            INSERT INTO audit_log(action, detail)
            VALUES (%s, %s)
        """, (
            "create_ticket",
            f"#{ticket['id']} {title} ({priority})"
        ))

        # Create notification with exact ticket ID.
        c.execute("""
            INSERT INTO notifications(
                title,
                message,
                type,
                target,
                session_id,
                ticket_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            f"Ticket #{ticket['id']} created",
            title or "Your support request was submitted.",
            "ticket",
            "tickets",
            session_ref,
            ticket["id"]
        ))

        return ticket


def get_ticket(ticket_id):
    with conn() as c:
        return c.execute("""
            SELECT *
            FROM tickets
            WHERE id = %s
        """, (
            ticket_id,
        )).fetchone()


def list_tickets():
    with conn() as c:
        return c.execute("""
            SELECT *
            FROM tickets
            ORDER BY id DESC
        """).fetchall()


def update_status(ticket_id, status):
    with conn() as c:

        # Update ticket status
        ticket = c.execute("""
            UPDATE tickets
            SET status = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """, (
            status,
            ticket_id
        )).fetchone()

        if ticket:

            # Save audit log
            c.execute("""
                INSERT INTO audit_log(action, detail)
                VALUES (%s, %s)
            """, (
                "update_status",
                f"#{ticket_id} -> {status}"
            ))

            # Create notification with exact ticket ID.
            c.execute("""
                INSERT INTO notifications(
                    title,
                    message,
                    type,
                    target,
                    session_id,
                    ticket_id
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                f"Ticket #{ticket_id} status updated",
                f"{ticket['title']} is now {status}.",
                "ticket",
                "tickets",
                ticket.get("session_id") or "default",
                ticket_id
            ))

        return ticket

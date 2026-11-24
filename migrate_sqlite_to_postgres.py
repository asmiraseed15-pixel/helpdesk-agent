import sqlite3
from pathlib import Path

from app.tickets import conn

SOURCE_DATABASE = "sqlite_helpdesk"
SQLITE_FILE = Path(__file__).resolve().parent / "data" / "helpdesk.db"


def migrate():
    if not SQLITE_FILE.exists():
        raise FileNotFoundError(SQLITE_FILE)

    source = sqlite3.connect(
        f"file:{SQLITE_FILE.as_posix()}?mode=ro",
        uri=True
    )
    source.row_factory = sqlite3.Row

    tickets = source.execute(
        "SELECT * FROM tickets ORDER BY id"
    ).fetchall()

    audit_logs = source.execute(
        "SELECT * FROM audit_log ORDER BY id"
    ).fetchall()

    inserted_tickets = 0
    skipped_tickets = 0
    inserted_audits = 0
    skipped_audits = 0

    try:
        with conn() as pg:
            for ticket in tickets:
                result = pg.execute("""
                    INSERT INTO tickets (
                        title,
                        description,
                        priority,
                        status,
                        thread_id,
                        session_id,
                        created_at,
                        updated_at,
                        source_ticket_id,
                        source_database
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    ON CONFLICT (
                        source_database,
                        source_ticket_id
                    )
                    WHERE source_database IS NOT NULL
                      AND source_ticket_id IS NOT NULL
                    DO NOTHING
                    RETURNING id
                """, (
                    ticket["title"],
                    ticket["description"],
                    ticket["priority"],
                    ticket["status"],
                    ticket["session_id"],
                    ticket["session_id"],
                    ticket["created_at"],
                    ticket["updated_at"],
                    ticket["id"],
                    SOURCE_DATABASE
                )).fetchone()

                if result:
                    inserted_tickets += 1
                    print(
                        f"Imported SQLite ticket #{ticket['id']} "
                        f"as PostgreSQL ticket #{result['id']}"
                    )
                else:
                    skipped_tickets += 1
                    print(
                        f"Skipped already migrated ticket #{ticket['id']}"
                    )

            for audit in audit_logs:
                result = pg.execute("""
                    INSERT INTO audit_log (
                        action,
                        detail,
                        created_at,
                        source_audit_id,
                        source_database
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (
                        source_database,
                        source_audit_id
                    )
                    WHERE source_database IS NOT NULL
                      AND source_audit_id IS NOT NULL
                    DO NOTHING
                    RETURNING id
                """, (
                    audit["action"],
                    audit["detail"],
                    audit["created_at"],
                    audit["id"],
                    SOURCE_DATABASE
                )).fetchone()

                if result:
                    inserted_audits += 1
                else:
                    skipped_audits += 1

        print("\n--- MIGRATION SUMMARY ---")
        print("SQLite tickets found:", len(tickets))
        print("Tickets imported:", inserted_tickets)
        print("Tickets skipped:", skipped_tickets)
        print("SQLite audit logs found:", len(audit_logs))
        print("Audit logs imported:", inserted_audits)
        print("Audit logs skipped:", skipped_audits)
        print("Migration completed.")

    finally:
        source.close()


if __name__ == "__main__":
    migrate()

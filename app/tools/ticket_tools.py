from app import tickets as ticket_db

PRIORITIES = {"Low", "Medium", "High", "Critical"}


def create_ticket(
    title: str,
    description: str = "",
    priority: str = "Medium",
    session_id: str = "default"
) -> dict:
    """Create a new IT support ticket in PostgreSQL."""

    priority = priority.capitalize()

    if priority not in PRIORITIES:
        priority = "Medium"

    ticket = ticket_db.create_ticket(
        title=title,
        description=description,
        priority=priority,
        thread_id=session_id,
        session_id=session_id
    )

    return dict(ticket)


def check_ticket_status(ticket_id: int) -> dict:
    """Check the status of an existing PostgreSQL ticket."""

    ticket = ticket_db.get_ticket(int(ticket_id))

    if not ticket:
        return {
            "found": False,
            "ticket_id": int(ticket_id)
        }

    return {
        "found": True,
        **dict(ticket)
    }


def list_tickets() -> list[dict]:
    """List all PostgreSQL tickets, newest first."""

    return [
        dict(ticket)
        for ticket in ticket_db.list_tickets()
    ]


from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import chat, tickets as ticket_db
from app.agent.graph import run as run_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    ticket_db.init_db()
    yield


app = FastAPI(title="IT Helpdesk Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    message: str
    session_id: str = "default"


class NotificationIn(BaseModel):
    title: str
    message: str = ""
    type: str = "system"
    target: str = "tickets"
    session_id: str = "default"


@app.get("/")
def root():
    return {"status": "ok", "service": "helpdesk-agent"}


@app.post("/chat")
def chat_endpoint(body: ChatIn):
    return run_agent(body.message, body.session_id)


@app.post("/tickets")
def new_ticket(session_id: str = "default"):
    return chat.create_ticket(session_id)


@app.get("/tickets")
def list_tickets():
    return ticket_db.list_tickets()


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    t = ticket_db.get_ticket(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t


# ------------------------------------
# NOTIFICATION APIs
# ------------------------------------

@app.get("/notifications")
def get_notifications(session_id: str = "default"):
    return ticket_db.list_notifications(session_id)


@app.post("/notifications")
def new_notification(body: NotificationIn):
    return ticket_db.create_notification(
        title=body.title,
        message=body.message,
        notification_type=body.type,
        target=body.target,
        session_id=body.session_id
    )


@app.patch("/notifications/{notification_id}/read")
def read_notification(
    notification_id: int,
    session_id: str = "default"
):
    notification = ticket_db.mark_notification_read(
        notification_id,
        session_id
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    return notification


@app.patch("/notifications/read-all")
def read_all_notifications(session_id: str = "default"):
    return ticket_db.mark_all_notifications_read(session_id)


@app.get("/problems")
def problems():
    out = []

    for f in sorted(Path("data/kb").glob("*.md")):
        lines = f.read_text(encoding="utf-8-sig").splitlines()
        title = lines[0][2:].strip()

        cat = next(
            (
                l.split(":", 1)[1].strip()
                for l in lines
                if l.lower().startswith("category:")
            ),
            "General"
        )

        out.append({
            "title": title,
            "category": cat
        })

    return out

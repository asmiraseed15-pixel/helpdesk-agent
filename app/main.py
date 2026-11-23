
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import chat

app = FastAPI(title="IT Helpdesk Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    message: str
    session_id: str = "default"


@app.get("/")
def root():
    return {"status": "ok", "service": "helpdesk-agent"}


@app.post("/chat")
def chat_endpoint(body: ChatIn):
    return chat.answer(body.message, body.session_id)


@app.post("/tickets")
def new_ticket(session_id: str = "default"):
    return chat.create_ticket(session_id)


@app.get("/tickets")
def list_tickets():
    return chat.tickets


@app.get("/problems")
def problems():
    out = []
    for f in sorted(Path("data/kb").glob("*.md")):
        lines = f.read_text(encoding="utf-8-sig").splitlines()
        title = lines[0][2:].strip()
        cat = next((l.split(":", 1)[1].strip() for l in lines
                    if l.lower().startswith("category:")), "General")
        out.append({"title": title, "category": cat})
    return out

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.rag.rewrite import rewrite_query
from app.rag.retriever import search

load_dotenv()
try:
    sys.stdout.reconfigure(encoding="utf-8")  # Tamil output on Windows
except Exception:
    pass

KB_DIR = Path("data/kb")
MIN_SCORE = 0.35

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY"),
)

SYSTEM = """You are an IT helpdesk agent.
Answer ONLY using the KB article given. Do not invent steps.

Language rule: reply in the same language and style the user wrote in.
- English -> English
- Tanglish (Tamil in English letters) -> Tanglish
- Tamil script -> Tamil script
Keep technical terms, commands and tool names in English.

Format: one short friendly line, then numbered troubleshooting steps.
End by asking whether it worked, and mention you can create a ticket if not.
Keep it short."""

NOT_FOUND = """You are an IT helpdesk agent. You could not find a matching article
for the user's problem. Reply in the same language and style as the user
(English, Tanglish or Tamil script). Ask one short clarifying question
and say you can create a ticket. Keep it to 2 sentences.

User message: {q}"""

sessions = {}   # session_id -> {"history": [...], "last_title": str | None}
tickets = []    # in-memory for now (PostgreSQL later)


def get_session(session_id: str) -> dict:
    return sessions.setdefault(session_id, {"history": [], "last_title": None})


def answer(user_q: str, session_id: str = "cli") -> dict:
    s = get_session(session_id)
    rq = rewrite_query(user_q)
    hits = search(rq)
    best = hits[0] if hits else None

    if not best or best["score"] < MIN_SCORE:
        s["last_title"] = None
        reply = llm.invoke(NOT_FOUND.format(q=user_q)).content.strip()
        return {
            "reply": reply,
            "trace": {"rewritten": rq, "match": None,
                      "score": best["score"] if best else None,
                      "actions": "", "escalate": ""},
        }

    meta = best["meta"]
    s["last_title"] = meta["title"]
    article = (KB_DIR / meta["source"]).read_text(encoding="utf-8-sig")
    convo = "\n".join(s["history"][-6:])
    prompt = (
        f"{SYSTEM}\n\nKB ARTICLE:\n{article}\n\n"
        f"CONVERSATION SO FAR:\n{convo}\n\n"
        f"USER: {user_q}"
    )
    reply = llm.invoke(prompt).content.strip()
    s["history"] += [f"USER: {user_q}", f"AGENT: {reply}"]

    return {
        "reply": reply,
        "trace": {"rewritten": rq, "match": meta["title"], "score": best["score"],
                  "actions": meta["actions"], "escalate": meta["escalate"]},
    }


def create_ticket(session_id: str = "cli") -> dict:
    s = get_session(session_id)
    ticket = {
        "id": 101 + len(tickets),
        "title": s["last_title"] or "General issue",
        "status": "Open",
    }
    tickets.append(ticket)
    return ticket


def main():
    print("IT Helpdesk Agent (English / Tanglish / Tamil)")
    print("Commands: /ticket  create a ticket | /exit  quit\n")
    while True:
        try:
            q = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in ("/exit", "exit", "quit"):
            break
        if q.lower() == "/ticket":
            t = create_ticket()
            print(f"\nAgent: Ticket #{t['id']} created for: {t['title']}.\n")
            continue
        try:
            r = answer(q)
            t = r["trace"]
            print(f"   [searched: {t['rewritten']} | match: {t['match']} ({t['score']})]")
            print(f"\nAgent: {r['reply']}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()


import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app import tickets as ticket_db
from app.lang import detect, t as msg
from app.rag.rewrite import rewrite_query
from app.rag.retriever import search


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# =========================================================
# CONFIGURATION
# =========================================================

KB_DIR = Path("data/kb")
MIN_SCORE = 0.35

PRIORITIES = {"Low", "Medium", "High", "Critical"}


# =========================================================
# LLM
# =========================================================

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY"),
)


# =========================================================
# PROMPTS
# =========================================================

SYSTEM = """You are an IT helpdesk agent.
Answer ONLY using the KB article given. Do not invent steps.
Reply in the language given under REPLY LANGUAGE. Never switch language.
Keep technical terms, commands and tool names in English.

Format: one short friendly line, then numbered troubleshooting steps.
End by asking whether it worked, and mention you can create a ticket if not.
Keep it short."""


NOT_FOUND = """You are an IT helpdesk agent. You could not find a matching article
for the user's problem. Ask one short clarifying question
and say you can create a ticket. Keep it to 2 sentences.

User message: {q}"""


LANG_HINT = {
    "en": "English",
    "tanglish": "Tanglish (Tamil written in English letters, NEVER Tamil script)",
    "ta": "Tamil script",
}


# =========================================================
# REGEX
# =========================================================

TICKET_RE = re.compile(r"ticket\s*#?\s*(\d+)", re.I)

STATUS_RE = re.compile(
    r"status|enna|state|check|paar|\u0BA8\u0BBF\u0BB2\u0BC8",
    re.I
)

RESOLVED_RE = re.compile(
    r"\b(thanks|thank you|works now|working now|it works|resolved|fixed|"
    r"sari aachu|work aagudhu|nandri)\b|\u0BA8\u0BA9\u0BCD\u0BB1\u0BBF",
    re.I
)


# =========================================================
# SESSION MANAGEMENT
# =========================================================

sessions = {}


def get_session(session_id: str) -> dict:
    session = sessions.setdefault(
        session_id,
        {
            "history": [],
            "last_title": None,
            "last_description": "",
            "last_priority": "Medium",
            "lang": "en",
        }
    )

    # Backward compatibility for sessions created before these fields.
    session.setdefault("history", [])
    session.setdefault("last_title", None)
    session.setdefault("last_description", "")
    session.setdefault("last_priority", "Medium")
    session.setdefault("lang", "en")

    return session


# =========================================================
# SAVE LATEST ISSUE INFORMATION
# =========================================================

def save_issue_context(
    session_id: str,
    title=None,
    description="",
    priority="Medium"
):
    session = get_session(session_id)

    if title:
        session["last_title"] = title

    session["last_description"] = description or ""

    priority = str(priority or "Medium").capitalize()

    if priority not in PRIORITIES:
        priority = "Medium"

    session["last_priority"] = priority


# =========================================================
# LEGACY CHAT ANSWER
# =========================================================

def answer(user_q: str, session_id: str = "cli") -> dict:
    session = get_session(session_id)

    lang = detect(user_q)
    session["lang"] = lang

    # -----------------------------------------------------
    # TICKET STATUS
    # -----------------------------------------------------

    match = TICKET_RE.search(user_q)

    if match and STATUS_RE.search(user_q):
        ticket = ticket_db.get_ticket(int(match.group(1)))

        reply = (
            msg(
                "ticket_status",
                lang,
                id=ticket["id"],
                title=ticket["title"],
                status=ticket["status"]
            )
            if ticket
            else msg(
                "ticket_missing",
                lang,
                id=match.group(1)
            )
        )

        return {
            "reply": reply,
            "trace": {
                "intent": "ticket_status"
            }
        }

    # -----------------------------------------------------
    # RESOLVED
    # -----------------------------------------------------

    if RESOLVED_RE.search(user_q):
        return {
            "reply": msg("resolved", lang),
            "trace": {
                "intent": "resolved"
            }
        }

    # -----------------------------------------------------
    # RAG SEARCH
    # -----------------------------------------------------

    rewritten_query = rewrite_query(user_q)
    hits = search(rewritten_query)

    best = hits[0] if hits else None

    if not best or best["score"] < MIN_SCORE:

        session["last_title"] = None
        session["last_description"] = user_q
        session["last_priority"] = "Medium"

        prompt = (
            NOT_FOUND.format(q=user_q)
            + f"\n\nREPLY LANGUAGE (mandatory): {LANG_HINT[lang]}"
        )

        reply = llm.invoke(prompt).content.strip()

        session["history"] += [
            f"USER: {user_q}",
            f"AGENT: {reply}",
        ]

        return {
            "reply": reply,
            "priority": "Medium",
            "trace": {
                "intent": "not_found",
                "rewritten": rewritten_query,
                "match": None,
                "score": best["score"] if best else None,
                "actions": "",
                "escalate": "",
            },
        }

    # -----------------------------------------------------
    # KNOWLEDGE BASE ANSWER
    # -----------------------------------------------------

    meta = best["meta"]

    session["last_title"] = meta["title"]
    session["last_description"] = user_q
    session["last_priority"] = "Medium"

    article = (
        KB_DIR / meta["source"]
    ).read_text(encoding="utf-8-sig")

    conversation = "\n".join(session["history"][-6:])

    prompt = (
        f"{SYSTEM}\n\n"
        f"REPLY LANGUAGE (mandatory): {LANG_HINT[lang]}\n\n"
        f"KB ARTICLE:\n{article}\n\n"
        f"CONVERSATION SO FAR:\n{conversation}\n\n"
        f"USER: {user_q}"
    )

    reply = llm.invoke(prompt).content.strip()

    session["history"] += [
        f"USER: {user_q}",
        f"AGENT: {reply}",
    ]

    return {
        "reply": reply,
        "priority": "Medium",
        "trace": {
            "intent": "issue",
            "rewritten": rewritten_query,
            "match": meta["title"],
            "score": best["score"],
            "actions": meta["actions"],
            "escalate": meta["escalate"],
        },
    }


# =========================================================
# CREATE TICKET
# =========================================================

def create_ticket(session_id: str = "cli") -> dict:
    session = get_session(session_id)

    title = (
        session.get("last_title")
        or "General issue"
    )

    description = (
        session.get("last_description")
        or "\n".join(session["history"][-6:])
        or title
    )

    priority = str(
        session.get("last_priority") or "Medium"
    ).capitalize()

    if priority not in PRIORITIES:
        priority = "Medium"

    # Save ticket with the detected priority.
    ticket = ticket_db.create_ticket(
        title=title,
        description=description,
        priority=priority,
        thread_id=session_id,
        session_id=session_id,
    )

    ticket["message"] = msg(
        "ticket_created",
        session.get("lang", "en"),
        id=ticket["id"],
        title=ticket["title"]
    )

    return ticket


# =========================================================
# CLI
# =========================================================

def main():
    print("IT Helpdesk Agent (English / Tanglish / Tamil)")
    print("Commands: /ticket  create a ticket | /exit  quit\n")

    while True:
        try:
            question = input("You: ").strip()

        except (EOFError, KeyboardInterrupt):
            break

        if not question:
            continue

        if question.lower() in ("/exit", "exit", "quit"):
            break

        if question.lower() == "/ticket":
            try:
                ticket = create_ticket()

                print(
                    f"\nAgent: {ticket['message']}"
                    f"\nPriority: {ticket['priority']}"
                    f"\nStatus: {ticket['status']}\n"
                )

            except Exception as error:
                print(f"\nError creating ticket: {error}\n")

            continue

        try:
            result = answer(question)

            trace = result["trace"]

            print(
                f"   [intent: {trace.get('intent')} | "
                f"match: {trace.get('match')} "
                f"({trace.get('score')})]"
            )

            print(f"\nAgent: {result['reply']}\n")

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()

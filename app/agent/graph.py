


import json
import re
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.chat import (
    KB_DIR,
    MIN_SCORE,
    NOT_FOUND,
    SYSTEM,
    get_session,
    llm,
)
from app.rag.retriever import search
from app.rag.rewrite import rewrite_query
from app.tools.password_tools import reset_password_guide
from app.tools.ticket_tools import check_ticket_status, create_ticket


# =========================================================
# LANGUAGE RULE
# =========================================================

LANG_RULE = (
    "Reply in the same language and style the user uses. "
    "English -> English, Tanglish -> Tanglish, Tamil script -> Tamil script. "
    "Keep technical terms, commands and tool names in English. "
    "Be clear, friendly and concise."
)


# =========================================================
# PRIORITY LEVELS
# =========================================================

PRIORITIES = {"Low", "Medium", "High", "Critical"}

IT_INTENTS = {"issue", "password_reset"}


# =========================================================
# INTENT CLASSIFICATION
# =========================================================

INTENTS = {
    "issue",
    "password_reset",
    "ticket_status",
    "create_ticket",
    "resolved",
    "general",
    "other",
}


CLASSIFY = """You are an intelligent AI assistant intent classifier.

Understand the user's actual intention from the current message and conversation history.

The user may ask questions in English, Tamil script, or Tanglish.

Return ONLY one valid JSON object:
{"intent": "general", "ticket_id": null, "priority": null}

Choose exactly one intent:

- "issue": IT problems, troubleshooting, hardware, software, network,
  Wi-Fi, printer, laptop, internet, or technical support questions.

- "password_reset": Forgot password, reset password, or locked account.

- "ticket_status": Asking about an existing support ticket status.

- "create_ticket": Explicitly requesting a new support ticket.

- "resolved": Confirming that a previously discussed IT problem is fixed.

- "general": Any non-IT question, general knowledge, education, coding,
  programming, writing, translation, explanations, calculations,
  comparisons, advice, or other everyday questions.

- "other": Greetings, casual conversation, or unclear messages
  that do not contain a specific question or request.

PRIORITY CLASSIFICATION:

For "issue" and "password_reset", assign one priority:

- Low: Minor inconvenience, non-urgent request, or limited impact.
- Medium: Normal IT issue affecting one user with a reasonable workaround.
- High: Important work blocked, major functionality unavailable,
  or urgent issue affecting a user or team.
- Critical: Widespread outage, many users fully blocked,
  or a critical business service completely unavailable.

For all other intents, priority must be null.

IMPORTANT:
- Do not classify general knowledge questions as IT issues.
- Do not classify every message as an IT support request.
- Follow the conversation context when understanding follow-up messages.
- Only use "create_ticket" when the user clearly requests ticket creation.
- Never create tickets just because the user says an issue still exists.
- A question about programming concepts is general, not an IT support issue.
- A question about fixing a computer or network problem is an IT issue.
- Do not assign Critical just because the user uses urgent language.
- Consider actual impact and number of affected users.

ticket_id: Ticket number if mentioned, otherwise null.
priority: Low, Medium, High, Critical, or null.
"""


# =========================================================
# GRAPH STATE
# =========================================================

class State(TypedDict, total=False):
    message: str
    session_id: str
    intent: str
    ticket_id: Optional[int]
    priority: Optional[str]
    rewritten: str
    best: Optional[dict]
    reply: str
    ticket: Optional[dict]
    resolved: bool


# =========================================================
# COMMON FUNCTIONS
# =========================================================

def ask(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content.strip()


def convo_text(session: dict) -> str:
    return "\n".join(session["history"][-6:])


def remember(state: State, reply: str) -> None:
    session = get_session(state["session_id"])

    session["history"] += [
        f"USER: {state['message']}",
        f"AGENT: {reply}",
    ]


def helper_prompt(task: str, state: State, data=None) -> str:
    prompt = (
        f"You are an IT helpdesk agent. {LANG_RULE}\n"
        f"{task}\n"
    )

    if data is not None:
        prompt += (
            "\nDATA:\n"
            f"{json.dumps(data, ensure_ascii=False, default=str)}\n"
        )

    return prompt + f"\nUser message: {state['message']}"


def save_issue_context(state: State, title=None) -> None:
    """Save the latest IT issue details for later ticket creation."""

    session = get_session(state["session_id"])

    if title:
        session["last_title"] = title

    session["last_priority"] = state.get("priority") or "Medium"
    session["last_description"] = state["message"]


# =========================================================
# UNDERSTAND USER MESSAGE
# =========================================================

def understand(state: State) -> dict:
    session = get_session(state["session_id"])

    prompt = (
        CLASSIFY
        + "\n\nConversation so far:\n"
        + convo_text(session)
        + "\n\nUser message: "
        + state["message"]
    )

    data = {}

    try:
        response = ask(prompt)
        match = re.search(r"\{.*\}", response, re.S)

        if match:
            data = json.loads(match.group(0))

    except (json.JSONDecodeError, TypeError, ValueError):
        data = {}

    except Exception:
        data = {}

    intent = data.get("intent")

    if intent not in INTENTS:
        intent = "general"

    ticket_id = data.get("ticket_id")

    try:
        ticket_id = int(ticket_id) if ticket_id is not None else None
    except (TypeError, ValueError):
        ticket_id = None

    # Extract ticket number directly if classifier missed it.
    if intent == "ticket_status" and ticket_id is None:
        match = re.search(r"\b\d+\b", state["message"])

        if match:
            ticket_id = int(match.group(0))

    # Priority is meaningful only for IT support issues.
    priority = None

    if intent in IT_INTENTS:
        detected_priority = str(
            data.get("priority") or "Medium"
        ).capitalize()

        if detected_priority not in PRIORITIES:
            detected_priority = "Medium"

        priority = detected_priority

    return {
        "intent": intent,
        "ticket_id": ticket_id,
        "priority": priority,
    }


# =========================================================
# IT KNOWLEDGE BASE SEARCH
# =========================================================

def rag_search(state: State) -> dict:
    rewritten_query = rewrite_query(state["message"])
    hits = search(rewritten_query)

    return {
        "rewritten": rewritten_query,
        "best": hits[0] if hits else None,
    }


# =========================================================
# ANSWER FROM KNOWLEDGE BASE
# =========================================================

def answer_kb(state: State) -> dict:
    session = get_session(state["session_id"])

    meta = state["best"]["meta"]

    session["last_title"] = meta["title"]

    save_issue_context(state, meta["title"])

    article = (
        KB_DIR / meta["source"]
    ).read_text(encoding="utf-8-sig")

    prompt = (
        f"{SYSTEM}\n\n"
        f"KB ARTICLE:\n{article}\n\n"
        f"CONVERSATION SO FAR:\n{convo_text(session)}\n\n"
        f"USER: {state['message']}"
    )

    reply = ask(prompt)

    remember(state, reply)

    return {"reply": reply}


# =========================================================
# NO KNOWLEDGE BASE MATCH
# =========================================================

def not_found(state: State) -> dict:
    session = get_session(state["session_id"])

    session["last_title"] = None

    save_issue_context(state)

    reply = ask(
        NOT_FOUND.format(q=state["message"])
    )

    remember(state, reply)

    return {"reply": reply}


# =========================================================
# GENERAL PURPOSE AI ASSISTANT
# =========================================================

def general(state: State) -> dict:
    session = get_session(state["session_id"])

    prompt = (
        "You are a helpful, intelligent, general-purpose AI assistant.\n\n"

        "Answer the user's actual question directly and accurately.\n\n"

        "You can help with:\n"
        "- General knowledge\n"
        "- Education and learning\n"
        "- Python and programming\n"
        "- React, JavaScript and web development\n"
        "- Writing letters, emails and documents\n"
        "- Translation and explanations\n"
        "- Calculations and comparisons\n"
        "- Planning and everyday questions\n"
        "- Technical concepts and interview preparation\n\n"

        "IMPORTANT RULES:\n"
        "- Do not force the conversation into IT helpdesk support.\n"
        "- Do not add unnecessary IT support closing messages.\n"
        "- Do not say that you can only answer IT questions.\n"
        "- Use conversation history to understand follow-up questions.\n"
        "- Give examples when they help the explanation.\n"
        "- If information may be outdated or uncertain, clearly mention it.\n"
        "- Never pretend to have live information when you do not.\n"
        "- Answer in the user's language and style.\n"

        f"\n{LANG_RULE}\n\n"
        f"CONVERSATION SO FAR:\n{convo_text(session)}\n\n"
        f"USER: {state['message']}"
    )

    reply = ask(prompt)

    remember(state, reply)

    return {"reply": reply}


# =========================================================
# PASSWORD RESET
# =========================================================

def password(state: State) -> dict:
    session = get_session(state["session_id"])

    session["last_title"] = "Password reset"

    save_issue_context(state, "Password reset")

    task = (
        "Explain the password reset steps from the DATA as short numbered steps. "
        "Use ONLY the provided guide. "
        "Clearly explain that identity verification (OTP) is required "
        "before any real reset. "
        "Explain that you cannot reset the password yourself. "
        "Ask whether the steps worked and offer to create a ticket if they did not."
    )

    reply = ask(
        helper_prompt(
            task,
            state,
            reset_password_guide(),
        )
    )

    remember(state, reply)

    return {"reply": reply}


# =========================================================
# CHECK TICKET STATUS
# =========================================================

def ticket_status(state: State) -> dict:
    ticket_id = state.get("ticket_id")

    if ticket_id is None:
        reply = ask(
            helper_prompt(
                "Ask the user for their ticket number in one short sentence.",
                state,
            )
        )

    else:
        task = (
            "Tell the user the status of their ticket using ONLY the DATA. "
            "If found is false, say you could not find that ticket number."
        )

        ticket_data = check_ticket_status(ticket_id)

        reply = ask(
            helper_prompt(
                task,
                state,
                ticket_data,
            )
        )

    remember(state, reply)

    return {"reply": reply}


# =========================================================
# CREATE SUPPORT TICKET
# =========================================================

def make_ticket(state: State) -> dict:
    session = get_session(state["session_id"])

    title = (
        session.get("last_title")
        or state["message"][:60]
    )

    description = (
        session.get("last_description")
        or convo_text(session)
        or state["message"]
    )

    priority = state.get("priority") or session.get(
        "last_priority",
        "Medium"
    )

    ticket = create_ticket(
        title,
        description,
        priority,
        state["session_id"],
    )

    task = (
        "A support ticket was just created. "
        "Tell the user the ticket number, title, priority and status "
        "using ONLY the DATA. "
        "Explain that the IT team will contact them."
    )

    reply = ask(
        helper_prompt(
            task,
            state,
            ticket,
        )
    )

    remember(state, reply)

    return {
        "reply": reply,
        "ticket": ticket,
    }


# =========================================================
# PROBLEM RESOLVED
# =========================================================

def resolved(state: State) -> dict:
    reply = ask(
        helper_prompt(
            "The user says the IT problem is fixed. "
            "Reply with one short happy line and ask if they need anything else.",
            state,
        )
    )

    remember(state, reply)

    return {
        "reply": reply,
        "resolved": True,
    }


# =========================================================
# GREETING AND CASUAL CONVERSATION
# =========================================================

def other(state: State) -> dict:
    session = get_session(state["session_id"])

    prompt = (
        "You are a friendly general-purpose AI assistant. "
        "Reply naturally to greetings and casual conversation. "
        "Do not force IT helpdesk support into every reply. "
        "If appropriate, briefly mention that you can help with many topics.\n"
        f"{LANG_RULE}\n\n"
        f"CONVERSATION SO FAR:\n{convo_text(session)}\n\n"
        f"USER: {state['message']}"
    )

    reply = ask(prompt)

    remember(state, reply)

    return {"reply": reply}


# =========================================================
# ROUTING
# =========================================================

def route(state: State) -> str:
    return {
        "issue": "rag_search",
        "password_reset": "password",
        "ticket_status": "ticket_status",
        "create_ticket": "make_ticket",
        "resolved": "resolved",
        "general": "general",
        "other": "other",
    }.get(state["intent"], "general")


def found(state: State) -> str:
    best = state.get("best")

    if best and best["score"] >= MIN_SCORE:
        return "answer_kb"

    return "not_found"


# =========================================================
# BUILD LANGGRAPH
# =========================================================

def build():
    graph_builder = StateGraph(State)

    nodes = {
        "understand": understand,
        "rag_search": rag_search,
        "answer_kb": answer_kb,
        "not_found": not_found,
        "general": general,
        "password": password,
        "ticket_status": ticket_status,
        "make_ticket": make_ticket,
        "resolved": resolved,
        "other": other,
    }

    for name, function in nodes.items():
        graph_builder.add_node(name, function)

    graph_builder.add_edge(START, "understand")

    graph_builder.add_conditional_edges(
        "understand",
        route,
        {
            "rag_search": "rag_search",
            "password": "password",
            "ticket_status": "ticket_status",
            "make_ticket": "make_ticket",
            "resolved": "resolved",
            "general": "general",
            "other": "other",
        },
    )

    graph_builder.add_conditional_edges(
        "rag_search",
        found,
        {
            "answer_kb": "answer_kb",
            "not_found": "not_found",
        },
    )

    end_nodes = (
        "answer_kb",
        "not_found",
        "general",
        "password",
        "ticket_status",
        "make_ticket",
        "resolved",
        "other",
    )

    for node in end_nodes:
        graph_builder.add_edge(node, END)

    return graph_builder.compile()


graph = build()


# =========================================================
# PUBLIC RUN FUNCTION
# =========================================================

def run(message: str, session_id: str = "default") -> dict:

    output = graph.invoke(
        {
            "message": message,
            "session_id": session_id,
            "resolved": False,
        }
    )

    best = output.get("best")

    # Only show resolution insights for matched IT issues.
    meta = None

    if (
        output.get("intent") == "issue"
        and best
        and best["score"] >= MIN_SCORE
    ):
        meta = best["meta"]

    intent = output.get("intent")

    # Priority is returned only for IT support questions.
    priority = (
        output.get("priority")
        if intent in IT_INTENTS
        else None
    )

    return {
        "reply": output["reply"],
        "intent": intent,
        "ticket": output.get("ticket"),
        "resolved": output.get("resolved", False),
        "priority": priority,

        "trace": {
            "rewritten": output.get("rewritten", ""),
            "match": meta["title"] if meta else None,
            "score": best["score"] if meta else None,
            "actions": meta["actions"] if meta else "",
            "escalate": meta["escalate"] if meta else "",
        },
    }

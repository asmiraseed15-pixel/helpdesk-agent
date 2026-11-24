from app.rag.retriever import search


def lookup_kb(query: str, top_k: int = 3) -> list[dict]:
    """Search the IT knowledge base and return the best matching articles."""
    hits = search(query)[:top_k]
    return [
        {
            "title": h["meta"]["title"],
            "source": h["meta"]["source"],
            "score": h["score"],
        }
        for h in hits
    ]

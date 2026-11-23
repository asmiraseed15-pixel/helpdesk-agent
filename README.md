# IT Helpdesk & Incident Resolution Agent

An IT helpdesk agent built with FastAPI and a ChromaDB knowledge base (RAG over `data/kb`).

## Run with Docker

1. Create a `.env` file one folder above the project (`../.env`) with your API keys.
2. Start the API: `docker compose up -d --build`
3. Open http://localhost:8000/docs and try the chat endpoint.

## Rebuild the knowledge base (only if `chroma_db/` is missing)

`docker compose run --rm api python scripts/make_kb.py`

## Stop

`docker compose down`
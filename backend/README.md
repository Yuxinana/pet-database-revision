# PawTrack FastAPI Backend

This backend is the standardized FastAPI entry point for the existing PawTrack
database application. It currently reuses the proven service functions in
`backend/app/services/web_server_legacy.py` so the API contract, visual UI, and
user workflows stay compatible while the codebase is migrated into smaller
modules. `backend/app/services/web_server_legacy.py` remains as a thin compatibility entry point.
The LLM SQL assistant implementation likewise lives under
`backend/app/services/llm_sql_assistant.py`, with `backend/app/services/llm_sql_assistant.py`
kept as a compatibility entry point.

Run it from the repository root:

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `PAWTRACK_RESET_DB=1` before startup if you need to rebuild
`pet_database.db` from the CSV seed data.

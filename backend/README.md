# PawTrack FastAPI Backend

This backend is the standardized FastAPI entry point for the existing PawTrack
database application. The API routes call the service layer in
`backend/app/services/pawtrack_service.py`, while prompt-to-SQL behavior lives
in `backend/app/services/llm_sql_assistant.py`.

Run it from the repository root:

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `PAWTRACK_RESET_DB=1` before startup if you need to rebuild
`pet_database.db` from the CSV seed data.

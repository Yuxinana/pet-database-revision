# Project Structure

The current migration keeps the original UI and behavior intact while placing
the runtime behind a clearer FastAPI + Vue project layout.

```text
pet-database_update/
├── backend/                  # FastAPI application wrapper
│   └── app/
│       ├── main.py           # App factory, middleware, router registration
│       ├── core/
│       │   ├── config.py     # Shared paths
│       │   ├── errors.py     # FastAPI exception handlers
│       │   └── legacy.py     # Compatibility layer over existing services
│       ├── routes/
│       │   ├── api.py        # /api routes used by the preserved UI
│       │   └── frontend.py   # Routes serving the preserved HTML UI
│       ├── db/
│       │   ├── schema/       # SQLite schema and indexes
│       │   ├── queries/      # Reviewed read-only SQL deliverables
│       │   └── data/         # CSV seed data used by database initialization
│       └── services/
│           ├── web_server_legacy.py  # Existing service logic, moved into backend
│           ├── query_registry.py
│           └── llm_sql_assistant.py  # Prompt-to-SQL and SQL safety checks
├── frontend/                 # Vue/Vite shell
│   ├── src/
│   │   ├── App.vue           # Full-page shell for the preserved UI
│   │   ├── main.js
│   │   └── styles.css
│   └── vite.config.js
├── docs/                     # Supporting report, SQL, and diagram docs
├── tests/                    # Regression tests
├── frontend/legacy/pawtrack_demo.html  # Preserved full UI, served by FastAPI
├── README.md
├── requirements.txt
└── package.json
```

## What Not To Delete Yet

- `frontend/legacy/pawtrack_demo.html`: this is still the complete production UI.
- `backend/app/services/web_server_legacy.py`: this still holds the existing
  database initialization, validation, and service behavior while it is split
  further.
- `backend/app/services/llm_sql_assistant.py`: this holds the prompt-to-SQL
  implementation and SQL safety checks.
- `pet_database.db`: generated runtime database; ignored by git, but useful for
  local startup.
- `frontend/node_modules/`: installed frontend dependencies; ignored by git.

## Generated Files That Can Be Deleted

These are ignored and safe to regenerate:

- `__pycache__/`
- `.pytest_cache/`
- `frontend/dist/`
- `frontend/node_modules/.vite/`

# Project Structure

The frontend is organized as a Vue/Vite application, while the FastAPI backend
exposes the JSON API used by the UI.

```text
pet-database_update/
├── backend/                  # FastAPI application wrapper
│   └── app/
│       ├── main.py           # App factory, middleware, router registration
│       ├── core/
│       │   ├── config.py     # Shared paths
│       │   ├── errors.py     # FastAPI exception handlers
│       │   └── service.py    # Service facade used by routes and startup
│       ├── routes/
│       │   ├── api.py        # /api routes used by the Vue frontend
│       │   └── frontend.py   # Root route serving the Vue entry point
│       ├── db/
│       │   ├── schema/       # SQLite schema and indexes
│       │   ├── queries/      # Reviewed read-only SQL deliverables
│       │   └── data/         # CSV seed data used by database initialization
│       └── services/
│           ├── pawtrack_service.py   # Database initialization and business workflows
│           ├── query_registry.py
│           └── llm_sql_assistant.py  # Prompt-to-SQL and SQL safety checks
├── frontend/                 # Vue/Vite application
│   ├── src/
│   │   ├── App.vue           # Vue entry component
│   │   ├── components/       # Sidebar, modals, and utility components
│   │   ├── pages/            # Page-level views
│   │   ├── services/         # API clients and external adapters
│   │   ├── config/           # App-wide constants
│   │   ├── utils/            # DOM and formatting helpers
│   │   ├── features/         # Domain feature modules and controllers
│   │   │   ├── analytics/    # Analytics table and chart rendering
│   │   │   ├── assistant/    # Prompt-to-SQL UI behavior
│   │   │   ├── crud/         # CRUD form configuration
│   │   │   ├── data/         # Frontend data loading service
│   │   │   ├── domain/       # Frontend business rules and guards
│   │   │   ├── errors/       # Fallback/error-state rendering
│   │   │   └── ui/           # Shared UI controllers
│   │   ├── lib/              # Application bootstrap and orchestration
│   │   ├── styles/           # Application styles
│   │   ├── main.js
│   ├── tests/              # Frontend unit tests
│   └── vite.config.js
├── backend/tests/           # Backend regression tests
├── docs/                     # Supporting report, SQL, and diagram docs
├── README.md
├── requirements.txt
└── package.json
```

## What Not To Delete Yet

- `backend/app/services/pawtrack_service.py`: this holds database
  initialization, validation, and service behavior.
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

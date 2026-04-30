# PawTrack Vue Frontend

This is the Vue 3 + Vite frontend for PawTrack. The source is split into a
standard frontend structure:

- `src/components/` contains reusable layout, modal, and utility components.
- `src/pages/` contains the page-level views.
- `src/services/` contains API clients and external service adapters.
- `src/config/` contains app-wide constants.
- `src/utils/` contains DOM and formatting helpers.
- `src/features/` contains domain-specific frontend modules and controllers.
- `src/styles/` contains the style entry point and scoped style partials.
- `src/lib/` contains the application bootstrap and orchestration layer.

Current feature modules:

- `features/analytics/` handles analytics tables and Chart.js rendering.
- `features/assistant/` handles prompt-to-SQL UI behavior.
- `features/crud/` owns CRUD form configuration.
- `features/data/` owns frontend data loading.
- `features/domain/` owns frontend business rules and guards.
- `features/errors/` owns fallback/error-state rendering.
- `features/ui/` owns shared UI controllers.

Run it from the repository root after installing Node.js:

```bash
cd frontend
npm install
npm run dev
```

Run frontend unit tests:

```bash
npm test
```

By default the Vue app calls the API through the Vite proxy at
`http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` if your API runs elsewhere.

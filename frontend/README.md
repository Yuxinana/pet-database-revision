# PawTrack Vue Frontend

This is the Vue 3 + Vite frontend shell for PawTrack. To preserve the existing
visual design and full feature set, it currently embeds the original
`frontend/legacy/pawtrack_demo.html` UI served by the FastAPI backend.

Run it from the repository root after installing Node.js:

```bash
cd frontend
npm install
npm run dev
```

By default the Vue shell loads the preserved UI from
`http://127.0.0.1:8000/pawtrack_demo.html`. Set `VITE_API_BASE_URL` if your API
runs elsewhere.

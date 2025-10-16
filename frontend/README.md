# Frontend Setup

The backend now exposes only JSON APIs. Serve the UI with the tooling of your choice and call the backend at `http://localhost:8000` (or the host/port where `server.py` runs).

## Development Flow

1. `cd frontend`
2. `npm install`
3. `npm run dev`

Point your dev server at the backend by proxying `/api/*` to `http://localhost:8000`.

## Production Flow

1. Build your frontend (`npm run build` or equivalent).
2. Drop the compiled assets under `frontend/static/` or deploy them separately.

The files in `frontend/static/` are a minimal scaffold that demonstrates:

- Logging in against `/api/auth/login`.
- Issuing a search via `/api/search/web`.
- Refreshing search status at `/api/search/status`.

Replace them once your real frontend is ready.

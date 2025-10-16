

## Backend Architecture

The repository is now split into two top-level domains:

- `backend/` contains the Flask application, domain services, and shared utilities.
  - `backend/app/` holds the application factory, dependency container, and route blueprints.
  - `backend/core/` contains foundational components such as the LLM client, conversation memory, and user management.
  - `backend/services/` groups feature modules (`search`, `rag`, `files`) behind cohesive service boundaries.
  - `backend/common/` exposes shared error types and helpers.
- `frontend/` contains static assets or the compiled SPA. Serve it with your preferred frontend tooling; the Python backend now exposes APIs only.

`server.py` remains at the repository root and simply boots the backend app via `backend.app.create_app`.

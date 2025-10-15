# Repository Guidelines

## Project Structure & Module Organization
- `server.py` orchestrates the Flask API and wires LLM, RAG, auth, and web search services.
- Core layers live in `core/` (LLM client, memory, user management) and feature modules in `src/` (RAG, ingestion, keyword extraction, Selenium search); REST blueprints are grouped in `api/`.
- Shared assets: `config/config.json` for toggles, `data/` for knowledge sources, `uploads/` for user files, `static/` for the client bundle, and `conversations/` for persisted chat logs.

## Build, Test, and Development Commands
- Create an isolated environment first: `python -m venv .venv && .\.venv\Scripts\activate`.
- Install packages with `pip install -r requirements.txt`; add tooling such as `pip install pytest black` when needed.
- Run the service locally via `python server.py` (UI at `http://localhost:5000`, diagnostics at `/health`).
- Smoke-test Bing search with `python test_search_order.py`; run `python -m pytest` once suites are collected under `tests/`.

## Coding Style & Naming Conventions
- Target Python 3.10+, keep 4-space indentation, module docstrings, and type hints on public entry points.
- Use `snake_case` for modules and config keys, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants, and expose new Flask routes through `create_*_endpoints` factories.
- Format code with `black --line-length 100` and `isort`; check in formatted files only.

## Testing Guidelines
- Prefer `pytest`; mirror the module tree under `tests/` and tag Selenium flows with `@pytest.mark.slow`.
- Fixture external services (LLM, Bing, SearXNG) and load override configs from `config/test/` to keep runs deterministic.
- Assert both success flags and payload shape (`result["result_count"]`, `result["success"]`) similar to `test_search_order.py`, and aim for ≥80 % coverage across `core/` and `src/`.

## Commit & Pull Request Guidelines
- Write imperative, scope-prefixed commits such as `search: fix selenium fallback`; keep subjects ≤72 characters and add brief bodies for behavior changes.
- Rebase before opening a PR, fill in summary, verification steps, linked issues, and include screenshots or logs for UI or search updates.
- Call out config or secret impacts (`config/config.json`, `auth/users.json`), request module owner review, and wait for lint/pytest CI to pass before merging.

## Security & Configuration Tips
- Keep secrets out of VCS (`.env.local`), load them via `os.getenv`, and rotate `auth/users.json` defaults whenever accounts are issued.
- Document temporary toggles (e.g., `ALLOW_INSECURE_SSL`, proxy overrides) in the PR and return them to hardened values after debugging.

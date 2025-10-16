

## Backend Architecture

The repository is now split into two top-level domains:

- `backend/` contains the Flask application, domain services, and shared utilities.
  - `backend/app/` holds the application factory, dependency container, and route blueprints.
  - `backend/core/` contains foundational components such as the LLM client, conversation memory, and user management.
  - `backend/services/` groups feature modules (`search`, `rag`, `files`) behind cohesive service boundaries.
  - `backend/common/` exposes shared error types and helpers.
- `frontend/` contains static assets or the compiled SPA. Serve it with your preferred frontend tooling; the Python backend now exposes APIs only.

`server.py` remains at the repository root and simply boots the backend app via `backend.app.create_app`.

### Web Search Provider (lite backend) fix

- Version: 2025-10-16
- Change: Switched `web_search.default_provider` from `selenium` to `duckduckgo` (HTML-only lite backend) in `backend/config/config.json` to avoid RuntimeError when Selenium is unavailable in headless/corporate environments.
- Impact: Web search now uses a CAPTCHA-free, lightweight HTML strategy by default via DuckDuckGo/requests/BeautifulSoup. SearXNG and Bing providers remain available if toggled.

Verification

1. Create venv and install deps:
   ```bash
   python -m venv .venv && .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Run server:
   ```bash
   python server.py
   ```
3. Test endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/search/web -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"query":"python tutorial","max_results":3}'
   ```
   - Expect: `{ "success": true, "result_count": >0, "provider": "duckduckgo" | "duckduckgo (cached)" }`.

Troubleshooting

- If results are empty, ensure internet access and retry; DuckDuckGo HTML is rate-limited occasionally.
- To re-enable Selenium UI automation, set `web_search.default_provider` back to `selenium` and ensure Chrome/Driver is installed; headless mode is configured under `web_search.selenium`.
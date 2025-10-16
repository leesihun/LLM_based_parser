

## Backend Architecture

The repository is now split into two top-level domains:

- `backend/` contains the Flask application, domain services, and shared utilities.
  - `backend/app/` holds the application factory, dependency container, and route blueprints.
  - `backend/core/` contains foundational components such as the LLM client, conversation memory, and user management.
  - `backend/services/` groups feature modules (`search`, `rag`, `files`) behind cohesive service boundaries.
  - `backend/common/` exposes shared error types and helpers.
- `frontend/` contains static assets or the compiled SPA. Serve it with your preferred frontend tooling; the Python backend now exposes APIs only.

`server.py` remains at the repository root and simply boots the backend app via `backend.app.create_app`.

### TypeScript-Only Web Search (Page Assist Original Code) 🚀

- **Version**: 2025-10-17 (v3.0.0 - TypeScript Native Only)
- **Change**: **REMOVED all Python web search implementations** - Now uses ONLY TypeScript (Page Assist original code)
  - ❌ **Deleted**: All Python provider files (`google.py`, `duckduckgo.py`, `bing.py`, `searxng.py`, etc.)
  - ❌ **Deleted**: Selenium-based search implementation (`selenium_search.py`)
  - ✅ **Using**: TypeScript bridge exclusively (`typescript_bridge.py` → `websearch_ts/search.js`)
  - ✅ **Source**: 100% Page Assist original JavaScript/TypeScript code
- **Impact**: Cleaner architecture, no Python HTML scraping, no Selenium dependencies. All search goes through Node.js with Page Assist's proven implementation.

**Available Providers (TypeScript Only):**
| Provider | Type | Requires API Key | Source |
|----------|------|------------------|--------|
| Google | HTML Scraping | No | Page Assist original |
| DuckDuckGo | HTML Scraping | No | Page Assist original |
| **Brave API** | **API** | **Yes** | Page Assist original |
| **Tavily API** | **API** | **Yes** | Page Assist original |
| **Exa API** | **API** | **Yes** | Page Assist original |

**Configuration:**
```json
{
  "web_search": {
    "enabled": true,
    "default_provider": "duckduckgo",  // or "google", "brave_api", "tavily_api", "exa_api"
    "google_domain": "google.com",
    "brave_api_key": "",  // Optional: Get from https://brave.com/search/api/
    "tavily_api_key": "",  // Optional: Get from https://tavily.com/
    "exa_api_key": ""  // Optional: Get from https://exa.ai/
  }
}
```

**Requirements:**
- ✅ **Node.js** (https://nodejs.org/) - Required for TypeScript search
- ✅ **npm packages** - Auto-installed on first run (`npm install` in `websearch_ts/`)
- ❌ **Selenium** - No longer needed (removed)
- ❌ **ChromeDriver** - No longer needed (removed)

**How It Works:**
1. Python API request → `SearchManager`
2. `SearchManager` → `TypeScriptSearchBridge`
3. `TypeScriptSearchBridge` → Execute `node websearch_ts/search.js <provider> <query>`
4. Node.js runs Page Assist original code
5. JSON results returned to Python
6. Results processed and cached

**Bug Fixes:**
- Fixed `AttributeError: 'WebSearchFeature' object has no attribute 'search_and_chat'`
  - Added `search_and_chat()` method that performs web search and generates LLM-powered responses
  - Method integrates with conversation memory and supports all new search providers
  - Properly handles search failures with graceful error messages

### Web Search Provider (lite backend) fix

- Version: 2025-10-16
- Change: Switched `web_search.default_provider` from `selenium` to `duckduckgo` (HTML-only lite backend) in `backend/config/config.json` to avoid RuntimeError when Selenium is unavailable in headless/corporate environments.
- Impact: Web search now uses a CAPTCHA-free, lightweight HTML strategy by default via DuckDuckGo/requests/BeautifulSoup. SearXNG and Bing providers remain available if toggled.

Verification

1. Create venv and install deps:
   ```bash
   python -m venv .venv && .\\.venv\\Scripts\\activate
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

### Single-provider mode (PageAssist-style)

- Version: 2025-10-16
- Change: Added `web_search.disable_fallbacks` (default `true` now in config) to prevent automatic provider fallbacks. The manager and feature honor this flag, so only the selected `default_provider` is used.
- Impact: Behavior matches a single-provider pipeline similar to PageAssist. To allow auto-fallbacks again, set `disable_fallbacks` to `false`.

Quick check
```bash
curl -X POST http://localhost:8000/api/search/web \
  -H "Content-Type: application/json" -H "Authorization: Bearer <token>" \
  -d '{"query":"site:python.org decorators","max_results":3}'
```
- Expect: `provider` equals the configured `default_provider` only; if blocked, response shows `success:false` without switching providers.

### Session History API Fix

- **Version**: 2025-10-16 (v1.2.2)
- **Change**: Fixed session history retrieval API that was not properly implemented.
  - Added missing `/api/conversations/<session_id>/history` endpoint with `include_system` query parameter support
  - Updated `/api/conversations/<session_id>` to return only conversation metadata (not full history)
  - Fixed response format inconsistencies between API documentation and actual implementation
- **Impact**: API clients can now properly retrieve session history using the documented endpoints. The separation between metadata and history endpoints provides better performance for listing conversations without loading full message history.

**Endpoints Updated:**
1. `GET /api/conversations/<session_id>` - Returns conversation metadata only
   - Response: `{"conversation": {id, user_id, created_at, last_activity, title, total_messages}}`
2. `GET /api/conversations/<session_id>/history` - Returns message history
   - Query param: `include_system` (default: false)
   - Response: `{"session_id": "...", "history": [...]}`
3. `DELETE /api/conversations/<session_id>` - Response format updated to `{"deleted": true/false}`

**Verification:**
```bash
# Get conversation metadata
curl -X GET "http://localhost:8000/api/conversations/<session_id>" \
  -H "Authorization: Bearer <token>"

# Get conversation history
curl -X GET "http://localhost:8000/api/conversations/<session_id>/history?include_system=true" \
  -H "Authorization: Bearer <token>"
```
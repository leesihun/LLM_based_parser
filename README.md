

## Backend Architecture

The repository is now split into two top-level domains:

- `backend/` contains the Flask application, domain services, and shared utilities.
  - `backend/app/` holds the application factory, dependency container, and route blueprints.
  - `backend/core/` contains foundational components such as the LLM client, conversation memory, and user management.
  - `backend/services/` groups feature modules (`search`, `rag`, `files`) behind cohesive service boundaries.
  - `backend/common/` exposes shared error types and helpers.
- `frontend/` contains static assets or the compiled SPA. Serve it with your preferred frontend tooling; the Python backend now exposes APIs only.

`server.py` remains at the repository root and simply boots the backend app via `backend.app.create_app`.

### Page Assist TypeScript Web Search Integration 🚀

- **Version**: 2025-10-16 (v2.1.0 - TypeScript Native)
- **Change**: Integrated Page Assist-inspired web search providers with API-based search engines
  - Added **Brave Search API** provider (`brave_api.py`) - requires API key
  - Added **Tavily Search API** provider (`tavily_api.py`) - includes AI-generated answers
  - Added **Exa Search API** provider (`exa_api.py`) - semantic search engine
  - Enhanced **Google Search** provider with pagination and deduplication (mirrors Page Assist algorithm)
  - Updated SearchManager with intelligent provider fallback system
  - Added API key configuration in `config.json`
- **Impact**: Web search now supports multiple premium search APIs alongside free providers. Users can choose between free HTML-based providers (Google, DuckDuckGo, Bing) and premium API providers (Brave, Tavily, Exa) for better quality and reliability.

**Available Providers:**
| Provider | Type | Requires API Key | Features |
|----------|------|------------------|----------|
| Google | HTML Scraping | No | Pagination, deduplication, region support |
| DuckDuckGo | HTML Scraping | No | CAPTCHA-free, lightweight |
| Bing | HTML/API | Optional | Fallback to web scraping |
| SearXNG | API | No | Self-hosted metasearch |
| **Brave API** | **API** | **Yes** | **Fast, reliable, structured results** |
| **Tavily API** | **API** | **Yes** | **AI-generated answers, research-focused** |
| **Exa API** | **API** | **Yes** | **Semantic search, AI-optimized** |

**Configuration:**
```json
{
  "web_search": {
    "default_provider": "google",  // or "brave_api", "tavily_api", "exa_api"
    "providers": {
      "google": { "enabled": true },
      "duckduckgo": { "enabled": true },
      "brave_api": { "enabled": false },
      "tavily_api": { "enabled": false },
      "exa_api": { "enabled": false }
    },
    "google_domain": "google.com",
    "brave_api_key": "YOUR_BRAVE_API_KEY",
    "tavily_api_key": "YOUR_TAVILY_API_KEY",
    "exa_api_key": "YOUR_EXA_API_KEY"
  }
}
```

**Get API Keys:**
- Brave API: https://brave.com/search/api/
- Tavily API: https://tavily.com/
- Exa API: https://exa.ai/

**TypeScript Bridge (New!):**
- ✅ **Page Assist 원본 코드를 TypeScript로 그대로 사용**
  - Python이 아닌 **Node.js로 실제 검색 실행** (`websearch_ts/search.js`)
  - Page Assist의 Google, DuckDuckGo, Brave API, Tavily API, Exa API 코드 100% 그대로
  - Python에서 subprocess로 Node.js 호출 (`typescript_bridge.py`)
  - JSON으로 결과 주고받기
  
**설정:**
```json
{
  "web_search": {
    "use_typescript_search": true,  // TypeScript 사용 (기본값)
    "default_provider": "duckduckgo"
  }
}
```

**요구사항:**
- Node.js 설치 필요 (https://nodejs.org/)
- 첫 실행 시 자동으로 `npm install` 실행

**작동 방식:**
1. Python API 호출 → SearchManager
2. SearchManager → TypeScriptSearchBridge
3. TypeScriptSearchBridge → `node search.js` 실행
4. Node.js가 Page Assist 원본 코드로 검색
5. JSON 결과 반환 → Python

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
# HE Team LLM Assistant

A comprehensive AI-powered assistant with multiple conversation modes, knowledge base integration, file processing, and intelligent web search capabilities.

## 📝 Recent Changes

### Version 1.3.0 (October 16, 2025) - Enhanced Web Search System
**Major Web Search Enhancements:**
- **Bing Search Provider**: Added full Bing search integration with API support and web scraping fallback
- **Advanced Result Filtering**: Implemented relevance scoring, duplicate detection, and content quality filtering
- **Search Result Caching**: Added Redis and in-memory caching with TTL support for faster repeated searches
- **Search Analytics**: Comprehensive metrics tracking including success rates, response times, and popular queries
- **Enhanced Configuration**: Expanded search settings with provider toggles, filtering options, and caching parameters

**Technical Improvements:**
- Modular search architecture with provider abstraction
- Advanced result ranking based on query relevance and content quality
- Intelligent cache management with automatic cleanup and size limits
- Detailed performance analytics with historical trends and error tracking
- Improved error handling with better fallback mechanisms

**New Configuration Options:**
```json
{
  "web_search": {
    "providers": {
      "bing": { "enabled": true },
      "duckduckgo": { "enabled": true },
      "searxng": { "enabled": false }
    },
    "result_filtering": {
      "enabled": true,
      "enable_duplicate_detection": true,
      "enable_relevance_scoring": true,
      "min_content_length": 100,
      "max_content_length": 5000
    },
    "cache": {
      "enabled": true,
      "enable_redis": false,
      "default_ttl": 3600,
      "max_cache_size": 1000
    },
    "analytics": {
      "enabled": true,
      "max_history_size": 1000,
      "retention_days": 7
    }
  }
}
```

### Version 1.2.3 (October 14, 2025)
Added: Proxy/SSL diagnostics and hardened HTML providers in `search_api_test.ipynb`
- New diagnostics cell prints proxy vars, tests connectivity, and shows cert store path.
- Unified network wrapper: supports HTTP(S) proxies, custom CA via `CA_BUNDLE_PATH`, retries, and optional insecure SSL (`ALLOW_INSECURE_SSL=1`).
- HTML providers (SearXNG, DuckDuckGo, Brave) now use the wrapper with endpoint rotation and SSL fallbacks.
- Added notebook docs for direct SearXNG URLs and examples.

### Version 1.2.2 (October 14, 2025)
Added: Self-contained search API test notebook
- New notebook: `search_api_test.ipynb`
- Tests multiple providers with one run: Bing API, SerpAPI (Bing), SearXNG, DuckDuckGo HTML, Brave HTML
- No repository code dependencies; installs required Python packages at runtime
- Outputs a summary table with latency, status, and sample results per provider
- Configure via env vars: `BING_API_KEY`, `SERPAPI_KEY`, `SEARXNG_BASE`

### Version 1.2.1 (October 14, 2025)
**Fixed: Selenium Double Search Issue & Config Cleanup**
- **Fixed duplicate search execution**: Frontend was making 2 API calls for web search
  - `/api/chat/web-search` (for LLM response) + `/api/search/web` (for UI display)
  - Now includes search results in chat response, eliminating duplicate call
- Disabled `query_expansion` in web search configuration to prevent multiple query variations
- Previously, keyword extraction was generating up to 3 optimized queries, causing Selenium to search multiple times
- Now limited to single optimized query per search request
- Configuration: `config/config.json` → `web_search.keyword_extraction.query_expansion: false`
- **Cleanup**: Removed unused `config/search_config.json` file to avoid confusion
- Disabled debug Chrome mode (now uses regular Chrome with anti-detection)
- **Documentation**: Completely rewrote API documentation
  - Comprehensive endpoint documentation in `API_documentation.md`
  - Added code examples (JavaScript, Python, cURL)
  - Documented recent API changes
  - Added model configuration endpoints
  - Included error handling guide
- **Impact**: Web search now performs only ONCE (was searching 2-3 times before)
  - 2-3x faster search performance
  - Reduced browser overhead and resource usage
  - No duplicate keyword extraction
- **Important**: Restart the server and refresh browser for changes to take effect

## ✨ Key Features

### 🔐 Authentication & Security
- **Multi-user authentication** with role-based access control
- **Session management** with secure token-based authentication  
- **Per-user data isolation** - each user has private conversations
- **Admin panel** for user management and system administration

### 🤖 AI Capabilities
- **Multiple chat modes**: Normal chat, RAG-enhanced, document analysis, file processing
- **Knowledge base integration** using ChromaDB for semantic search
- **Intelligent web search** with keyword extraction and result optimization
- **File upload and analysis** for document processing
- **Configurable system prompts** for different conversation contexts

### 🌐 Web Search Intelligence
- **Selenium-based web search** for reliable results
- **Advanced keyword extraction** using multiple methods (TF-IDF, rule-based, LLM-assisted)
- **Search adequacy validation** - prevents search when keywords are too generic
- **Query optimization** for better search results
- **Performance metrics** tracking for search operations

### 🏗️ Architecture
- **Modular API design** with clean separation of concerns
- **RESTful endpoints** for all functionality
- **Modern web interface** with responsive design
- **Local Ollama integration** for offline LLM capabilities
- **Configurable and extensible** system architecture

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- At least one Ollama model pulled (e.g., `ollama pull llama3.2`)
- Chrome or Chromium browser (for web search functionality)

### Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd LLM_based_parser
   pip install -r requirements.txt
   ```

2. **Initialize the system**
   ```bash
   python setup_system.py  # Sets up RAG system and processes Excel data
   ```

3. **Start the server**
   ```bash
   python server.py  # or python server_new.py for the refactored version
   ```

4. **Access the interface**
   - **Local**: `http://localhost:8000/login.html`
   - **Network**: `http://YOUR_IP:8000/login.html`
   - **Default login**: `admin` / `admin123` ⚠️ *Change immediately*

5. **Choose your chat mode**
   - **Normal Chat**: Standard AI conversation
   - **RAG Mode**: Knowledge base enhanced responses
   - **Web Search**: Live internet search integration
   - **File Analysis**: Upload and analyze documents

## ⚙️ Configuration

The system uses `config/config.json` for all settings:

```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "model": "llama3.2",
    "timeout": 30000,
    "num_ctx": 8192,
    "temperature": 0.7
  },
  "server": {
    "port": 8000,
    "host": "0.0.0.0"
  },
  "web_search": {
    "enabled": true,
    "use_keyword_extraction": true,
    "max_results": 5,
    "timeout": 10
  },
  "system_prompt": {
    "enabled": true,
    "universal": "Base instructions for all modes",
    "default": "Normal chat instructions",
    "rag_mode": "Knowledge base search instructions",
    "search_mode": "Web search instructions"
  }
}
```

## 🏗️ System Architecture

### Core Components
- **`core/`** - Core system functionality
  - `llm_client.py` - Ollama integration and LLM communication
  - `conversation_memory.py` - Session and conversation management
  - `user_management.py` - Authentication and user management

- **`src/`** - Feature modules
  - `rag_system.py` - ChromaDB integration and semantic search
  - `web_search_feature.py` - Intelligent web search with Selenium
  - `keyword_extractor.py` - Advanced keyword extraction
  - `file_handler.py` - File upload and processing
  - `excel_to_md_converter.py` - Data processing utilities

- **`api/`** - RESTful API modules
  - `auth.py` - Authentication endpoints
  - `chat.py` - Chat and conversation endpoints
  - `search.py` - Web search functionality
  - `system.py` - System management and health

- **`static/`** - Web interface
  - `index.html` - Main chat interface
  - `login.html` - Authentication page

## 🔌 API Reference

For complete, detailed API documentation see **[API_documentation.md](API_documentation.md)**

### Quick Reference

**Authentication**
```
POST   /api/auth/login                    # User authentication
POST   /api/auth/logout                   # Session termination
GET    /api/auth/me                       # Current user info
POST   /api/auth/change-password          # Password management
```

**Chat Modes** (all support conversation resumption via `session_id`)
```
POST   /api/chat                          # Normal conversation
POST   /api/chat/rag                      # Knowledge base enhanced
POST   /api/chat/web-search               # Web search integrated (includes search_results)
```

**Conversation Management**
```
GET    /api/conversations                 # List user sessions
POST   /api/conversations                 # Create new session
GET    /api/conversations/<id>            # Get conversation details
GET    /api/conversations/<id>/history    # Get message history
DELETE /api/conversations/<id>            # Delete conversation
POST   /api/conversations/clear           # Delete all conversations
GET    /api/conversations/stats           # Get statistics
```

**Web Search**
```
POST   /api/search/web                    # Direct web search
POST   /api/search/extract-keywords       # Keyword extraction
GET    /api/search/status                 # Search capabilities
POST   /api/search/keyword-extraction/enable
POST   /api/search/keyword-extraction/disable
```

**Model Configuration**
```
GET    /api/models/available              # List Ollama models
GET    /api/models/current                # Current configuration
POST   /api/models/configure              # Update parameters
POST   /api/models/test                   # Test model
GET    /api/models/presets                # Get presets
POST   /api/models/preset/<name>          # Apply preset
```

**System Management**
```
GET    /health                            # System health check (no auth)
GET    /api/models                        # Available LLM models
GET    /api/config                        # System configuration
POST   /api/config                        # Update config (runtime)
GET    /api/rag/stats                     # RAG system statistics
```

**Administration** (admin role required)
```
GET    /api/admin/users                   # List all users
POST   /api/admin/users                   # Create user
POST   /api/admin/users/<user>/reset-password
GET    /api/admin/sessions                # Active sessions
GET    /api/admin/stats                   # System statistics
```

**📖 See [API_documentation.md](API_documentation.md) for**:
- Complete endpoint documentation
- Request/response examples
- Error handling
- Code examples (JavaScript, Python, cURL)
- Authentication flow
- Conversation resumption examples

## 💡 Usage Examples

### Company Proxy Setup (Notebook)
- Set these before launching Jupyter:
  - `HTTP_PROXY` / `HTTPS_PROXY` or `PROXY_URL`
  - Optional `CA_BUNDLE_PATH` to your corporate PEM bundle
  - Optional `ALLOW_INSECURE_SSL=1` (dev/lab only)
  - Optional `REQUEST_RETRIES=3`, `REQUEST_BACKOFF=1.0`
- The notebook’s diagnostics cell will verify connectivity and SSL.

### SearXNG Quick Test (Browser)
- Home: `https://search.bus-hit.me/`
- JSON: `https://search.bus-hit.me/search?q=python&format=json`
- HTML: `https://search.bus-hit.me/search?q=python`

### Search API Test Notebook
- Open `search_api_test.ipynb` in Jupyter/VS Code and run all cells top-to-bottom.
- Optional environment variables:
  - `BING_API_KEY` for Bing Web Search API
  - `SERPAPI_KEY` for SerpAPI (engine=bing)
  - `SEARXNG_BASE` (default: `https://search.bus-hit.me`)
- The notebook prints a results summary table and sample hits per provider.

### Web Interface Usage

1. **Normal Chat**
   ```
   User: "Explain quantum computing"
   AI: [Provides detailed explanation]
   ```

2. **RAG Mode** (Knowledge base enhanced)
   ```
   User: "What does our company policy say about remote work?"
   AI: [Searches knowledge base and provides policy details]
   ```

3. **Web Search Mode**
   ```
   User: "Latest developments in AI 2024"
   AI: [Searches web, extracts relevant info, provides current insights]
   ```

4. **File Analysis**
   ```
   Upload document → AI analyzes content → Ask questions about the file
   ```

### API Integration

```python
import requests

# Authentication
auth = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin', 'password': 'admin123'
})
headers = {'Authorization': f"Bearer {auth.json()['session_token']}"}

# Normal chat
chat = requests.post('http://localhost:8000/api/chat', 
    headers=headers, json={'message': 'Hello!'})

# RAG-enhanced chat
rag_chat = requests.post('http://localhost:8000/api/chat/rag',
    headers=headers, json={'message': 'Search our knowledge base'})

# Web search chat
web_chat = requests.post('http://localhost:8000/api/chat/web-search',
    headers=headers, json={'message': 'Current weather in Tokyo'})

# Direct web search (returns raw results)
search = requests.post('http://localhost:8000/api/search/web',
    headers=headers, json={'query': 'latest AI news', 'max_results': 3})
```

### Keyword Extraction Testing

```python
# Test keyword extraction adequacy
keywords = requests.post('http://localhost:8000/api/search/extract-keywords',
    headers=headers, json={'text': 'I need help with machine learning algorithms'})

print(keywords.json())
# Output: {
#   'keywords': ['machine learning', 'algorithms'],
#   'adequate_keywords': True,
#   'queries': ['machine learning algorithms'],
#   'method': 'tfidf_enhanced'
# }
```

## 👥 User Management

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123` ⚠️ *Change immediately*
- **Role**: Administrator

### User Administration

**Via Web Interface:**
1. Login as admin
2. Access admin panel from the interface
3. Create/modify/delete users
4. Reset passwords as needed

**Via API:**
```python
# Create new user
requests.post('/api/admin/users', headers=admin_headers, json={
    'username': 'newuser',
    'password': 'securepass123',
    'email': 'user@company.com',
    'role': 'user'
})

# Reset password
requests.post('/api/admin/users/newuser/reset-password',
    headers=admin_headers, json={'new_password': 'newpass123'})
```

### Data Storage
```
auth/
├── users.json           # User accounts and credentials
└── user_sessions.json   # Active session tokens

conversations/
└── <user-id>/           # Per-user conversation history
    ├── session-1.json
    └── session-2.json

data/
├── chroma_db/           # RAG system vector database
├── combined_data.md     # Processed knowledge base
└── *.xlsx               # Source Excel files
```

## 📁 File Structure

```
LLM_based_parser/
├── README.md                 # This file
├── CLAUDE.md                # Development guide
├── requirements.txt         # Python dependencies
├── server.py               # Main server (legacy)
├── server_new.py           # Refactored server
├── setup_system.py         # System initialization
│
├── config/
│   └── config.json         # System configuration (includes web search settings)
│
├── core/                   # Core system modules
│   ├── llm_client.py
│   ├── conversation_memory.py
│   └── user_management.py
│
├── src/                    # Feature modules
│   ├── rag_system.py
│   ├── web_search_feature.py
│   ├── keyword_extractor.py
│   ├── file_handler.py
│   └── excel_to_md_converter.py
│
├── api/                    # RESTful API modules
│   ├── auth.py
│   ├── chat.py
│   ├── search.py
│   └── system.py
│
├── static/                 # Web interface
│   ├── index.html
│   └── login.html
│
├── data/                   # Data files
│   ├── chroma_db/         # RAG database
│   ├── combined_data.md   # Knowledge base
│   └── *.xlsx             # Source files
│
├── uploads/               # User uploads
├── auth/                  # Authentication data
└── conversations/         # Chat history
```

## 🔍 Enhanced Web Search Features

### Advanced Search Architecture
The system now features a comprehensive, modular web search architecture with multiple enhancements:

#### 🔧 Multiple Search Providers
- **Bing Search**: Full API integration with web scraping fallback
- **DuckDuckGo**: HTML scraping with API fallback support
- **SearXNG**: Meta-search engine integration (when available)
- **Brave Search**: Alternative search engine option
- **Automatic Fallback**: Seamless provider switching on failures

#### 🎯 Intelligent Result Processing
1. **Advanced Result Filtering**:
   - Relevance scoring based on query matching
   - Duplicate content detection and removal
   - Spam and low-quality content filtering
   - Domain-based filtering (allow/block lists)

2. **Content Quality Assessment**:
   - Minimum/maximum content length validation
   - Title quality checks
   - URL validity verification
   - Content relevance scoring

#### ⚡ Performance Optimizations
- **Smart Caching System**:
  - In-memory caching with Redis backend support
  - Configurable TTL (Time To Live) for cache entries
  - Automatic cache cleanup and size management
  - Cache hit/miss tracking and analytics

- **Search Analytics**:
  - Comprehensive performance metrics tracking
  - Success rate monitoring by provider
  - Response time analysis and trends
  - Popular query identification
  - Error pattern detection and reporting

#### 🧠 Enhanced Keyword Intelligence
1. **Multiple extraction methods**: TF-IDF, rule-based patterns, LLM-assisted
2. **Adequacy validation**: Prevents search with generic or insufficient keywords
3. **Technical term recognition**: Identifies domain-specific terminology
4. **Query optimization**: Generates optimized search queries from extracted keywords

### Search Process Flow
```
User Query → Keyword Extraction → Adequacy Check → Provider Selection →
Cache Check → Web Search → Result Filtering → Content Enrichment →
Cache Storage → Analytics Recording → Response
```

### Configuration Options
All web search settings are in `config/config.json` under the `web_search` section:

```json
{
  "web_search": {
    "enabled": true,
    "default_provider": "duckduckgo",
    "use_keyword_extraction": true,
    "max_results": 5,
    "timeout": 100,
    "providers": {
      "bing": { "enabled": true },
      "duckduckgo": { "enabled": true },
      "searxng": { "enabled": false }
    },
    "result_filtering": {
      "enabled": true,
      "enable_duplicate_detection": true,
      "enable_relevance_scoring": true,
      "min_content_length": 100,
      "max_content_length": 5000
    },
    "cache": {
      "enabled": true,
      "enable_redis": false,
      "default_ttl": 3600,
      "max_cache_size": 1000
    },
    "analytics": {
      "enabled": true,
      "max_history_size": 1000,
      "retention_days": 7
    },
    "keyword_extraction": {
      "enabled": true,
      "use_llm": true,
      "query_expansion": false,
      "max_keywords": 4
    }
  }
}
```

### Analytics and Monitoring
The system provides comprehensive analytics through:
- **Performance Reports**: Success rates, response times, cache hit rates
- **Provider Statistics**: Individual provider performance metrics
- **Query Trends**: Most frequently searched terms
- **Error Analysis**: Common failure patterns and troubleshooting data
- **Historical Data**: Trends over time with configurable retention

## 📊 Performance Metrics

The system tracks comprehensive performance metrics:

- **Response Time**: Total time from request to response
- **Processing Time**: LLM processing duration
- **Tokens per Second**: LLM generation speed
- **Search Processing Time**: Web search duration (when applicable)
- **Keyword Extraction**: Method used and adequacy status

These metrics are returned in API responses and displayed in the web interface.

## 🛠️ Development

### Adding New Features
1. Create feature module in `src/`
2. Add API endpoints in `api/`
3. Update web interface in `static/`
4. Configure settings in `config/`
5. Test thoroughly with different scenarios

### Testing Web Search
```bash
# Test search adequacy
python -c "
from src.keyword_extractor import KeywordExtractor
extractor = KeywordExtractor()
result = extractor.extract_keywords('help me please')
print('Adequate:', result.get('adequate_keywords', False))
"

# Test direct search
python -c "
from src.web_search_feature import WebSearchFeature
search = WebSearchFeature({}, None)
results = search.search_web('machine learning algorithms 2024', 3)
print('Success:', results['success'])
"
```

### Custom Models
- Install any Ollama-compatible model: `ollama pull model-name`
- Update `config/config.json` with the model name
- Restart the server to apply changes

## 🔒 Security Features

- **Token-based authentication** with session management
- **Password hashing** using secure algorithms
- **Role-based access control** (admin vs user permissions)
- **Data isolation** - users can only access their own data
- **Input validation** on all API endpoints
- **Secure session handling** with automatic expiration

### Security Best Practices
1. Change default admin password immediately
2. Use strong passwords for all accounts
3. Configure firewall for network access
4. Use HTTPS in production environments
5. Regularly update dependencies
6. Monitor logs for suspicious activity

## 🐛 Troubleshooting

### Common Issues

**Web Search Not Working**
- Check if Chrome/Chromium is installed
- Verify internet connectivity
- Test keyword extraction adequacy
- Check search configuration in `config/config.json` → `web_search` section
- Restart server after any config changes

**Ollama Connection Errors**
- Ensure Ollama is running: `ollama serve`
- Check Ollama URL in config
- Verify model is available: `ollama list`

**Authentication Issues**
- Check default credentials: admin/admin123
- Verify `auth/users.json` exists
- Clear browser cache and cookies
- Ensure JavaScript is enabled

**RAG System Issues**
- Check if `data/combined_data.md` exists
- Verify ChromaDB installation
- Run `python setup_system.py` to reinitialize

### Logs and Debugging
- Server logs: `server.log`
- Check browser console for frontend errors
- Use `/health` endpoint to check system status
- Monitor API responses for error details

## 📄 License

MIT License - Feel free to use and modify as needed.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request with detailed description

## 📞 Support

For issues and questions:
- Check troubleshooting section first
- Review system logs for error details
- Open GitHub issue with reproduction steps
- Include system configuration and environment details
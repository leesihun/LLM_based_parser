# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Setup & Commands

### Development Commands
```bash
# Start the main server
python server.py

# Run system initialization (processes Excel data, sets up RAG)
python setup_system.py

# Install dependencies
pip install -r requirements.txt

# Test individual components
python -c "from backend.services.search.keyword_extractor import KeywordExtractor; print('Keyword extraction OK')"
python -c "from backend.services.rag.rag_system import RAGSystem; print('RAG system OK')"
python -c "from backend.services.search.selenium_search import SeleniumSearcher; print('Web search OK')"
```

### Key Configuration Files
- `config/config.json` - Main system configuration (Ollama, web search, RAG settings)
- `config/search_config.json` - Web search specific settings
- `auth/users.json` - User accounts and authentication data

## Architecture Overview

This is a multi-modal AI assistant system built on Flask with the following key components:

### Core Architecture Pattern
The system follows a modular API-first architecture:
- **`core/`** - Core system services (LLM client, auth, memory)
- **`src/`** - Feature modules (RAG, search, file handling)  
- **`api/`** - REST endpoint definitions
- **`static/`** - Web interface files

### Key Integration Points

**LLM Integration (`core/llm_client.py`)**
- Uses Ollama for local LLM execution
- Configurable models (default: gemma3:12b)
- Handles both streaming and non-streaming responses
- System prompt hierarchy (universal ??mode-specific ??contextual)

**RAG System (`src/rag_system.py`)**
- ChromaDB vector storage with Ollama embeddings (nomic-embed-text)
- Semantic chunking strategy with 1000 token chunks, 200 token overlap
- Configurable similarity threshold (0.8 default)
- Parallel processing and caching enabled

**Web Search (`src/web_search_feature.py`)**
- Selenium-based search with Chrome WebDriver
- Advanced keyword extraction using TF-IDF + LLM assistance
- Search adequacy validation (prevents poor searches)

**Authentication (`core/user_management.py`)**
- Session-based authentication with Bearer tokens
- Role-based access (admin/user)
- Per-user data isolation
- Default credentials: admin/admin123

### API Architecture Pattern

All API modules follow this pattern:
```python
def create_*_endpoints(app, dependencies):
    """Create endpoints with dependency injection"""
    
    @app.route('/api/endpoint', methods=['POST'])
    @require_auth  # Authentication decorator
    def endpoint_handler():
        # Validate input
        # Process request
        # Return JSON response
```

Main API modules:
- `api/auth.py` - Authentication endpoints
- `api/chat.py` - Chat conversation endpoints
- `api/search.py` - Web search functionality
- `api/system.py` - System health and configuration

## Key Development Patterns

### Adding New Features

1. **Create feature module** in `src/` following this pattern:
   ```python
   class FeatureName:
       def __init__(self, config, llm_client=None):
           self.config = config
           self.llm_client = llm_client
   ```

2. **Add API endpoints** in `api/` using the endpoint factory pattern:
   ```python
   def create_feature_endpoints(app, feature_instance):
       @app.route('/api/feature/action', methods=['POST'])
       @require_auth
       def feature_action():
           return jsonify(result), 200
   ```

3. **Register endpoints** in `server.py`:
   ```python
   from api.feature import create_feature_endpoints
   create_feature_endpoints(app, feature_instance)
   ```

### Configuration Management

The system uses a hierarchical JSON configuration:
```json
{
  "ollama": { /* LLM settings */ },
  "web_search": { /* Search configuration */ },
  "rag": { /* RAG system settings */ },
  "system_prompt": { /* Mode-specific prompts */ }
}
```

Configuration is loaded once at startup but can be updated at runtime via `/api/config` (admin only).

### System Prompts Architecture

The system uses layered prompts:
- **Universal**: Applied to all conversations
- **Mode-specific**: Additional context for search/RAG/file modes
- **Dynamic context**: RAG results or search results injected as context

Example prompt construction:
```python
# Universal prompt from config
universal_prompt = config['system_prompt']['universal']

# Mode-specific addition
mode_prompt = config['system_prompt']['rag_mode']  

# Dynamic context injection
context = f"Context: {rag_results}\n\nUser: {user_message}"
```

### Error Handling Pattern

All components follow this error handling pattern:
```python
try:
    result = perform_operation()
    return {"success": True, "data": result}
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    return {"success": False, "error": str(e)}
```

### Data Storage Patterns

- **User data**: `conversations/<user_id>/session-*.json`
- **Authentication**: `auth/users.json`, `auth/user_sessions.json`
- **Knowledge base**: `data/chroma_db/` (ChromaDB), `data/combined_data.md` (source)
- **Uploads**: `uploads/` (temporary file storage)

## Testing & Debugging

### Component Testing
```bash
# Test web search capabilities
python -c "
from backend.services.search.web_search_feature import WebSearchFeature
searcher = WebSearchFeature({}, None)
caps = searcher.get_search_capabilities()
print('Search available:', caps.get('selenium_available'))
"

# Test RAG system
python -c "
from backend.services.rag.rag_system import RAGSystem
rag = RAGSystem('config/config.json')
stats = rag.get_stats()
print('Documents:', stats.get('document_count'))
"

# Test keyword extraction adequacy
python -c "
from backend.services.search.keyword_extractor import KeywordExtractor
extractor = KeywordExtractor({}, None)
result = extractor.extract_keywords('machine learning algorithms')
print('Adequate keywords:', result.get('adequate_keywords'))
"
```

### API Health Checks
```bash
# System health
curl http://localhost:8000/health

# Authentication test
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Debug Logging
The system logs to console and `server.log`. Key debug points:
- LLM communication errors in `core/llm_client.py`
- Search adequacy validation in `src/keyword_extractor.py`
- Authentication failures in `api/auth.py`
- RAG embedding issues in `src/rag_system.py`

## Important Implementation Details

### Web Search Adequacy System
The keyword extraction system prevents poor searches by validating:
- Minimum 2 keywords required
- Keywords must be sufficiently technical/specific
- Generic words ("help", "please") are filtered out
- Total keyword character length threshold

### ChromaDB Integration Specifics
- Uses Ollama embeddings (nomic-embed-text:latest) 
- Persists to `./data/chroma_db`
- Semantic chunking with configurable overlap
- Batch processing for performance
- Collection name: "documents"

### Session Management
- Bearer token authentication
- 24-hour session expiration
- Session cleanup runs automatically
- Tokens stored in `auth/user_sessions.json`

### System Initialization
The `setup_system.py` script:
1. Processes Excel files (`data/?�드긍정.xlsx`, `data/?�드부??xlsx`)
2. Converts to markdown (`data/combined_data.md`)
3. Initializes ChromaDB with embeddings
4. Sets up the RAG system for first use

## Dependencies & Requirements

### Core Dependencies
- **Flask 2.3.3** - Web framework and API server
- **ChromaDB 0.4.15** - Vector database for RAG
- **Selenium 4.15.2** - Web automation for search
- **Pandas 2.0.3** - Excel data processing

### External Requirements
- **Ollama** running locally (default: localhost:11434)
- **Chrome/Chromium** browser for web search
- **Models**: Main LLM (gemma3:12b) + embedding model (nomic-embed-text)

### Port Usage
- **8000** - Main Flask server (configurable in config.json)
- **11434** - Ollama API server (standard Ollama port)

This system is designed for local deployment with the HE team and provides a comprehensive AI assistant with knowledge base integration, web search, and multi-user support.

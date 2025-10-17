# HE Team LLM Assistant

A multi-modal AI assistant system built with Flask, featuring RAG (Retrieval Augmented Generation), web search capabilities, and comprehensive file handling.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)

## Overview

The HE Team LLM Assistant is a comprehensive AI-powered assistant system designed to provide intelligent responses using multiple data sources:

- **Local LLM Integration** via Ollama
- **RAG System** with ChromaDB for knowledge base queries
- **Web Search** with intelligent keyword extraction
- **File Analysis** supporting multiple formats
- **Multi-user Support** with role-based access control
- **Session Management** with conversation history

## Features

### Core Capabilities

- **Chat Interface**: Natural language conversation with context retention
- **Knowledge Base Search**: Semantic search through embedded documents using ChromaDB
- **Web Search Integration**: Real-time web search with multiple providers (DuckDuckGo, Bing, Brave)
- **File Processing**: Upload and analyze documents (PDF, DOCX, XLSX, TXT, code files)
- **User Management**: Admin panel for user creation and management
- **Multi-Session Support**: Maintain multiple concurrent conversations

### Technical Features

- **Streaming Responses**: Real-time LLM output streaming
- **Advanced Keyword Extraction**: LLM-assisted keyword extraction for better search results
- **Result Filtering**: Relevance scoring, duplicate detection, domain filtering
- **Caching System**: Configurable caching for search results and embeddings
- **Analytics**: Search analytics and usage tracking
- **TypeScript Bridge**: Integration with TypeScript-based web search module

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
├─────────────────────────────────────────────────────────┤
│  Routes: Auth, Chat, Search, RAG, Files, Admin, System  │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼─────┐      ┌──────────┐
│  Core  │      │ Services │      │ External │
└───┬────┘      └────┬─────┘      └────┬─────┘
    │                │                  │
┌───▼──────────┐ ┌──▼──────────┐   ┌──▼──────┐
│ LLM Client   │ │ RAG System  │   │ Ollama  │
│ User Mgmt    │ │ Web Search  │   │ ChromaDB│
│ Memory       │ │ File Handler│   │ Selenium│
└──────────────┘ └─────────────┘   └─────────┘
```

### Key Technologies

- **Backend**: Python 3.8+, Flask 2.3.3
- **LLM**: Ollama (default: gemma3:12b)
- **Vector DB**: ChromaDB 0.4.15 with Ollama embeddings (nomic-embed-text)
- **Web Automation**: Selenium 4.15.2
- **Frontend**: HTML/CSS/JavaScript (served statically)
- **Data Processing**: Pandas 2.0.3 for Excel files

## Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Ollama** running locally (download from [ollama.ai](https://ollama.ai))
3. **Chrome/Chromium** browser (for web search)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd LLM_based_parser
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Pull required Ollama models:
```bash
ollama pull gemma3:12b
ollama pull nomic-embed-text
```

4. Initialize the system (process Excel data and set up RAG):
```bash
python setup_system.py
```

5. Start the server:
```bash
python server.py
```

The application will be available at:
- Local: http://localhost:8000
- Network: http://<your-ip>:8000

### Default Credentials

- **Admin**: username: `admin`, password: `admin123`
- **Guest**: username: `guest`, password: `guest_test1`

## Configuration

The system uses a single configuration file: `config.json` at the root directory.

### Key Configuration Sections

#### Server Settings
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

#### Ollama Configuration
```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "model": "gemma3:12b",
    "temperature": 0.7,
    "num_ctx": 8192
  }
}
```

#### RAG System
```json
{
  "rag": {
    "embedding": {
      "provider": "ollama",
      "model": "nomic-embed-text:latest"
    },
    "chunking": {
      "strategy": "semantic",
      "chunk_size": 1000,
      "overlap": 200
    },
    "search": {
      "similarity_threshold": 0.8
    }
  }
}
```

#### Web Search
```json
{
  "web_search": {
    "enabled": true,
    "default_provider": "duckduckgo",
    "use_keyword_extraction": true,
    "max_results": 5
  }
}
```

See the full configuration file for all available options.

## Project Structure

```
LLM_based_parser/
├── config.json                 # Main configuration file
├── server.py                   # Application entry point
├── setup_system.py            # System initialization script
├── requirements.txt           # Python dependencies
│
├── backend/
│   ├── app/
│   │   ├── __init__.py       # Flask app factory
│   │   ├── container.py      # Dependency injection
│   │   ├── errors.py         # Error handlers
│   │   └── routes/           # API route blueprints
│   │       ├── auth.py       # Authentication endpoints
│   │       ├── chat.py       # Chat/conversation endpoints
│   │       ├── search.py     # Web search endpoints
│   │       ├── rag.py        # RAG system endpoints
│   │       ├── files.py      # File management endpoints
│   │       ├── admin.py      # Admin/user management
│   │       ├── system.py     # System health/info
│   │       └── model_config.py # Model configuration
│   │
│   ├── core/
│   │   ├── llm_client.py     # Ollama LLM client
│   │   ├── user_management.py # User authentication
│   │   └── conversation_memory.py # Session management
│   │
│   ├── services/
│   │   ├── rag/
│   │   │   └── rag_system.py # ChromaDB RAG implementation
│   │   ├── search/
│   │   │   ├── web_search_feature.py # Web search orchestration
│   │   │   ├── keyword_extractor.py  # Keyword extraction
│   │   │   ├── result_filter.py      # Result filtering
│   │   │   └── typescript_bridge.py  # TS integration
│   │   └── files/
│   │       └── file_handler.py # File processing
│   │
│   └── config/
│       ├── users.json        # User data (passwords, roles)
│       └── user_sessions.json # Active sessions
│
├── frontend/
│   └── static/              # HTML/CSS/JS frontend files
│
├── data/
│   ├── combined_data.md     # Knowledge base markdown
│   └── chroma_db/          # ChromaDB persistence
│
├── conversations/           # User conversation history
├── uploads/                # User uploaded files
└── websearch_ts/           # TypeScript web search module
```

## Development

### Running in Development Mode

```bash
# Start the server with auto-reload
python server.py
```

### Adding New Features

The system follows a modular blueprint pattern:

1. **Create a new service** in `backend/services/`
2. **Register in container** at `backend/app/container.py`
3. **Create route blueprint** in `backend/app/routes/`
4. **Register blueprint** in `backend/app/routes/__init__.py`

### Testing Individual Components

```bash
# Test LLM connection
python -c "from backend.core.llm_client import LLMClient; client = LLMClient('config.json'); print(client.chat_completion([{'role': 'user', 'content': 'Hello'}]))"

# Test RAG system
python -c "from backend.services.rag.rag_system import RAGSystem; rag = RAGSystem('config.json'); print(rag.get_stats())"

# Test web search
python -c "from backend.services.search.web_search_feature import WebSearchFeature; ws = WebSearchFeature({}, None); print(ws.get_search_capabilities())"
```

### Component Testing Commands

```bash
# Keyword extraction
python -c "from backend.services.search.keyword_extractor import KeywordExtractor; ke = KeywordExtractor({}, None); print(ke.extract_keywords('machine learning algorithms'))"

# Health check
curl http://localhost:8000/health

# Authentication test
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

### Quick API Overview

- **Authentication**: `/api/auth/login`, `/api/auth/logout`
- **Chat**: `/api/chat/messages` - Send messages with optional RAG
- **Search**: `/api/search/web` - Perform web searches
- **RAG**: `/api/rag/search` - Query knowledge base
- **Files**: `/api/files/upload`, `/api/files/<id>/read`
- **Admin**: `/api/admin/users` - User management (admin only)
- **System**: `/health`, `/api/system/info`

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest backend/tests/test_app.py

# Run with coverage
pytest --cov=backend
```

### Manual Testing

Use the included frontend interface or tools like Postman/curl to test API endpoints.

## Deployment

### Production Considerations

1. **Change the secret key** in `config.json`
2. **Use environment variables** for sensitive configuration
3. **Set up HTTPS** with reverse proxy (nginx/Apache)
4. **Configure firewall** rules for ports 8000 and 11434
5. **Use production WSGI server** (gunicorn/uwsgi)

### Production Server Setup

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 server:app
```

### Docker Deployment (Future)

Docker support is planned for future releases.

## System Requirements

### Minimum Requirements
- CPU: 4 cores
- RAM: 8GB (16GB recommended)
- Storage: 10GB free space
- OS: Windows 10+, Linux, macOS

### Network Requirements
- Port 8000: Web server
- Port 11434: Ollama API
- Internet connection for web search features

## Troubleshooting

### Common Issues

**Ollama Connection Failed**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama service
ollama serve
```

**ChromaDB Errors**
```bash
# Reinitialize the database
python setup_system.py
```

**Web Search Not Working**
- Ensure Chrome/Chromium is installed
- Check `web_search.enabled` in config.json
- Verify network connectivity

**Permission Errors**
```bash
# Ensure correct permissions
chmod -R 755 data/ conversations/ uploads/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues and questions:
- Create an issue on GitHub
- Contact the HE team

## Acknowledgments

- Ollama for local LLM inference
- ChromaDB for vector database
- The open-source community

## Changelog

### Version 2.1.2 (2025-10-17)

**API Notebook Improvements:**
- Reorganized JSON processing section (7.5) with proper subsection ordering
- Removed duplicate section headers and subsections
- Added section 6.5: RAG dataset creation from markdown files
  - Demonstrates loading `data/combined_data.md` into the RAG system
  - Shows verification of loaded data via RAG statistics
- Updated JSON file examples to use warpage analysis data
  - Changed from generic user data to `data/warpage_data/20250925_stats.json`
  - Includes sample warpage statistics structure with auto-generation if file missing
- Improved documentation clarity and workflow examples

**File Changes:**
- `python_API_call.ipynb`: Major reorganization and content updates

---

**Version**: 2.1.2
**Last Updated**: 2025-10-17

### Previous Versions

**Version 2.1.1 (2025-10-17)**
- Initial comprehensive API documentation
- Complete endpoint coverage in Jupyter notebook

**Version 1.0.0**
- Initial release with core features

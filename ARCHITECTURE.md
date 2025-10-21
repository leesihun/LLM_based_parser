# Backend Architecture

**Version**: 2.2.0
**Date**: 2025-10-21

## Overview

The backend follows a clean **3-tier layered architecture** for separation of concerns and maintainability.

```
┌─────────────────────────────────────────────────┐
│          HTTP/API Layer (Flask)                 │
│              backend/app/                       │
│  - Flask app factory                            │
│  - Routes (API endpoints)                       │
│  - HTTP error handlers                          │
│  - Dependency injection (ServiceContainer)      │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│         Business Logic Layer                    │
│              backend/core/                      │
│  - LLM client                                   │
│  - Agentic system (ReAct, planning, memory)     │
│  - Authentication & user management             │
│  - Conversation memory                          │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│           Services Layer                        │
│            backend/services/                    │
│  - RAG system (ChromaDB)                        │
│  - File processing (PDF, DOCX, etc.)            │
│  - Web search integration                       │
│  - Agent tools (calculators, validators, etc.)  │
└─────────────────────────────────────────────────┘
```

---

## Layer Breakdown

### 1. App Layer (`backend/app/`)

**Purpose**: HTTP/REST API handling (Flask-specific code)

**Responsibilities**:
- Define Flask application and configuration
- Register API routes (endpoints)
- Handle HTTP requests/responses
- Authentication decorators
- Error handling and formatting
- Dependency injection via ServiceContainer

**Key Files**:

```
backend/app/
├── __init__.py          # Flask app factory, CORS config
├── container.py         # Service dependency injection
├── errors.py            # HTTP error handlers
└── routes/              # API endpoints
    ├── __init__.py      # Blueprint registration
    ├── admin.py         # Admin endpoints
    ├── auth.py          # Authentication endpoints
    ├── chat.py          # Chat endpoints
    ├── conversations.py # Conversation management
    ├── files.py         # File upload/analysis
    ├── model_config.py  # Model configuration
    ├── rag.py           # RAG endpoints
    ├── search.py        # Web search endpoints
    ├── system.py        # System endpoints (health, config)
    ├── context.py       # Request context helpers
    └── decorators.py    # Auth decorators
```

**Why it's necessary**:
- **Framework abstraction**: All Flask-specific code is isolated here
- **Easy framework swap**: Could replace Flask with FastAPI without changing core/services
- **Clear API contracts**: Each route file defines clear API endpoints
- **Reusable patterns**: Decorators, error handlers, etc.

---

### 2. Core Layer (`backend/core/`)

**Purpose**: Framework-agnostic business logic

**Responsibilities**:
- LLM interactions (chat completion, generation)
- Agentic workflow (ReAct, planning, execution)
- User authentication and management
- Conversation memory management
- Core business rules

**Key Files**:

```
backend/core/
├── llm/                      # LLM client (refactored)
│   ├── __init__.py
│   ├── client.py            # Main LLM client
│   ├── models.py            # Data models (LLMResponse, etc.)
│   └── prompts.py           # Prompt templates
│
├── agents/                   # Agentic system
│   ├── __init__.py
│   ├── base.py              # BaseAgent
│   ├── executor.py          # ReAct executor
│   ├── planner.py           # Task planner
│   ├── memory.py            # Agent memory
│   └── orchestrator.py      # Multi-agent orchestration
│
├── auth/                     # Authentication
│   ├── __init__.py
│   └── add_new_user.py      # User creation utility
│
├── conversation_memory.py    # Conversation history
└── user_management.py        # User management
```

**Why it's separate**:
- **Testability**: Can test business logic without HTTP layer
- **Reusability**: Core logic can be used in CLI, batch jobs, etc.
- **Domain focus**: Pure business logic, no web framework concerns

---

### 3. Services Layer (`backend/services/`)

**Purpose**: Specialized services and integrations

**Responsibilities**:
- RAG (Retrieval-Augmented Generation) system
- File processing (PDF, DOCX, Excel, etc.)
- Web search integration
- Agent tools (calculators, validators, analyzers)

**Key Files**:

```
backend/services/
├── rag/                          # RAG system
│   ├── __init__.py
│   ├── rag_system.py            # Main RAG implementation
│   ├── advanced_rag_system.py   # Advanced features
│   └── knowledge_graph.py       # Knowledge graph integration
│
├── files/                        # File processing
│   ├── __init__.py
│   ├── file_handler.py          # File upload/storage
│   ├── enhanced_file_processor.py # Advanced processing
│   └── excel_to_md_converter.py # Excel conversion
│
├── search/                       # Web search
│   ├── __init__.py
│   ├── web_search_feature.py    # Main search feature
│   ├── keyword_extractor.py     # Keyword extraction
│   ├── manager.py               # Search manager
│   ├── content_loader.py        # Content loading
│   ├── result_filter.py         # Result filtering
│   ├── cache.py                 # Search cache
│   ├── analytics.py             # Search analytics
│   ├── settings.py              # Search settings
│   ├── types.py                 # Type definitions
│   ├── utils.py                 # Utilities
│   └── providers/               # Search providers
│
└── agents/tools/                 # Agent tools
    ├── __init__.py
    ├── base.py                  # Base tool interface
    ├── numeric_summary.py       # Numeric analysis
    ├── calculator.py            # Calculations
    ├── validator.py             # Validation
    └── json_analyzer.py         # JSON analysis
```

**Why it's separate**:
- **Modularity**: Each service can be developed/tested independently
- **Optional features**: Can disable RAG, web search, etc.
- **Specialized logic**: Each service has its own domain expertise

---

## Dependency Flow

### Request Flow (Example: Chat API)

```
1. Client → POST /api/chat

2. App Layer (routes/chat.py)
   - Receives HTTP request
   - Validates authentication (decorator)
   - Extracts parameters (message, session_id)
   ↓
3. Core Layer (conversation_memory.py, llm/client.py)
   - Loads conversation history from memory
   - Calls LLM with context
   - Processes LLM response
   ↓
4. App Layer (routes/chat.py)
   - Formats response as JSON
   - Returns HTTP response

5. Client ← {"session_id": "...", "response": "..."}
```

### Service Initialization (Dependency Injection)

```python
# In app/container.py
class ServiceContainer:
    """Bundle of core backend services shared across routes."""

    llm_client: LLMClient          # Core layer
    memory: ConversationMemory     # Core layer
    user_manager: UserManager      # Core layer
    rag_system: RAGSystem          # Services layer
    file_handler: FileHandler      # Services layer
    web_search: WebSearchFeature   # Services layer

    @classmethod
    def build(cls, config_path: str) -> ServiceContainer:
        """Construct services using shared configuration."""
        llm_client = LLMClient(config_path)
        memory = ConversationMemory()
        user_manager = UserManager(...)
        rag_system = RAGSystem(config_path)
        file_handler = FileHandler()
        web_search = WebSearchFeature(...)

        return cls(
            llm_client=llm_client,
            memory=memory,
            user_manager=user_manager,
            rag_system=rag_system,
            file_handler=file_handler,
            web_search=web_search,
        )
```

All routes receive the same `ServiceContainer` instance via dependency injection.

---

## Why This Architecture?

### ✅ Separation of Concerns

Each layer has a single responsibility:
- **App**: HTTP/API handling
- **Core**: Business logic
- **Services**: Specialized features

### ✅ Testability

Each layer can be tested independently:
- **App**: HTTP integration tests
- **Core**: Unit tests for business logic
- **Services**: Service-specific tests

### ✅ Maintainability

Clear boundaries make it easy to:
- Find code (consistent organization)
- Add features (extend in appropriate layer)
- Fix bugs (isolated changes)

### ✅ Scalability

Can scale different layers independently:
- Add more API workers (app layer)
- Use distributed LLM (core layer)
- Add search replicas (services layer)

### ✅ Framework Independence

Core business logic doesn't depend on Flask:
- Could swap Flask for FastAPI
- Could use in CLI tools
- Could run as batch jobs

---

## Common Patterns

### 1. Blueprint Pattern (App Layer)

Each route file creates a Flask Blueprint:

```python
# routes/chat.py
def create_blueprint(ctx: RouteContext) -> Blueprint:
    bp = Blueprint("chat", __name__, url_prefix="/api/chat")

    @bp.post("")
    @ctx.require_auth
    def send_message():
        # Route logic here
        pass

    return bp
```

### 2. Dependency Injection (App Layer)

ServiceContainer provides all dependencies:

```python
# routes/chat.py
def create_blueprint(ctx: RouteContext) -> Blueprint:
    services = ctx.services  # All services available here

    # Use services
    llm_client = services.llm_client
    memory = services.memory
    rag_system = services.rag_system
    # etc.
```

### 3. Factory Pattern (Core Layer)

LLMClient and other core components use factory initialization:

```python
# core/llm/client.py
class LLMClient:
    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self._initialize()
```

### 4. Service Pattern (Services Layer)

Each service is self-contained:

```python
# services/rag/rag_system.py
class RAGSystem:
    def __init__(self, config_path: str):
        # Initialize ChromaDB, embeddings, etc.
        pass

    def get_context_for_query(self, query: str) -> str:
        # RAG-specific logic
        pass
```

---

## Utilities & Common

### `backend/utils/`

Shared utilities used across all layers:
- `exceptions.py` - Custom exception classes
- `json_utils.py` - JSON manipulation helpers
- `validators.py` - Data validation functions

### `backend/common/`

Common code and constants:
- `errors.py` - Error definitions
- `__init__.py` - Common imports

---

## Configuration

All layers share the same configuration from `config.json`:

```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "model": "llama3.2:latest",
    "temperature": 0.7,
    "num_ctx": 8192
  },
  "web_search": {
    "enabled": true,
    "default_provider": "searxng"
  },
  "rag": {
    "enabled": true,
    "chunk_size": 500,
    "chunk_overlap": 50
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

---

## Adding New Features

### Adding a New API Endpoint

1. **Create route** in `backend/app/routes/`:
   ```python
   # routes/my_feature.py
   def create_blueprint(ctx: RouteContext) -> Blueprint:
       bp = Blueprint("my_feature", __name__, url_prefix="/api/my-feature")

       @bp.post("/action")
       @ctx.require_auth
       def do_action():
           # Implementation
           pass

       return bp
   ```

2. **Register blueprint** in `backend/app/routes/__init__.py`:
   ```python
   from backend.app.routes import my_feature

   _BLUEPRINT_FACTORIES = (
       # ... existing blueprints
       my_feature.create_blueprint,
   )
   ```

### Adding a New Service

1. **Create service** in `backend/services/my_service/`:
   ```python
   # services/my_service/my_service.py
   class MyService:
       def __init__(self, config: dict):
           # Initialize
           pass

       def do_something(self):
           # Service logic
           pass
   ```

2. **Add to container** in `backend/app/container.py`:
   ```python
   from backend.services.my_service import MyService

   class ServiceContainer:
       my_service: MyService

       @classmethod
       def build(cls, config_path: str):
           # ... existing services
           my_service = MyService(config)

           return cls(
               # ... existing services
               my_service=my_service,
           )
   ```

3. **Use in routes**:
   ```python
   def create_blueprint(ctx: RouteContext) -> Blueprint:
       my_service = ctx.services.my_service
       # Use my_service
   ```

---

## Summary

The `backend/app/` folder is **absolutely necessary** because:

1. ✅ **It's the HTTP layer** - Handles all Flask-specific code
2. ✅ **Separation of concerns** - Keeps web framework separate from business logic
3. ✅ **Clean architecture** - Follows industry best practices
4. ✅ **Maintainable** - Clear boundaries between layers
5. ✅ **Testable** - Each layer can be tested independently
6. ✅ **Scalable** - Layers can scale independently

**Do NOT delete `backend/app/`** - it's a critical part of the architecture!

---

## References

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Flask Blueprints](https://flask.palletsprojects.com/en/2.3.x/blueprints/)
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)

---

**Version**: 2.2.0
**Date**: 2025-10-21
**Status**: ✅ Documented

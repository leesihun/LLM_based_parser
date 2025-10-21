# Routes Guide - Understanding API Endpoints

**Version**: 2.2.0
**Date**: 2025-10-21

## What are Routes?

**Routes** are the API endpoints that clients (frontend, Jupyter notebooks, other applications) use to interact with your backend server.

Think of routes as **the menu of actions** your API provides.

---

## Simple Explanation

### Real-World Analogy

Imagine your backend is a **restaurant**:

- **Routes** = Menu items (what you can order)
- **HTTP Methods** = How you order (takeout, dine-in, delivery)
- **Request** = Your order (what you want)
- **Response** = The food you get back

### Example Route

```python
@bp.post("/api/chat")
def send_message():
    # When client POSTs to /api/chat
    # This function runs
    # Returns a response
```

**Translation**:
- "When someone sends a message to `/api/chat` using POST method"
- "Run the `send_message()` function"
- "Send back the AI's response"

---

## Your Application's Routes

Your backend has **11 route files**, each handling a specific area of functionality:

```
backend/app/routes/
├── admin.py         # User management (admin only)
├── auth.py          # Login/logout
├── chat.py          # Chat with AI
├── conversations.py # Conversation history
├── decorators.py    # Utilities (not a route file)
├── context.py       # Utilities (not a route file)
├── files.py         # File upload/analysis
├── model_config.py  # Model configuration
├── rag.py           # RAG system
├── search.py        # Web search
└── system.py        # Health checks, system info
```

---

## Complete Route List

### 1. Authentication Routes (`auth.py`)

**Purpose**: User login, logout, password management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/login` | Login and get token | No |
| POST | `/api/auth/logout` | Logout and invalidate token | Yes |
| GET | `/api/auth/me` | Get current user info | Yes |
| POST | `/api/auth/change-password` | Change password | Yes |

**Example**:
```python
# Login
POST /api/auth/login
Body: {"username": "guest", "password": "guest_test1"}
Response: {"session_token": "abc123...", "user": {...}}

# Get current user
GET /api/auth/me
Header: Authorization: Bearer abc123...
Response: {"user": {"username": "guest", ...}}
```

---

### 2. Chat Routes (`chat.py`)

**Purpose**: AI chat functionality

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/chat` | Normal chat | Yes |
| POST | `/api/chat/rag` | RAG-enabled chat | Yes |
| POST | `/api/chat/web-search` | Web search chat | Yes |
| POST | `/api/chat/with-json` | High-accuracy JSON analysis | Yes |
| POST | `/api/chat/messages` | Advanced chat with options | Yes |
| GET | `/api/chat/sessions` | List chat sessions | Yes |
| GET | `/api/chat/sessions/<id>` | Get session history | Yes |
| DELETE | `/api/chat/sessions/<id>` | Delete session | Yes |

**Example**:
```python
# Normal chat
POST /api/chat
Body: {"message": "Hello!", "session_id": "optional"}
Response: {"session_id": "123", "response": "Hi there!"}

# JSON analysis
POST /api/chat/with-json
Body: {
  "message": "What's the max value?",
  "json_data": {"values": [1, 5, 3, 9, 2]},
  "temperature": 0.0
}
Response: {"response": "The maximum value is 9", ...}
```

---

### 3. File Routes (`files.py`)

**Purpose**: File upload and analysis

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/files/upload` | Upload file | Yes |
| GET | `/api/files` | List uploaded files | Yes |
| POST | `/api/files/<id>/read` | Analyze file | Yes |
| DELETE | `/api/files/<id>` | Delete file | Yes |

**Example**:
```python
# Upload file
POST /api/files/upload
Content-Type: multipart/form-data
Body: file=document.pdf
Response: {"success": true, "file_id": "abc123", ...}

# Analyze file
POST /api/files/abc123/read
Body: {"question": "Summarize this document"}
Response: {"response": "This document discusses...", ...}
```

---

### 4. RAG Routes (`rag.py`)

**Purpose**: RAG (Retrieval-Augmented Generation) system

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/rag/add-document` | Add document to knowledge base | Yes |
| POST | `/api/rag/search` | Search knowledge base | Yes |
| GET | `/api/rag/stats` | Get RAG statistics | Yes |

**Example**:
```python
# Add document
POST /api/rag/add-document
Body: {
  "content": "Warpage is a deformation...",
  "metadata": {"title": "Warpage Guide", "source": "manual"}
}
Response: {"success": true, "document_id": "doc123"}

# Search
POST /api/rag/search
Body: {"query": "What is warpage?", "top_k": 5}
Response: {"results": [{content: "...", score: 0.95}, ...]}
```

---

### 5. Conversation Routes (`conversations.py`)

**Purpose**: Manage conversation sessions

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/conversations` | Create new conversation | Yes |
| GET | `/api/conversations/<id>/history` | Get conversation history | Yes |

**Example**:
```python
# Create conversation
POST /api/conversations
Response: {"session_id": "conv123"}

# Get history
GET /api/conversations/conv123/history
Response: {
  "session_id": "conv123",
  "history": [
    {"role": "user", "content": "Hello", "timestamp": "..."},
    {"role": "assistant", "content": "Hi!", "timestamp": "..."}
  ]
}
```

---

### 6. Admin Routes (`admin.py`)

**Purpose**: User management (admin only)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/users` | List all users | Admin |
| POST | `/api/admin/users` | Create new user | Admin |
| DELETE | `/api/admin/users/<username>` | Delete user | Admin |
| PUT | `/api/admin/users/<username>` | Update user | Admin |
| POST | `/api/admin/users/<username>/reset-password` | Reset password | Admin |

**Example**:
```python
# Create user (admin only)
POST /api/admin/users
Body: {
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "role": "user"
}
Response: {"success": true, "message": "User created", ...}

# List users
GET /api/admin/users
Response: {
  "users": [
    {"username": "guest", "role": "user", ...},
    {"username": "admin", "role": "admin", ...}
  ]
}
```

---

### 7. System Routes (`system.py`)

**Purpose**: System health and configuration

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check | No |
| GET | `/api/config` | Get configuration | No |
| POST | `/api/config` | Update configuration | Yes |
| GET | `/api/models` | List available models | No |

**Example**:
```python
# Health check
GET /health
Response: {
  "status": "healthy",
  "model": "llama3.2:latest",
  "ollama_url": "http://localhost:11434",
  "web_search_enabled": true,
  ...
}

# List models
GET /api/models
Response: {
  "models": [
    {"name": "llama3.2:latest", "size": "2.0GB"},
    {"name": "mistral:latest", "size": "4.1GB"}
  ]
}
```

---

### 8. Search Routes (`search.py`)

**Purpose**: Web search

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/search/web` | Perform web search | Yes |

**Example**:
```python
# Web search
POST /api/search/web
Body: {"query": "latest AI news", "num_results": 5}
Response: {
  "results": [
    {"title": "...", "url": "...", "snippet": "..."},
    ...
  ]
}
```

---

### 9. Model Config Routes (`model_config.py`)

**Purpose**: LLM model configuration

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/model/config` | Get current model config | Yes |
| POST | `/api/model/config` | Update model config | Yes |

**Example**:
```python
# Get config
GET /api/model/config
Response: {
  "model": "llama3.2:latest",
  "temperature": 0.7,
  "num_ctx": 8192
}

# Update config
POST /api/model/config
Body: {"temperature": 0.5, "num_ctx": 4096}
Response: {"success": true, "message": "Config updated"}
```

---

## How Routes Work

### Route Anatomy

```python
@bp.post("/api/chat")           # 1. HTTP method and URL path
@ctx.require_auth               # 2. Decorators (authentication)
def send_message():             # 3. Function name
    """Send a chat message.""" # 4. Documentation

    # 5. Get request data
    payload = request.get_json()
    message = payload.get("message")

    # 6. Process (business logic)
    response = llm_client.chat(message)

    # 7. Return response
    return jsonify({"response": response})
```

### Request Flow

```
Client Request
    ↓
1. HTTP Request arrives at route
   POST /api/chat
   Body: {"message": "Hello"}
    ↓
2. Decorators run (@require_auth)
   - Check authentication
   - Validate permissions
    ↓
3. Route function executes
   - Extract data from request
   - Call business logic
   - Format response
    ↓
4. Response sent back to client
   {"session_id": "123", "response": "Hi!"}
    ↓
Client receives response
```

---

## HTTP Methods Explained

| Method | Purpose | Has Body? | Example Use |
|--------|---------|-----------|-------------|
| GET | Retrieve data | No | List files, get user info |
| POST | Create/send data | Yes | Login, send chat message |
| PUT | Update data | Yes | Update user info |
| DELETE | Delete data | No | Delete file, delete user |

---

## Authentication

Most routes require authentication via Bearer token:

```python
# 1. Login to get token
POST /api/auth/login
Body: {"username": "guest", "password": "guest_test1"}
Response: {"session_token": "your-token-here"}

# 2. Use token in subsequent requests
GET /api/chat/sessions
Header: Authorization: Bearer your-token-here
```

### Routes That DON'T Require Auth:
- `/api/auth/login` - Login endpoint
- `/health` - Health check
- `/api/config` - Get config (GET only)
- `/api/models` - List models

### Routes That Require Admin:
- `/api/admin/*` - All admin routes

---

## Flask Blueprints

Each route file creates a **Blueprint** (a group of related routes):

```python
# In admin.py
def create_blueprint(ctx: RouteContext) -> Blueprint:
    bp = Blueprint("admin", __name__, url_prefix="/api/admin")

    @bp.get("/users")
    def list_users():
        # Route implementation
        pass

    return bp
```

**Blueprint** = A collection of routes with a common URL prefix

---

## Adding a New Route

### Example: Add a `/api/stats/summary` endpoint

1. **Choose the right file** (or create new):
   ```python
   # In routes/system.py (or create routes/stats.py)
   ```

2. **Add the route**:
   ```python
   @bp.get("/summary")
   @ctx.require_auth
   def get_summary():
       """Get system statistics summary."""
       return jsonify({
           "total_users": len(user_manager.users),
           "total_sessions": len(memory.sessions),
           "total_files": len(file_handler.list_files())
       })
   ```

3. **Test it**:
   ```bash
   curl -H "Authorization: Bearer token" \
        http://localhost:8000/api/stats/summary
   ```

---

## Route Testing

### Using cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"guest","password":"guest_test1"}'

# Save token
TOKEN="your-token-here"

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"Hello!"}'
```

### Using Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={'username': 'guest', 'password': 'guest_test1'}
)
token = response.json()['session_token']

# Chat
response = requests.post(
    'http://localhost:8000/api/chat',
    headers={'Authorization': f'Bearer {token}'},
    json={'message': 'Hello!'}
)
print(response.json()['response'])
```

### Using Jupyter Notebook

See [API_examples.ipynb](API_examples.ipynb) for complete examples!

---

## Summary

### What Routes Are:
- ✅ API endpoints (URLs that accept requests)
- ✅ The "menu" of actions your API provides
- ✅ Python functions that handle HTTP requests
- ✅ Organized in `backend/app/routes/` by functionality

### Route Structure:
```
backend/app/routes/
├── admin.py         → /api/admin/*        (5 routes)
├── auth.py          → /api/auth/*         (4 routes)
├── chat.py          → /api/chat/*         (8 routes)
├── conversations.py → /api/conversations/* (2 routes)
├── files.py         → /api/files/*        (4 routes)
├── model_config.py  → /api/model/*        (2 routes)
├── rag.py           → /api/rag/*          (3 routes)
├── search.py        → /api/search/*       (1 route)
└── system.py        → /health, /api/config, /api/models (3 routes)
```

**Total**: ~32 API endpoints

---

## Quick Reference

| I want to... | Use this route |
|--------------|----------------|
| Login | `POST /api/auth/login` |
| Chat with AI | `POST /api/chat` |
| Search docs (RAG) | `POST /api/chat/rag` |
| Search web | `POST /api/chat/web-search` |
| Analyze JSON | `POST /api/chat/with-json` |
| Upload file | `POST /api/files/upload` |
| Analyze file | `POST /api/files/<id>/read` |
| Create user (admin) | `POST /api/admin/users` |
| Check system health | `GET /health` |
| List models | `GET /api/models` |

---

## See Also

- [API_REFERENCE.md](API_REFERENCE.md) - Complete API documentation
- [API_examples.ipynb](API_examples.ipynb) - Working code examples
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture

---

**Version**: 2.2.0
**Date**: 2025-10-21
**Status**: ✅ Complete

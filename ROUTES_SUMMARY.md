# Routes - Quick Summary

## What Are Routes?

**Routes** = The **URLs** your API responds to

Think of them as **doors** to your application:
- Each door (route) leads to a specific function
- Clients knock on a door (make HTTP request)
- Your backend opens the door and responds

---

## Visual Map

```
Your Backend Server (http://localhost:8000)
│
├── 🏠 /                                → "API is running"
│
├── 🏥 /health                          → System health check
│
└── 📡 /api/
    │
    ├── 🔐 /auth/
    │   ├── /login                      → Login (get token)
    │   ├── /logout                     → Logout
    │   ├── /me                         → Get current user
    │   └── /change-password            → Change password
    │
    ├── 💬 /chat/
    │   ├── (POST)                      → Normal chat
    │   ├── /rag                        → RAG search chat
    │   ├── /web-search                 → Web search chat
    │   ├── /with-json                  → JSON analysis
    │   ├── /messages                   → Advanced chat
    │   └── /sessions/
    │       ├── (GET)                   → List sessions
    │       ├── /<id> (GET)             → Get session
    │       └── /<id> (DELETE)          → Delete session
    │
    ├── 📁 /files/
    │   ├── /upload                     → Upload file
    │   ├── (GET)                       → List files
    │   ├── /<id>/read                  → Analyze file
    │   └── /<id> (DELETE)              → Delete file
    │
    ├── 📚 /rag/
    │   ├── /add-document               → Add to knowledge base
    │   ├── /search                     → Search knowledge base
    │   └── /stats                      → Get statistics
    │
    ├── 👥 /admin/
    │   └── /users/
    │       ├── (GET)                   → List users
    │       ├── (POST)                  → Create user
    │       ├── /<username> (PUT)       → Update user
    │       ├── /<username> (DELETE)    → Delete user
    │       └── /<username>/reset-pwd   → Reset password
    │
    ├── 🔍 /search/
    │   └── /web                        → Web search
    │
    ├── 💬 /conversations/
    │   ├── (POST)                      → Create conversation
    │   └── /<id>/history               → Get history
    │
    ├── 🤖 /model/
    │   └── /config                     → Get/update model config
    │
    ├── ⚙️  /config                      → Get/update system config
    │
    └── 📋 /models                       → List available models
```

---

## Quick Reference Table

| Route | Method | What It Does | Auth? |
|-------|--------|--------------|-------|
| `/api/auth/login` | POST | Login and get token | ❌ No |
| `/api/chat` | POST | Chat with AI | ✅ Yes |
| `/api/chat/rag` | POST | Search docs + chat | ✅ Yes |
| `/api/chat/web-search` | POST | Web search + chat | ✅ Yes |
| `/api/chat/with-json` | POST | Analyze JSON data | ✅ Yes |
| `/api/files/upload` | POST | Upload a file | ✅ Yes |
| `/api/files/<id>/read` | POST | Analyze uploaded file | ✅ Yes |
| `/api/rag/search` | POST | Search knowledge base | ✅ Yes |
| `/api/admin/users` | POST | Create user | 👑 Admin |
| `/health` | GET | Check if system is OK | ❌ No |

---

## Example Usage

### 1. Login (Get Token)
```bash
POST http://localhost:8000/api/auth/login
Body: {"username": "guest", "password": "guest_test1"}

Response: {"session_token": "abc123..."}
```

### 2. Chat (Use Token)
```bash
POST http://localhost:8000/api/chat
Header: Authorization: Bearer abc123...
Body: {"message": "Hello!"}

Response: {"response": "Hi there! How can I help?"}
```

### 3. Upload File
```bash
POST http://localhost:8000/api/files/upload
Header: Authorization: Bearer abc123...
Body: (multipart file upload)

Response: {"file_id": "file123", "original_name": "doc.pdf"}
```

### 4. Analyze File
```bash
POST http://localhost:8000/api/files/file123/read
Header: Authorization: Bearer abc123...
Body: {"question": "Summarize this document"}

Response: {"response": "This document discusses..."}
```

---

## Where Routes Are Defined

All routes are in `backend/app/routes/`:

```
backend/app/routes/
├── admin.py         → Admin/user management routes
├── auth.py          → Login/logout routes
├── chat.py          → Chat routes (most important!)
├── conversations.py → Conversation management
├── files.py         → File upload/analysis routes
├── model_config.py  → Model configuration
├── rag.py           → RAG system routes
├── search.py        → Web search routes
└── system.py        → Health/config routes
```

---

## How It Works

```
1. Client sends request
   ↓
   POST http://localhost:8000/api/chat
   Body: {"message": "Hello"}

2. Flask receives request
   ↓
   Looks for route matching "/api/chat"

3. Finds route in routes/chat.py
   ↓
   @bp.post("")  ← This matches!

4. Runs authentication decorator
   ↓
   @ctx.require_auth  ← Checks token

5. Executes route function
   ↓
   def send_chat_message():
       # Process message
       # Call LLM
       # Return response

6. Sends response back
   ↓
   {"response": "Hi there!"}
```

---

## Authentication Flow

```
┌─────────────────────────────────────┐
│ 1. Login (no auth required)         │
│    POST /api/auth/login             │
│    ↓                                │
│    Get Token: "abc123..."           │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ 2. Use Token for other routes       │
│    POST /api/chat                   │
│    Header: Authorization: Bearer... │
│    ↓                                │
│    Access granted!                  │
└─────────────────────────────────────┘
```

---

## Categories

### 🔐 Authentication
- Login/logout
- User info
- Password management

### 💬 Chat & AI
- Normal chat
- RAG search
- Web search
- JSON analysis

### 📁 File Management
- Upload files
- Analyze files (PDF, DOCX, etc.)
- List/delete files

### 👥 Admin
- User management
- User creation/deletion
- Password reset

### ⚙️ System
- Health checks
- Configuration
- Model management

---

## Common Patterns

### POST (Send Data)
```python
POST /api/chat
Body: {"message": "Hello"}
→ Sends data to server
```

### GET (Retrieve Data)
```python
GET /api/files
→ Gets list of files
```

### DELETE (Remove Data)
```python
DELETE /api/files/abc123
→ Deletes file abc123
```

### PUT (Update Data)
```python
PUT /api/admin/users/john
Body: {"email": "new@email.com"}
→ Updates user john's email
```

---

## See Full Details

- **[ROUTES_GUIDE.md](ROUTES_GUIDE.md)** - Complete route documentation
- **[API_REFERENCE.md](API_REFERENCE.md)** - Full API reference
- **[API_examples.ipynb](API_examples.ipynb)** - Working code examples

---

## Summary

**Routes** are simply:
- ✅ URLs your API responds to
- ✅ The "menu" of available actions
- ✅ Defined in `backend/app/routes/*.py` files
- ✅ Handle HTTP requests and return responses

**Total Routes**: ~32 endpoints across 9 categories

---

**Version**: 2.2.0

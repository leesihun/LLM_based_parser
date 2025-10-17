# API Documentation

Complete API reference for the HE Team LLM Assistant.

## Table of Contents

- [Authentication](#authentication)
- [Chat & Conversations](#chat--conversations)
- [Web Search](#web-search)
- [RAG (Knowledge Base)](#rag-knowledge-base)
- [File Management](#file-management)
- [Admin & User Management](#admin--user-management)
- [Model Configuration](#model-configuration)
- [System & Health](#system--health)
- [Error Handling](#error-handling)

## Base URL

All API endpoints are prefixed with the base URL:
```
http://10.252.38.241:8000
```

## Authentication

All endpoints (except `/api/auth/login` and `/health`) require authentication via Bearer token.

### Headers

```http
Authorization: Bearer <session_token>
Content-Type: application/json
```

---

## Authentication

### POST /api/auth/login

Authenticate a user and receive a session token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "administrator"
}
```

**Response (200 OK):**
```json
{
  "session_token": "xGP2ZM4V0F4hm6s8rQYosTI1Iuwr0x4qMvBu7nacVWE",
  "user": {
    "user_id": "sudo",
    "username": "admin",
    "email": "admin@heteam.com",
    "role": "admin",
    "display_name": "Administrator"
  },
  "message": "Login successful"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "Invalid username or password"
}
```

---

### POST /api/auth/logout

Logout and invalidate the current session token.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

---

### GET /api/auth/me

Get current authenticated user information.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "user": {
    "user_id": "sudo",
    "username": "admin",
    "email": "admin@heteam.com",
    "role": "admin",
    "display_name": "Administrator"
  }
}
```

---

### POST /api/auth/change-password

Change the password for the current user.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "old_password": "admin123",
  "new_password": "newpassword456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## Chat & Conversations

### POST /api/chat/messages

Send a chat message and receive an AI response.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "What is machine learning?",
  "session_id": "optional-session-id",
  "use_rag": false,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Parameters:**
- `message` (required): User's message text
- `session_id` (optional): Conversation session ID. If not provided, a new session is created
- `use_rag` (optional): Enable RAG context injection (default: false)
- `temperature` (optional): LLM temperature override (default: from config)
- `max_tokens` (optional): Maximum tokens override (default: from config)

**Response (200 OK):**
```json
{
  "session_id": "session-20251017-123456",
  "message": "Machine learning is a subset of artificial intelligence...",
  "raw": {
    "content": "Machine learning is...",
    "model": "gemma3:12b",
    "done": true
  },
  "history": [
    {
      "role": "user",
      "content": "What is machine learning?",
      "timestamp": "2025-10-17T10:30:00.000000"
    },
    {
      "role": "assistant",
      "content": "Machine learning is...",
      "timestamp": "2025-10-17T10:30:05.000000"
    }
  ]
}
```

---

### POST /api/chat

**Legacy endpoint** for old frontend compatibility. Send a normal chat message.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "Hello",
  "session_id": "optional-session-id"
}
```

**Response (200 OK):**
```json
{
  "session_id": "session-id",
  "response": "Hello! How can I help you today?"
}
```

---

### POST /api/chat/rag

**Legacy endpoint** for RAG-enabled chat messages.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "What does the knowledge base say about Fold 7?",
  "session_id": "optional-session-id"
}
```

**Response (200 OK):**
```json
{
  "session_id": "session-id",
  "response": "According to the knowledge base, Fold 7 is described as..."
}
```

---

### POST /api/chat/web-search

**Legacy endpoint** for web search-enabled chat.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "Latest news about AI developments",
  "session_id": "optional-session-id"
}
```

**Response (200 OK):**
```json
{
  "session_id": "session-id",
  "response": "Based on current search results...",
  "keyword_extraction_used": true,
  "optimized_queries": ["AI developments", "artificial intelligence news"],
  "successful_query": "AI developments",
  "search_results": [
    {
      "title": "Recent AI Breakthroughs",
      "url": "https://example.com/ai-news",
      "snippet": "New developments in AI..."
    }
  ]
}
```

---

### GET /api/chat/sessions

List all sessions for the current user.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "id": "session-20251017-123456",
      "user_id": "sudo",
      "created_at": "2025-10-17T10:00:00.000000",
      "last_activity": "2025-10-17T10:30:00.000000",
      "metadata": {
        "title": "Machine Learning Discussion",
        "total_messages": 10
      }
    }
  ]
}
```

---

### GET /api/chat/sessions/:session_id

Get specific session details.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "session_id": "session-20251017-123456",
  "history": [
    {
      "role": "user",
      "content": "What is machine learning?",
      "timestamp": "2025-10-17T10:30:00.000000"
    },
    {
      "role": "assistant",
      "content": "Machine learning is...",
      "timestamp": "2025-10-17T10:30:05.000000"
    }
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "session_id": "invalid-id",
  "history": []
}
```

---

### DELETE /api/chat/sessions/:session_id

Delete a conversation session.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "deleted": true
}
```

---

## Conversations

### GET /api/conversations/

List all conversations for the current user.

**Headers Required:** `Authorization: Bearer <token>`

**Response:** Same as `/api/chat/sessions`

---

### GET /api/conversations/:session_id

Get conversation metadata.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "conversation": {
    "id": "session-20251017-123456",
    "user_id": "sudo",
    "created_at": "2025-10-17T10:00:00.000000",
    "last_activity": "2025-10-17T10:30:00.000000",
    "title": "Machine Learning Discussion",
    "total_messages": 10
  }
}
```

---

### GET /api/conversations/:session_id/history

Get conversation message history.

**Headers Required:** `Authorization: Bearer <token>`

**Query Parameters:**
- `include_system` (optional): Include system messages (default: false)

**Response (200 OK):**
```json
{
  "session_id": "session-20251017-123456",
  "history": [
    {
      "role": "user",
      "content": "What is machine learning?",
      "timestamp": "2025-10-17T10:30:00.000000"
    }
  ]
}
```

---

### DELETE /api/conversations/:session_id

Delete a conversation.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "deleted": true
}
```

---

## Web Search

### POST /api/search/web

Perform a web search and return results.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "max_results": 5
}
```

**Parameters:**
- `query` (required): Search query string
- `max_results` (optional): Number of results to return (default: 5)

**Response (200 OK):**
```json
{
  "success": true,
  "query": "machine learning algorithms",
  "results": [
    {
      "title": "Introduction to ML Algorithms",
      "url": "https://example.com/ml-intro",
      "snippet": "Machine learning algorithms are...",
      "relevance_score": 0.95
    }
  ],
  "total_results": 5,
  "search_time": 2.34
}
```

---

### POST /api/search/extract-keywords

Extract keywords from text using LLM-assisted extraction.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "text": "I want to learn about machine learning algorithms and neural networks"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "keywords": ["machine learning", "algorithms", "neural networks"],
  "adequate_keywords": true,
  "extraction_method": "llm",
  "original_query": "I want to learn about machine learning algorithms and neural networks"
}
```

---

### GET /api/search/status

Get web search system status and capabilities.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "enabled": true,
  "keyword_extraction_enabled": true,
  "capabilities": {
    "selenium_available": true,
    "typescript_search_available": true,
    "keyword_extraction_available": true,
    "providers": ["duckduckgo", "bing", "brave"]
  }
}
```

---

### POST /api/search/keyword-extraction/enable

Enable keyword extraction feature (Admin only).

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Response (200 OK):**
```json
{
  "success": true,
  "enabled": true
}
```

---

### POST /api/search/keyword-extraction/disable

Disable keyword extraction feature (Admin only).

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Response (200 OK):**
```json
{
  "success": true,
  "enabled": false
}
```

---

## RAG (Knowledge Base)

### GET /api/rag/stats

Get RAG system statistics.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "stats": {
    "document_count": 2,
    "total_chunks": 450,
    "collection_name": "documents",
    "embedding_model": "nomic-embed-text:latest",
    "status": "ready"
  },
  "available": true
}
```

---

### POST /api/rag/search

Search the knowledge base.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "query": "What are users saying about Fold 7 battery life?",
  "n_results": 5
}
```

**Parameters:**
- `query` (required): Search query
- `n_results` (optional): Number of results (default: 5)

**Response (200 OK):**
```json
{
  "results": [
    {
      "content": "Using the Fold 7 is powerful in terms of battery life. I can't put it down.",
      "metadata": {
        "source": "data/폴드긍정.xlsx",
        "chunk_id": "chunk-123"
      },
      "similarity": 0.92
    }
  ],
  "query": "What are users saying about Fold 7 battery life?"
}
```

---

### GET /api/rag/context

Get formatted context for a query from RAG system.

**Headers Required:** `Authorization: Bearer <token>`

**Query Parameters:**
- `query` (required): Search query
- `max_length` (optional): Maximum context length

**Example:**
```
GET /api/rag/context?query=battery%20life&max_length=1000
```

**Response (200 OK):**
```json
{
  "context": "Based on the knowledge base:\n\n1. Using the Fold 7 is powerful in terms of battery life...\n2. Hands down, the Fold 7 is next-level in terms of battery life...",
  "query": "battery life"
}
```

---

## File Management

### POST /api/files/upload

Upload a file for analysis.

**Headers Required:** `Authorization: Bearer <token>`

**Request:** Multipart form data
- `file`: File to upload

**Allowed File Types:**
- Documents: `.pdf`, `.docx`, `.txt`, `.md`
- Data: `.xlsx`, `.xls`, `.csv`, `.json`
- Code: `.py`, `.js`, `.html`, `.xml`, `.yml`, `.yaml`

**Response (201 Created):**
```json
{
  "success": true,
  "file_id": "document-123",
  "filename": "report.pdf",
  "message": "File 'report.pdf' uploaded successfully"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "File type not allowed. Supported types: .pdf, .docx, ..."
}
```

---

### GET /api/files

List all uploaded files for current user.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "files": [
    {
      "file_id": "document-123",
      "original_name": "report.pdf",
      "file_type": ".pdf",
      "size": 1048576,
      "uploaded_at": 1697539200.0
    }
  ]
}
```

---

### POST /api/files/:file_id/read

Read and analyze a file with a question.

**Headers Required:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "question": "What are the main findings in this document?",
  "session_id": "optional-session-id"
}
```

**Response (200 OK):**
```json
{
  "response": "Based on the document, the main findings are...",
  "session_id": "session-id",
  "file_id": "document-123"
}
```

---

### DELETE /api/files/:file_id

Delete an uploaded file.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

---

## Admin & User Management

All admin endpoints require the user to have `admin` role.

### GET /api/admin/users

List all users in the system.

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Response (200 OK):**
```json
{
  "users": [
    {
      "username": "admin",
      "user_id": "sudo",
      "email": "admin@heteam.com",
      "role": "admin",
      "display_name": "Administrator",
      "is_active": true,
      "created_at": "2025-08-08T13:09:22.207394",
      "last_login": "2025-10-16T17:17:39.134194"
    }
  ]
}
```

---

### POST /api/admin/users

Create a new user.

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Request Body:**
```json
{
  "username": "newuser",
  "password": "secure_password",
  "email": "newuser@heteam.com",
  "role": "user",
  "display_name": "New User"
}
```

**Parameters:**
- `username` (required): Unique username
- `password` (required): User password
- `email` (required): User email
- `role` (optional): "user" or "admin" (default: "user")
- `display_name` (optional): Display name (default: username)

**Response (201 Created):**
```json
{
  "success": true,
  "message": "User 'newuser' created successfully",
  "user": {
    "username": "newuser",
    "email": "newuser@heteam.com",
    "role": "user",
    "display_name": "New User"
  }
}
```

---

### PUT /api/admin/users/:username

Update user details.

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Request Body:**
```json
{
  "email": "updated@heteam.com",
  "role": "admin",
  "display_name": "Updated Name",
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "User 'newuser' updated successfully",
  "user": {
    "username": "newuser",
    "email": "updated@heteam.com",
    "role": "admin",
    "display_name": "Updated Name",
    "is_active": false
  }
}
```

---

### DELETE /api/admin/users/:username

Delete a user.

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "User 'username' deleted successfully"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Cannot delete admin user"
}
```

---

### POST /api/admin/users/:username/reset-password

Reset a user's password (Admin only).

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Request Body:**
```json
{
  "new_password": "new_secure_password"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password for user 'username' reset successfully"
}
```

---

## Model Configuration

### GET /api/config

Get current system configuration.

**Response (200 OK):**
Returns the entire config.json file content.

---

### POST /api/config

Update system configuration (Admin only).

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Request Body (Update Model):**
```json
{
  "model": "llama2:13b"
}
```

**Request Body (Update Ollama Config):**
```json
{
  "ollama": {
    "model": "gemma3:12b",
    "temperature": 0.8,
    "num_ctx": 4096
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "ollama": {
    "model": "gemma3:12b",
    "temperature": 0.8,
    "num_ctx": 4096
  }
}
```

---

### GET /api/models

List all available Ollama models.

**Response (200 OK):**
```json
{
  "models": [
    {
      "name": "gemma3:12b",
      "size": "7.4 GB",
      "modified_at": "2025-10-15T10:30:00Z"
    },
    {
      "name": "nomic-embed-text:latest",
      "size": "274.3 MB",
      "modified_at": "2025-10-14T08:15:00Z"
    }
  ]
}
```

---

### GET /api/config/model

Get current model configuration.

**Headers Required:** `Authorization: Bearer <token>`

**Response (200 OK):**
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

---

### POST /api/config/model

Update model configuration (Admin only).

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Request Body:**
```json
{
  "ollama": {
    "model": "llama2:13b",
    "temperature": 0.8
  }
}
```

**Response (200 OK):**
```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "model": "llama2:13b",
    "temperature": 0.8,
    "num_ctx": 8192
  }
}
```

---

## System & Health

### GET /health

System health check endpoint (no authentication required).

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T10:30:00.000000",
  "model": "gemma3:12b",
  "ollama_url": "http://localhost:11434",
  "web_search_enabled": true,
  "keyword_extraction_enabled": true
}
```

**Response (200 OK - Ollama Unreachable):**
```json
{
  "status": "ollama_unreachable",
  "timestamp": "2025-10-17T10:30:00.000000",
  "error": "Connection refused",
  "model": "gemma3:12b",
  "ollama_url": "http://localhost:11434"
}
```

---

### GET /api/system/info

Get detailed system information (Admin only).

**Headers Required:** `Authorization: Bearer <token>` (Admin role)

**Response (200 OK):**
```json
{
  "platform": "Windows-10-10.0.19045-SP0",
  "python_version": "3.11.5",
  "llm": {
    "model": "gemma3:12b",
    "endpoint": "http://localhost:11434"
  },
  "memory": {
    "total_sessions": 15,
    "active_sessions": 3,
    "total_messages": 450
  }
}
```

---

## Error Handling

### Standard Error Response Format

All error responses follow this structure:

```json
{
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Insufficient permissions (not admin)
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Common Error Responses

**Authentication Error:**
```json
{
  "error": "Authentication required"
}
```

**Validation Error:**
```json
{
  "error": "Message is required"
}
```

**Permission Error:**
```json
{
  "error": "Admin access required"
}
```

**Not Found:**
```json
{
  "error": "Session not found"
}
```

---

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

## Versioning

API version: **v1**

The API does not currently use versioned endpoints. Breaking changes will be announced in release notes.

---

## Additional Notes

### Session Management

- Sessions expire after 24 hours of inactivity
- Active sessions are stored in `backend/config/user_sessions.json`
- Session cleanup runs automatically

### File Upload Limits

- Maximum file size: Configured by web server (default: 16MB)
- Files are stored in `uploads/<user_id>/`
- User-specific isolation prevents cross-user file access

### Search Caching

- Search results are cached for 1 hour (configurable)
- Cache can be disabled in configuration
- Redis support available but disabled by default

### RAG Context Injection

When `use_rag: true` in chat requests:
1. Query is sent to RAG system
2. Top N relevant documents retrieved
3. Context prepended to conversation
4. LLM generates response with context

---

**API Version**: 1.0.0
**Last Updated**: 2025-10-17

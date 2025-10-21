# HE Team LLM Assistant - API Reference

**Version**: 2.2.0
**Base URL**: `http://localhost:8000`
**Date**: 2025-10-21

## Table of Contents

- [Authentication](#authentication)
- [Chat Endpoints](#chat-endpoints)
- [File Management](#file-management)
- [RAG System](#rag-system)
- [System & Configuration](#system--configuration)
- [Conversations](#conversations)
- [Admin](#admin)
- [Models](#models)
- [Error Handling](#error-handling)
- [Python Client](#python-client)

---

## Authentication

All API endpoints (except `/health` and login) require authentication via Bearer token.

### POST `/api/auth/login`

Login to obtain a session token.

**Request**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response** (200):
```json
{
  "session_token": "string",
  "user": {
    "user_id": "string",
    "username": "string",
    "display_name": "string",
    "email": "string",
    "role": "string"
  }
}
```

**Example**:
```python
import requests

response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={'username': 'guest', 'password': 'guest_test1'}
)
token = response.json()['session_token']
```

### POST `/api/auth/logout`

Logout and invalidate session token.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "message": "Logged out successfully"
}
```

### GET `/api/auth/me`

Get current user information.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "user": {
    "user_id": "string",
    "username": "string",
    "display_name": "string",
    "email": "string",
    "role": "string"
  }
}
```

### POST `/api/auth/change-password`

Change user password.

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**Response** (200):
```json
{
  "message": "Password changed successfully"
}
```

---

## Chat Endpoints

### POST `/api/chat`

Send a normal chat message (legacy endpoint for frontend compatibility).

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "message": "string",
  "session_id": "string (optional)"
}
```

**Response** (200):
```json
{
  "session_id": "string",
  "response": "string"
}
```

**Example**:
```python
response = requests.post(
    'http://localhost:8000/api/chat',
    headers={'Authorization': f'Bearer {token}'},
    json={'message': 'Hello, how are you?'}
)
print(response.json()['response'])
```

### POST `/api/chat/rag`

Send a RAG-enabled chat message (searches knowledge base).

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "message": "string",
  "session_id": "string (optional)"
}
```

**Response** (200):
```json
{
  "session_id": "string",
  "response": "string"
}
```

**Example**:
```python
response = requests.post(
    'http://localhost:8000/api/chat/rag',
    headers={'Authorization': f'Bearer {token}'},
    json={'message': 'What documents do we have about warpage?'}
)
```

### POST `/api/chat/web-search`

Send a web search-enabled chat message.

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "message": "string",
  "session_id": "string (optional)"
}
```

**Response** (200):
```json
{
  "session_id": "string",
  "response": "string",
  "keyword_extraction_used": boolean,
  "optimized_queries": ["string"],
  "successful_query": "string",
  "search_results": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string"
    }
  ]
}
```

**Example**:
```python
response = requests.post(
    'http://localhost:8000/api/chat/web-search',
    headers={'Authorization': f'Bearer {token}'},
    json={'message': 'What is the latest news about AI?'}
)
```

### POST `/api/chat/with-json`

Analyze JSON data with high accuracy (zero-hallucination mode).

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "message": "string",
  "json_data": object,  // Inline JSON data
  "file_id": "string (optional)",  // OR reference to uploaded JSON file
  "json_path": "string (optional)",  // Path to extract (e.g., "users.0.name")
  "session_id": "string (optional)",
  "temperature": 0.0,  // Recommended for factual accuracy
  "max_tokens": 2000
}
```

**Response** (200):
```json
{
  "session_id": "string",
  "response": "string",
  "context": "string",  // Full context sent to LLM
  "numeric_summary": "string",  // Auto-generated statistics
  "validation_notes": {
    "validated": boolean,
    "warnings": ["string"],
    "info": ["string"]
  },
  "message": [object],  // Full message array
  "memory": [object]  // Conversation history
}
```

**Example**:
```python
json_data = {
    "materials": [
        {"id": "ABC123", "name": "Material A", "warpage": 0.45},
        {"id": "XYZ789", "name": "Material B", "warpage": 1.23}
    ]
}

response = requests.post(
    'http://localhost:8000/api/chat/with-json',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'message': 'Which material has the lowest warpage?',
        'json_data': json_data,
        'temperature': 0.0
    }
)
```

### POST `/api/chat/messages`

Advanced chat endpoint with full configuration options.

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "message": "string",
  "session_id": "string (optional)",
  "use_rag": boolean,  // Enable RAG search
  "temperature": number,  // Override default temperature
  "max_tokens": number  // Max tokens to generate
}
```

**Response** (200):
```json
{
  "session_id": "string",
  "message": "string",  // Assistant response
  "response": {
    "content": "string",
    "processing_time": number,
    "tokens_per_second": number
  },
  "history": [object]  // Full conversation history
}
```

### GET `/api/chat/sessions`

List all chat sessions for the current user.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "sessions": [
    {
      "session_id": "string",
      "created_at": "string",
      "message_count": number
    }
  ]
}
```

### GET `/api/chat/sessions/<session_id>`

Get specific session history.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "session_id": "string",
  "history": [
    {
      "role": "string",  // "user" or "assistant"
      "content": "string",
      "timestamp": "string"
    }
  ]
}
```

### DELETE `/api/chat/sessions/<session_id>`

Delete a chat session.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "deleted": boolean
}
```

---

## File Management

### POST `/api/files/upload`

Upload a file for analysis.

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data**:
- `file`: File (PDF, DOCX, XLSX, TXT, MD, JSON, etc.)

**Response** (200):
```json
{
  "success": boolean,
  "file_id": "string",
  "original_name": "string",
  "file_type": "string",
  "size": number
}
```

**Example**:
```python
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/files/upload',
        headers={'Authorization': f'Bearer {token}'},
        files=files
    )
```

### GET `/api/files`

List all uploaded files for the current user.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "files": [
    {
      "file_id": "string",
      "original_name": "string",
      "file_type": "string",
      "size": number,
      "uploaded_at": "string"
    }
  ]
}
```

### POST `/api/files/<file_id>/read`

Analyze an uploaded file and ask questions about it.

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "question": "string",
  "session_id": "string (optional)"
}
```

**Response** (200):
```json
{
  "session_id": "string",
  "response": "string",
  "file_content": "string"  // Extracted text
}
```

### DELETE `/api/files/<file_id>`

Delete an uploaded file.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "success": boolean,
  "message": "string"
}
```

---

## RAG System

### POST `/api/rag/add-document`

Add a document to the RAG knowledge base.

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "content": "string",
  "metadata": {
    "title": "string",
    "source": "string"
  }
}
```

**Response** (200):
```json
{
  "success": boolean,
  "document_id": "string"
}
```

### POST `/api/rag/search`

Search the RAG knowledge base.

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "query": "string",
  "top_k": number  // Number of results (default: 5)
}
```

**Response** (200):
```json
{
  "results": [
    {
      "content": "string",
      "metadata": object,
      "score": number
    }
  ]
}
```

### GET `/api/rag/stats`

Get RAG system statistics.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "stats": {
    "document_count": number,
    "total_chunks": number,
    "indexed": boolean
  }
}
```

---

## System & Configuration

### GET `/health`

System health check (no authentication required).

**Response** (200):
```json
{
  "status": "healthy",
  "model": "string",
  "ollama_url": "string",
  "web_search_enabled": boolean,
  "keyword_extraction_enabled": boolean,
  "error": "string (if any)"
}
```

### GET `/api/config`

Get current system configuration.

**Response** (200):
```json
{
  "ollama": {
    "host": "string",
    "model": "string",
    "temperature": number,
    "num_ctx": number
  },
  "web_search": {
    "enabled": boolean,
    "default_provider": "string"
  }
}
```

### POST `/api/config`

Update system configuration.

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "model": "string (optional)",
  "temperature": number,
  "num_ctx": number
}
```

**Response** (200):
```json
{
  "success": boolean,
  "message": "string"
}
```

---

## Conversations

### POST `/api/conversations`

Create a new conversation session.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "session_id": "string"
}
```

### GET `/api/conversations/<session_id>/history`

Get conversation history.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "session_id": "string",
  "history": [
    {
      "role": "string",
      "content": "string",
      "timestamp": "string"
    }
  ]
}
```

---

## Admin

### POST `/api/admin/users`

Create a new user (admin only).

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "username": "string",
  "password": "string",
  "email": "string",
  "display_name": "string",
  "role": "user" | "admin"
}
```

**Response** (200):
```json
{
  "success": boolean,
  "user_id": "string"
}
```

---

## Models

### GET `/api/models`

List available LLM models from Ollama.

**Response** (200):
```json
{
  "models": [
    {
      "name": "string",
      "size": "string",
      "modified_at": "string"
    }
  ]
}
```

---

## Error Handling

All endpoints return standard error responses:

### Error Response Format

```json
{
  "error": "string",
  "message": "string",
  "status_code": number
}
```

### Common Status Codes

- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

---

## Python Client

### Complete Client Implementation

```python
import requests
import json

class LLMClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_token = None
        self.headers = {"Content-Type": "application/json"}

    def login(self, username: str, password: str) -> bool:
        """Login and obtain session token."""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            headers=self.headers,
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.session_token = data["session_token"]
            self.headers["Authorization"] = f"Bearer {self.session_token}"
            return True
        return False

    def chat(self, message: str, session_id=None, chat_type="normal",
             json_path=None, json_data=None) -> dict:
        """Send a message to the LLM API."""
        endpoint_map = {
            "normal": "/api/chat",
            "web_search": "/api/chat/web-search",
            "rag": "/api/chat/rag",
            "json": "/api/chat/with-json"
        }
        endpoint = endpoint_map.get(chat_type, "/api/chat")

        if chat_type == "json":
            payload = {
                "message": message,
                "json_data": json_data,
                "session_id": session_id,
                "temperature": 0.0
            }
        else:
            payload = {"message": message}
            if session_id:
                payload["session_id"] = session_id

        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload,
            timeout=600
        )
        return response.json() if response.status_code == 200 else None

    def upload_file(self, file_path: str) -> dict:
        """Upload a file for analysis."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {"Authorization": self.headers.get("Authorization")}
            response = requests.post(
                f"{self.base_url}/api/files/upload",
                headers=headers,
                files=files
            )
        return response.json()

    def analyze_file(self, file_id: str, question: str, session_id=None) -> dict:
        """Analyze an uploaded file."""
        response = requests.post(
            f"{self.base_url}/api/files/{file_id}/read",
            headers=self.headers,
            json={"question": question, "session_id": session_id}
        )
        return response.json()

    def list_conversations(self) -> list:
        """List all conversations."""
        response = requests.get(
            f"{self.base_url}/api/chat/sessions",
            headers=self.headers
        )
        return response.json()

    def get_conversation(self, session_id: str):
        """Get conversation history."""
        response = requests.get(
            f"{self.base_url}/api/chat/sessions/{session_id}",
            headers=self.headers
        )
        return response.json()

    def health_check(self) -> dict:
        """Check system health."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
```

### Usage Examples

```python
# Initialize client
client = LLMClient("http://localhost:8000")

# Login
client.login("guest", "guest_test1")

# Normal chat
result = client.chat("Hello, how are you?")
print(result['response'])

# RAG search
result = client.chat("What is warpage?", chat_type="rag")
print(result['response'])

# Web search
result = client.chat("Latest AI news", chat_type="web_search")
print(result['response'])

# JSON analysis
json_data = {"values": [1, 5, 3, 9, 2]}
result = client.chat(
    "What is the maximum value?",
    chat_type="json",
    json_data=json_data
)
print(result['response'])

# File upload and analysis
upload_result = client.upload_file("document.pdf")
file_id = upload_result['file_id']

analyze_result = client.analyze_file(file_id, "Summarize this document")
print(analyze_result['response'])

# Health check
health = client.health_check()
print(f"Status: {health['status']}, Model: {health['model']}")
```

---

## Rate Limiting

Currently no rate limiting implemented. For production use, consider adding:
- Per-user request limits
- Per-IP rate limiting
- Token bucket algorithm

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (not in code)
3. **Rotate secrets regularly**
4. **Implement proper CORS** (not `*`)
5. **Validate all inputs**
6. **Use environment variables** for sensitive config

---

## Support

For issues or questions:
- Check `/health` endpoint for system status
- Review error messages and status codes
- Contact: s.hun.lee

---

**API Reference Version**: 2.2.0
**Last Updated**: 2025-10-21

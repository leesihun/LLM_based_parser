# REST API Documentation

This document provides comprehensive documentation for all REST API endpoints in the HE Team LLM Assistant system.

## Authentication

All API endpoints (except login and health check) require authentication via Bearer token.

### Headers Required
```
Authorization: Bearer <session_token>
Content-Type: application/json
```

### Authentication Flow
1. **Login** → Receive session token
2. **Include token** in all subsequent requests
3. **Token expires** after 24 hours
4. **Re-authenticate** when token expires

---

## Authentication Endpoints

### Login

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate user and obtain session token

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "session_token": "string",
  "user": {
    "username": "string",
    "role": "string",
    "display_name": "string"
  }
}
```

**Error Response (401):**
```json
{
  "error": "Invalid credentials"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

---

### Logout

**Endpoint:** `POST /api/auth/logout`

**Description:** Terminate current session

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

### Get User Info

**Endpoint:** `GET /api/auth/me`

**Description:** Get current user information

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "user_id": "string",
  "username": "string",
  "email": "string",
  "role": "string",
  "display_name": "string",
  "created_at": "string",
  "is_active": true
}
```

---

### Change Password

**Endpoint:** `POST /api/auth/change-password`

**Description:** Change current user's password

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

---

## Chat Endpoints

### Normal Chat

**Endpoint:** `POST /api/chat`

**Description:** Standard AI conversation

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string (optional)"
}
```

**Success Response (200):**
```json
{
  "response": "string",
  "session_id": "string",
  "processing_time": 1250,
  "tokens_per_second": 15.2,
  "chat_type": "normal"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?"
  }'
```

---

### RAG Enhanced Chat

**Endpoint:** `POST /api/chat/rag`

**Description:** Chat with knowledge base search integration

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string (optional)",
  "max_results": 5
}
```

**Success Response (200):**
```json
{
  "response": "string",
  "session_id": "string",
  "processing_time": 1450,
  "tokens_per_second": 14.8,
  "rag_context_used": true,
  "search_results_count": 3,
  "chat_type": "rag"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/rag \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is our company policy on remote work?",
    "max_results": 5
  }'
```

---

### Web Search Chat

**Endpoint:** `POST /api/chat/web-search`

**Description:** Chat with live web search integration

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string (optional)",
  "max_results": 5
}
```

**Success Response (200):**
```json
{
  "response": "string",
  "session_id": "string",
  "processing_time": 2100,
  "tokens_per_second": 13.5,
  "search_processing_time": 850,
  "search_context_used": true,
  "search_results_count": 4,
  "keyword_extraction_used": true,
  "optimized_queries": [
    "AI developments 2024",
    "artificial intelligence latest news"
  ],
  "successful_query": "AI developments 2024",
  "chat_type": "web_search"
}
```

**Error Response - Inadequate Keywords (400):**
```json
{
  "error": "Cannot perform web search: no adequate keywords found. Query too generic or lacks searchable terms.",
  "search_failed": true
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/web-search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Latest AI developments in 2024"
  }'
```

---

## Search Endpoints

### Direct Web Search

**Endpoint:** `POST /api/search/web`

**Description:** Perform web search without chat context

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "query": "string",
  "max_results": 5
}
```

**Success Response (200):**
```json
{
  "success": true,
  "results": [
    {
      "title": "Latest AI Developments in 2024",
      "url": "https://example.com/ai-news",
      "snippet": "Recent breakthroughs in artificial intelligence...",
      "source": "bing"
    }
  ],
  "query": "AI developments 2024",
  "count": 4,
  "keyword_extraction_used": true,
  "optimized_queries": [
    "AI developments 2024",
    "artificial intelligence news"
  ],
  "successful_query": "AI developments 2024"
}
```

**Error Response - Inadequate Keywords (400):**
```json
{
  "success": false,
  "error": "Cannot perform web search: no adequate keywords found",
  "results": []
}
```

---

### Extract Keywords

**Endpoint:** `POST /api/search/extract-keywords`

**Description:** Extract and validate keywords from text

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "text": "string"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "original_text": "I need help with machine learning algorithms",
  "keywords": [
    "machine learning",
    "algorithms"
  ],
  "queries": [
    "machine learning algorithms"
  ],
  "method": "tfidf_enhanced",
  "adequate_keywords": true,
  "extraction_results": {
    "tfidf": ["machine", "learning", "algorithms"],
    "rules": ["machine learning"],
    "combined": ["machine learning", "algorithms"]
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/search/extract-keywords \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I need help with machine learning algorithms"
  }'
```

---

### Search Status

**Endpoint:** `GET /api/search/status`

**Description:** Get web search capabilities and configuration

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "enabled": true,
  "keyword_extraction_enabled": true,
  "extraction_methods": [
    "tfidf",
    "rules",
    "llm"
  ],
  "max_keywords": 10,
  "search_history_count": 25,
  "capabilities": {
    "selenium_available": true,
    "chrome_available": true
  }
}
```

---

### Enable Keyword Extraction

**Endpoint:** `POST /api/search/keyword-extraction/enable`

**Description:** Enable keyword extraction for web searches

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "success": true,
  "message": "Keyword extraction enabled",
  "enabled": true
}
```

---

### Disable Keyword Extraction

**Endpoint:** `POST /api/search/keyword-extraction/disable`

**Description:** Disable keyword extraction for web searches

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "success": true,
  "message": "Keyword extraction disabled",
  "enabled": false
}
```

---

## System Management Endpoints

### Health Check

**Endpoint:** `GET /health`

**Description:** System health status (no authentication required)

**Success Response (200):**
```json
{
  "status": "healthy",
  "ollama_url": "http://localhost:11434",
  "model": "llama3.2",
  "web_search_enabled": true,
  "keyword_extraction_enabled": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Error Response (500):**
```json
{
  "status": "error",
  "error": "Ollama connection failed",
  "ollama_url": "http://localhost:11434",
  "model": "llama3.2"
}
```

---

### List Models

**Endpoint:** `GET /api/models`

**Description:** Get available Ollama models

**Success Response (200):**
```json
{
  "models": [
    "llama3.2",
    "codellama",
    "mistral"
  ]
}
```

---

### Get Configuration

**Endpoint:** `GET /api/config`

**Description:** Get current system configuration

**Success Response (200):**
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
    "max_results": 5
  }
}
```

---

### Update Configuration

**Endpoint:** `POST /api/config`

**Description:** Update runtime configuration (admin only)

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "model": "string (optional)",
  "host": "string (optional)",
  "timeout": 30000
}
```

**Success Response (200):**
```json
{
  "message": "Configuration updated successfully"
}
```

---

## RAG System Endpoints

### RAG Statistics

**Endpoint:** `GET /api/rag/stats`

**Description:** Get RAG system statistics and status

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "stats": {
    "document_count": 1250,
    "collection_exists": true,
    "total_chunks": 8500,
    "last_updated": "2024-01-15T09:15:00Z"
  }
}
```

---

## File Management Endpoints

### Upload File

**Endpoint:** `POST /api/files/upload`

**Description:** Upload file for analysis

**Headers:** `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`

**Request Body:** Form data with `file` field

**Success Response (200):**
```json
{
  "message": "File uploaded successfully",
  "file_id": "abc123",
  "filename": "document.pdf",
  "size": 245760
}
```

---

### List Files

**Endpoint:** `GET /api/files`

**Description:** List user's uploaded files

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "files": [
    {
      "file_id": "abc123",
      "filename": "document.pdf",
      "upload_date": "2024-01-15T10:00:00Z",
      "size": 245760
    }
  ]
}
```

---

### Analyze File

**Endpoint:** `POST /api/files/{file_id}/read`

**Description:** Analyze specific uploaded file

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string (optional)"
}
```

**Success Response (200):**
```json
{
  "response": "string",
  "session_id": "string",
  "file_info": {
    "filename": "document.pdf",
    "size": 245760
  }
}
```

---

### Delete File

**Endpoint:** `DELETE /api/files/{file_id}`

**Description:** Delete uploaded file

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "message": "File deleted successfully"
}
```

---

## Conversation Management

### List Conversations

**Endpoint:** `GET /api/conversations`

**Description:** List user's conversation sessions

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "sessions": [
    {
      "session_id": "sess_123",
      "created_at": "2024-01-15T10:00:00Z",
      "message_count": 15,
      "last_message": "Thank you for the explanation"
    }
  ]
}
```

---

### Get Conversation History

**Endpoint:** `GET /api/conversations/{session_id}/history`

**Description:** Get full conversation history

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "history": [
    {
      "role": "user",
      "content": "Hello, how are you?",
      "timestamp": "2024-01-15T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "I'm doing well, thank you!",
      "timestamp": "2024-01-15T10:00:05Z"
    }
  ]
}
```

---

### Delete Conversation

**Endpoint:** `DELETE /api/conversations/{session_id}`

**Description:** Delete conversation session

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "message": "Session deleted successfully"
}
```

---

## Admin Endpoints

### List All Users

**Endpoint:** `GET /api/admin/users`

**Description:** List all users (admin only)

**Headers:** `Authorization: Bearer <admin_token>`

**Success Response (200):**
```json
{
  "users": [
    {
      "username": "admin",
      "email": "admin@company.com",
      "role": "admin",
      "display_name": "Administrator",
      "created_at": "2024-01-01T00:00:00Z",
      "is_active": true
    }
  ]
}
```

---

### Create User

**Endpoint:** `POST /api/admin/users`

**Description:** Create new user (admin only)

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "email": "string",
  "role": "user",
  "display_name": "string"
}
```

**Success Response (201):**
```json
{
  "message": "User created successfully",
  "user": {
    "username": "newuser",
    "email": "user@company.com",
    "role": "user"
  }
}
```

---

### Reset User Password

**Endpoint:** `POST /api/admin/users/{username}/reset-password`

**Description:** Reset user password (admin only)

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "new_password": "string"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

---

## Error Responses

### Standard Error Format
All error responses follow this format:

```json
{
  "error": "Error description",
  "details": "Additional error details (optional)"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| **200** | Success |
| **201** | Created |
| **400** | Bad Request (invalid parameters) |
| **401** | Unauthorized (authentication required) |
| **403** | Forbidden (insufficient permissions) |
| **404** | Not Found |
| **500** | Internal Server Error |

### Common Error Examples

**Authentication Required (401):**
```json
{
  "error": "Authentication required"
}
```

**Invalid Session (401):**
```json
{
  "error": "Invalid or expired session"
}
```

**Admin Access Required (403):**
```json
{
  "error": "Admin access required"
}
```

**Web Search Disabled (403):**
```json
{
  "error": "Web search is disabled"
}
```

**Inadequate Keywords (400):**
```json
{
  "error": "Cannot perform web search: no adequate keywords found. Query too generic or lacks searchable terms.",
  "search_failed": true
}
```

---

## Complete Usage Examples

### JavaScript Authentication Flow

```javascript
// 1. Login and get token
const loginResponse = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
    })
});

const {session_token} = await loginResponse.json();

// 2. Set headers for authenticated requests
const headers = {
    'Authorization': `Bearer ${session_token}`,
    'Content-Type': 'application/json'
};

// 3. Normal chat
const chatResponse = await fetch('/api/chat', {
    method: 'POST',
    headers,
    body: JSON.stringify({
        message: 'Hello, how are you?'
    })
});

const chatResult = await chatResponse.json();
console.log('Response:', chatResult.response);
console.log('Processing time:', chatResult.processing_time, 'ms');

// 4. RAG enhanced chat
const ragResponse = await fetch('/api/chat/rag', {
    method: 'POST',
    headers,
    body: JSON.stringify({
        message: 'What is our company policy?',
        max_results: 5
    })
});

const ragResult = await ragResponse.json();
console.log('RAG Response:', ragResult.response);
console.log('Search results used:', ragResult.search_results_count);

// 5. Web search chat
const searchResponse = await fetch('/api/chat/web-search', {
    method: 'POST',
    headers,
    body: JSON.stringify({
        message: 'Latest AI developments 2024'
    })
});

const searchResult = await searchResponse.json();
if (searchResult.search_failed) {
    console.log('Search failed:', searchResult.error);
} else {
    console.log('Search Response:', searchResult.response);
    console.log('Keywords used:', searchResult.keyword_extraction_used);
}
```

### cURL Testing Examples

```bash
# Set variables
BASE_URL="http://localhost:8000"
TOKEN=""

# 1. Login
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.session_token')
echo "Token: $TOKEN"

# 2. Health check (no auth required)
curl -s $BASE_URL/health | jq '.'

# 3. Normal chat
curl -s -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing"
  }' | jq '.'

# 4. RAG chat
curl -s -X POST $BASE_URL/api/chat/rag \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Search knowledge base for policy information",
    "max_results": 5
  }' | jq '.'

# 5. Web search chat
curl -s -X POST $BASE_URL/api/chat/web-search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Latest developments in artificial intelligence 2024"
  }' | jq '.'

# 6. Test keyword extraction
curl -s -X POST $BASE_URL/api/search/extract-keywords \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "machine learning algorithms optimization"
  }' | jq '.'

# 7. Direct web search
curl -s -X POST $BASE_URL/api/search/web \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "python programming tutorial",
    "max_results": 3
  }' | jq '.'

# 8. Get search status
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/api/search/status | jq '.'

# 9. Get system configuration
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/api/config | jq '.'

# 10. List available models
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/api/models | jq '.'

# 11. Get RAG statistics
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/api/rag/stats | jq '.'

# 12. Logout
curl -s -X POST $BASE_URL/api/auth/logout \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

This comprehensive API documentation provides all the information needed to integrate with the HE Team LLM Assistant system. Each endpoint is thoroughly documented with examples, error handling, and usage patterns.
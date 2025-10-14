# HE Team LLM Assistant - API Documentation

**Version 1.2.1 | Last Updated: October 14, 2025**

This document provides comprehensive documentation for all REST API endpoints in the HE Team LLM Assistant system.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Chat Endpoints](#chat-endpoints)
- [Search Endpoints](#search-endpoints)
- [Conversation Management](#conversation-management)
- [Model Configuration](#model-configuration)
- [System Endpoints](#system-endpoints)
- [RAG Endpoints](#rag-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)

---

## Overview

**Base URL**: `http://localhost:8000` (configurable in `config/config.json`)

**Authentication**: Bearer token-based authentication (except `/health` and `/api/auth/login`)

**Content Type**: `application/json` (unless specified otherwise)

**Response Format**: All responses return JSON

---

## Authentication

### Common Headers

All authenticated endpoints require:

```http
Authorization: Bearer <session_token>
Content-Type: application/json
```

### Session Management

- **Token Expiration**: 24 hours
- **Token Generation**: Upon successful login
- **Token Invalidation**: Upon logout or expiration

---

## 🔐 Authentication Endpoints

### Login

Authenticate user and obtain session token.

**Endpoint**: `POST /api/auth/login`

**Authentication**: Not required

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response (200)**:
```json
{
  "message": "Login successful",
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "user_123",
    "username": "admin",
    "role": "admin",
    "display_name": "Administrator",
    "email": "admin@company.com"
  }
}
```

**Error Responses**:
- `400`: Missing username or password
- `401`: Invalid credentials
- `500`: Server error

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

---

### Logout

Terminate current session and invalidate token.

**Endpoint**: `POST /api/auth/logout`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "message": "Logout successful"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <token>"
```

---

### Get Current User

Retrieve authenticated user information.

**Endpoint**: `GET /api/auth/me`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "user": {
    "user_id": "user_123",
    "username": "admin",
    "email": "admin@company.com",
    "role": "admin",
    "display_name": "Administrator",
    "created_at": "2025-01-01T00:00:00Z",
    "is_active": true
  }
}
```

---

### Change Password

Change current user's password.

**Endpoint**: `POST /api/auth/change-password`

**Authentication**: Required

**Request Body**:
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**Success Response (200)**:
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses**:
- `400`: Missing or invalid password (minimum 4 characters)
- `401`: Invalid old password
- `500`: Server error

---

## 💬 Chat Endpoints

### Normal Chat

Standard AI conversation without additional context.

**Endpoint**: `POST /api/chat`

**Authentication**: Required

**Request Body**:
```json
{
  "message": "string",
  "session_id": "string (optional)"
}
```

**Success Response (200)**:
```json
{
  "response": "AI generated response text...",
  "session_id": "session_abc123",
  "processing_time": 1250.5,
  "tokens_per_second": 24.8,
  "chat_type": "normal"
}
```

**Conversation Continuity**:
- If `session_id` is provided: continues existing conversation with full context
- If `session_id` is omitted: creates new conversation
- Response includes `session_id` for subsequent messages

**Example**:
```bash
# Start new conversation
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'

# Continue conversation
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about that",
    "session_id": "session_abc123"
  }'
```

---

### RAG Enhanced Chat

Chat with knowledge base search integration.

**Endpoint**: `POST /api/chat/rag`

**Authentication**: Required

**Request Body**:
```json
{
  "message": "string",
  "session_id": "string (optional)",
  "max_results": 5
}
```

**Success Response (200)**:
```json
{
  "response": "AI response using knowledge base context...",
  "session_id": "session_abc123",
  "processing_time": 1450.2,
  "tokens_per_second": 22.1,
  "rag_context_used": true,
  "search_results_count": 3,
  "chat_type": "rag"
}
```

**How It Works**:
1. Searches knowledge base for relevant documents
2. Injects top results into LLM context
3. Generates response using both conversation history and knowledge base

**Example**:
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

Chat with live web search integration.

**Endpoint**: `POST /api/chat/web-search`

**Authentication**: Required

**Request Body**:
```json
{
  "message": "string",
  "session_id": "string (optional)",
  "max_results": 5
}
```

**Success Response (200)**:
```json
{
  "response": "AI response using web search results...",
  "session_id": "session_abc123",
  "processing_time": 2100.8,
  "tokens_per_second": 20.5,
  "search_processing_time": 850.3,
  "search_context_used": true,
  "search_results_count": 4,
  "search_results": [
    {
      "title": "Latest AI Developments 2024",
      "url": "https://example.com/ai-news",
      "snippet": "Recent breakthroughs in artificial intelligence...",
      "source": "Bing"
    }
  ],
  "keyword_extraction_used": true,
  "optimized_queries": ["AI developments 2024"],
  "successful_query": "AI developments 2024",
  "chat_type": "web_search"
}
```

**Features**:
- **Keyword Extraction**: Automatically extracts optimal search keywords (if enabled)
- **Live Search**: Performs real-time web search using Selenium
- **Source Attribution**: Returns full search results with URLs
- **Query Optimization**: Can generate multiple optimized queries (if `query_expansion` enabled)

**Configuration**:
- Enable/disable in `config/config.json` → `web_search.enabled`
- Keyword extraction: `web_search.use_keyword_extraction`
- Query expansion: `web_search.keyword_extraction.query_expansion` (default: `false`)

**Error Response - Inadequate Keywords (400)**:
```json
{
  "error": "Cannot perform web search: no adequate keywords found. Query too generic or lacks searchable terms.",
  "search_failed": true
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/chat/web-search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Latest developments in artificial intelligence 2024",
    "max_results": 5
  }'
```

**Recent Changes (v1.2.1)**:
- ✅ **Added `search_results`** to response - no longer requires separate API call
- ✅ **Disabled `query_expansion`** by default - searches once instead of 2-3 times
- ✅ **Single search execution** - eliminated duplicate searches

---

## 🔍 Search Endpoints

### Direct Web Search

Perform web search without chat context (returns raw results).

**Endpoint**: `POST /api/search/web`

**Authentication**: Required

**Request Body**:
```json
{
  "query": "string",
  "max_results": 5
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "results": [
    {
      "title": "Latest AI Developments 2024",
      "url": "https://example.com/ai-news",
      "snippet": "Recent breakthroughs in artificial intelligence...",
      "source": "Bing"
    }
  ],
  "query": "AI developments 2024",
  "count": 4,
  "keyword_extraction_used": true,
  "optimized_queries": ["AI developments 2024"],
  "successful_query": "AI developments 2024",
  "error": null
}
```

**Error Response (400)**:
```json
{
  "success": false,
  "error": "Cannot perform web search: no adequate keywords found",
  "results": [],
  "query": "original query"
}
```

**Use Cases**:
- Direct search without LLM response
- Fetch search results for custom processing
- Testing search functionality

---

### Extract Keywords

Extract and validate keywords from text.

**Endpoint**: `POST /api/search/extract-keywords`

**Authentication**: Required

**Request Body**:
```json
{
  "text": "string"
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "original_text": "I need help with machine learning algorithms",
  "keywords": ["machine learning", "algorithms"],
  "queries": ["machine learning algorithms"],
  "method": "llm_assisted",
  "adequate_keywords": true,
  "extraction_results": {
    "tfidf": ["machine", "learning", "algorithms"],
    "rules": ["machine learning"],
    "llm": ["machine learning", "algorithms"],
    "combined": ["machine learning", "algorithms"]
  }
}
```

**Extraction Methods**:
- `rule_based`: Pattern matching for technical terms
- `tfidf`: TF-IDF statistical analysis
- `llm_assisted`: LLM-powered keyword extraction (most accurate)

**Configuration**:
- Enable LLM extraction: `config.json` → `web_search.keyword_extraction.use_llm: true`
- Extraction methods: `web_search.keyword_extraction.extraction_methods`

---

### Search Status

Get web search capabilities and configuration.

**Endpoint**: `GET /api/search/status`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "enabled": true,
  "keyword_extraction_enabled": true,
  "extraction_methods": ["rule_based", "tfidf", "llm_assisted"],
  "max_keywords": 4,
  "search_history_count": 25,
  "capabilities": {
    "success": true,
    "result_count": 3,
    "test_query": "python programming",
    "engines_working": ["Bing"],
    "sample_result": {
      "title": "Python Programming Tutorial",
      "url": "https://example.com",
      "source": "Bing"
    }
  }
}
```

---

### Enable Keyword Extraction

Enable keyword extraction for web searches.

**Endpoint**: `POST /api/search/keyword-extraction/enable`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Keyword extraction enabled",
  "enabled": true
}
```

---

### Disable Keyword Extraction

Disable keyword extraction for web searches.

**Endpoint**: `POST /api/search/keyword-extraction/disable`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Keyword extraction disabled",
  "enabled": false
}
```

---

## 💾 Conversation Management

### List Conversations

Get list of user's conversation sessions.

**Endpoint**: `GET /api/conversations`

**Authentication**: Required

**Query Parameters**:
- `limit` (optional): Maximum conversations to return (default: 50)

**Success Response (200)**:
```json
{
  "conversations": [
    {
      "id": "session_abc123",
      "title": "Python programming help discussion...",
      "created_at": "2025-01-08T10:30:00.123456",
      "last_activity": "2025-01-08T11:45:30.654321",
      "total_messages": 12,
      "user_id": "user_123"
    },
    {
      "id": "session_def456",
      "title": "Machine learning concepts...",
      "created_at": "2025-01-07T14:20:00.789012",
      "last_activity": "2025-01-07T15:30:45.345678",
      "total_messages": 8,
      "user_id": "user_123"
    }
  ]
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/conversations?limit=10" \
  -H "Authorization: Bearer <token>"
```

---

### Create New Conversation

Explicitly create a new conversation session.

**Endpoint**: `POST /api/conversations`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "session_id": "session_xyz789"
}
```

**Note**: Creating a session explicitly is optional. Chat endpoints auto-create sessions if no `session_id` is provided.

---

### Get Conversation

Get details about a specific conversation.

**Endpoint**: `GET /api/conversations/<session_id>`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "conversation": {
    "id": "session_abc123",
    "user_id": "user_123",
    "created_at": "2025-01-08T10:30:00.123456",
    "last_activity": "2025-01-08T11:45:30.654321",
    "messages": [...],
    "metadata": {
      "title": "Python programming help...",
      "total_messages": 12
    }
  }
}
```

**Error Responses**:
- `403`: Session access denied (belongs to different user)
- `404`: Session not found

---

### Get Conversation History

Get message history for a conversation.

**Endpoint**: `GET /api/conversations/<session_id>/history`

**Authentication**: Required

**Query Parameters**:
- `include_system` (optional): Include system messages (default: false)

**Success Response (200)**:
```json
{
  "history": [
    {
      "role": "user",
      "content": "Hello, can you help me with Python?",
      "timestamp": "2025-01-08T10:30:15.123456",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "I'd be happy to help you with Python programming!",
      "timestamp": "2025-01-08T10:30:18.654321",
      "metadata": {}
    }
  ],
  "session_id": "session_abc123"
}
```

---

### Delete Conversation

Delete a specific conversation.

**Endpoint**: `DELETE /api/conversations/<session_id>`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "message": "Session deleted successfully"
}
```

**Error Responses**:
- `403`: Session access denied
- `404`: Session not found

---

### Clear All Conversations

Delete all user's conversations.

**Endpoint**: `POST /api/conversations/clear`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "message": "Cleared 5 conversations",
  "deleted_count": 5
}
```

---

### Get Conversation Statistics

Get statistics about user's conversations.

**Endpoint**: `GET /api/conversations/stats`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "stats": {
    "total_sessions": 5,
    "total_messages": 47,
    "max_context_length": 8192,
    "session_timeout_hours": 24
  }
}
```

---

## ⚙️ Model Configuration

### List Available Models

Get list of all models available in Ollama.

**Endpoint**: `GET /api/models/available`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "models": [
    {
      "name": "gemma3:12b",
      "size": 6738374762,
      "modified_at": "2025-01-08T10:30:00Z",
      "digest": "sha256:abc123...",
      "details": {
        "format": "gguf",
        "family": "gemma3",
        "parameter_size": "12B"
      }
    },
    {
      "name": "llama3.2:latest",
      "size": 2648374762,
      "modified_at": "2025-01-07T15:20:00Z",
      "digest": "sha256:def456...",
      "details": {
        "format": "gguf",
        "family": "llama",
        "parameter_size": "3B"
      }
    }
  ],
  "total_count": 2,
  "ollama_url": "http://localhost:11434"
}
```

**Error Response (500)**:
```json
{
  "error": "Cannot connect to Ollama at http://localhost:11434: Connection refused",
  "models": [],
  "ollama_url": "http://localhost:11434"
}
```

---

### Get Current Model Configuration

Get current model configuration and parameters.

**Endpoint**: `GET /api/models/current`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "current_model": {
    "model": "gemma3:12b",
    "host": "http://localhost:11434",
    "timeout": 60000,
    "num_ctx": 8192,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40
  },
  "status": "active"
}
```

---

### Configure Model Parameters

Dynamically configure model parameters (runtime only, doesn't save to config file).

**Endpoint**: `POST /api/models/configure`

**Authentication**: Required

**Request Body**:
```json
{
  "model": "llama3.2:latest",
  "temperature": 0.8,
  "top_p": 0.9,
  "top_k": 40,
  "num_ctx": 4096,
  "timeout": 30000
}
```

**All Parameters (all optional)**:
- `model` (string): Model name (must exist in Ollama)
- `temperature` (float): 0.0-1.0 (creativity level)
- `top_p` (float): 0.0-1.0 (nucleus sampling)
- `top_k` (integer): 1-100 (top-k sampling)
- `num_ctx` (integer): 512-32768 (context window size)
- `timeout` (integer): 1000-300000 (request timeout in milliseconds)
- `host` (string): Ollama host URL

**Success Response (200)**:
```json
{
  "message": "Model configuration updated successfully",
  "changes": [
    "model: llama3.2:latest",
    "temperature: 0.8",
    "context: 4096"
  ],
  "new_config": {
    "model": "llama3.2:latest",
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 40,
    "num_ctx": 4096
  }
}
```

**Error Responses**:
- `400`: Invalid parameters (out of range, wrong type)
- `404`: Model not found in Ollama
- `500`: Failed to reinitialize client

**Example**:
```bash
curl -X POST http://localhost:8000/api/models/configure \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:latest",
    "temperature": 0.8,
    "num_ctx": 8192
  }'
```

---

### Test Model Configuration

Test current model with a sample message.

**Endpoint**: `POST /api/models/test`

**Authentication**: Required

**Request Body**:
```json
{
  "message": "Hello, this is a test message"
}
```

**Success Response (200)**:
```json
{
  "test_successful": true,
  "model": "gemma3:12b",
  "test_message": "Hello, this is a test message",
  "response": "Hello! I'm working correctly. How can I assist you today?",
  "processing_time_ms": 1250.5,
  "tokens_per_second": 24.8,
  "response_length": 145
}
```

**Error Response (500)**:
```json
{
  "test_successful": false,
  "model": "gemma3:12b",
  "test_message": "Hello, this is a test message",
  "error": "Connection timeout",
  "error_type": "TimeoutError"
}
```

---

### Get Model Presets

Get predefined model configuration presets.

**Endpoint**: `GET /api/models/presets`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "presets": {
    "creative": {
      "name": "Creative",
      "description": "High creativity for creative writing and brainstorming",
      "temperature": 0.9,
      "top_p": 0.9,
      "top_k": 40,
      "num_ctx": 4096
    },
    "balanced": {
      "name": "Balanced",
      "description": "Balanced settings for general use",
      "temperature": 0.7,
      "top_p": 0.9,
      "top_k": 40,
      "num_ctx": 4096
    },
    "precise": {
      "name": "Precise",
      "description": "Low creativity for factual and analytical tasks",
      "temperature": 0.3,
      "top_p": 0.7,
      "top_k": 20,
      "num_ctx": 4096
    },
    "coding": {
      "name": "Coding",
      "description": "Optimized for code generation and programming",
      "temperature": 0.2,
      "top_p": 0.8,
      "top_k": 30,
      "num_ctx": 8192
    },
    "research": {
      "name": "Research",
      "description": "Large context for research and document analysis",
      "temperature": 0.4,
      "top_p": 0.8,
      "top_k": 25,
      "num_ctx": 8192
    }
  },
  "total_count": 5
}
```

---

### Apply Model Preset

Apply a predefined configuration preset.

**Endpoint**: `POST /api/models/preset/<preset_name>`

**Authentication**: Required

**Path Parameters**:
- `preset_name`: One of: `creative`, `balanced`, `precise`, `coding`, `research`

**Success Response (200)**:
```json
{
  "message": "Model configuration updated successfully",
  "changes": [
    "temperature: 0.2",
    "top_p: 0.8",
    "top_k: 30",
    "context: 8192"
  ],
  "preset_applied": "coding",
  "preset_description": "Optimized for code generation and programming",
  "new_config": {
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 30,
    "num_ctx": 8192
  }
}
```

**Error Response (400)**:
```json
{
  "error": "Preset 'invalid' not found",
  "available_presets": ["creative", "balanced", "precise", "coding", "research"]
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/models/preset/coding \
  -H "Authorization: Bearer <token>"
```

---

## 🖥️ System Endpoints

### Health Check

System health status (no authentication required).

**Endpoint**: `GET /health`

**Authentication**: Not required

**Success Response (200)**:
```json
{
  "status": "healthy",
  "ollama_url": "http://localhost:11434",
  "model": "gemma3:12b",
  "web_search_enabled": true,
  "keyword_extraction_enabled": true,
  "timestamp": null
}
```

**Error Response (500)**:
```json
{
  "status": "ollama_unreachable",
  "error": "Connection refused",
  "ollama_url": "http://localhost:11434",
  "model": "gemma3:12b"
}
```

**Use Cases**:
- Monitor system availability
- Check Ollama connection status
- Verify feature availability

---

### List Models

Get available Ollama models (simple list).

**Endpoint**: `GET /api/models`

**Authentication**: Not required

**Success Response (200)**:
```json
{
  "models": [
    "gemma3:12b",
    "llama3.2:latest",
    "codellama:latest",
    "mistral:latest"
  ]
}
```

---

### Get Configuration

Get current system configuration.

**Endpoint**: `GET /api/config`

**Authentication**: Not required

**Success Response (200)**:
```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "model": "gemma3:12b",
    "timeout": 60000,
    "num_ctx": 8192,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40
  },
  "server": {
    "port": 8000,
    "host": "0.0.0.0"
  },
  "web_search": {
    "enabled": true,
    "search_engine": "bing",
    "use_keyword_extraction": true,
    "max_results": 5,
    "timeout": 100,
    "keyword_extraction": {
      "enabled": true,
      "use_llm": true,
      "query_expansion": false,
      "max_keywords": 4
    }
  },
  "rag": {
    "collection": {
      "name": "documents",
      "persist_directory": "./data/chroma_db"
    },
    "search": {
      "default_results": 5,
      "max_results": 20
    }
  }
}
```

---

### Update Configuration

Update system configuration (runtime only).

**Endpoint**: `POST /api/config`

**Authentication**: Required

**Request Body**:
```json
{
  "model": "llama3.2:latest",
  "host": "http://localhost:11434",
  "timeout": 30000
}
```

**Success Response (200)**:
```json
{
  "message": "Configuration updated successfully"
}
```

**Note**: This updates runtime configuration only. To persist changes, edit `config/config.json`.

---

## 📚 RAG Endpoints

### RAG Statistics

Get RAG system statistics and status.

**Endpoint**: `GET /api/rag/stats`

**Authentication**: Required

**Success Response (200)**:
```json
{
  "stats": {
    "total_documents": 1250,
    "total_chunks": 8500,
    "collection_exists": true,
    "collection_name": "documents",
    "embedding_model": "nomic-embed-text:latest",
    "embedding_dimensions": 768,
    "last_updated": "2025-01-08T09:15:00Z"
  }
}
```

---

## 👥 Admin Endpoints

All admin endpoints require admin role.

### List All Users

Get list of all users (admin only).

**Endpoint**: `GET /api/admin/users`

**Authentication**: Required (admin role)

**Success Response (200)**:
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
    },
    {
      "username": "user1",
      "email": "user1@company.com",
      "role": "user",
      "display_name": "User One",
      "created_at": "2024-01-15T10:30:00Z",
      "is_active": true
    }
  ]
}
```

**Error Response (403)**:
```json
{
  "error": "Admin privileges required"
}
```

---

### Create User

Create new user (admin only).

**Endpoint**: `POST /api/admin/users`

**Authentication**: Required (admin role)

**Request Body**:
```json
{
  "username": "newuser",
  "password": "securepassword123",
  "email": "newuser@company.com",
  "role": "user",
  "display_name": "New User"
}
```

**Success Response (200)**:
```json
{
  "message": "User newuser created successfully"
}
```

**Error Responses**:
- `400`: Missing required fields, weak password, invalid role
- `409`: Username or email already exists

**Password Requirements**:
- Minimum 6 characters
- No complexity requirements (for testing; increase in production)

---

### Reset User Password

Reset user's password (admin only).

**Endpoint**: `POST /api/admin/users/<username>/reset-password`

**Authentication**: Required (admin role)

**Request Body**:
```json
{
  "new_password": "newpassword123"
}
```

**Success Response (200)**:
```json
{
  "message": "Password reset for user newuser"
}
```

**Error Responses**:
- `400`: Password too short (minimum 6 characters)
- `404`: User not found

---

## ❌ Error Handling

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
| **401** | Unauthorized (authentication required or failed) |
| **403** | Forbidden (insufficient permissions or feature disabled) |
| **404** | Not Found |
| **409** | Conflict (resource already exists) |
| **500** | Internal Server Error |
| **503** | Service Unavailable (feature not enabled) |

### Common Error Examples

**Authentication Required (401)**:
```json
{
  "error": "Authentication required"
}
```

**Invalid Session (401)**:
```json
{
  "error": "Invalid or expired session"
}
```

**Admin Access Required (403)**:
```json
{
  "error": "Admin privileges required"
}
```

**Web Search Disabled (403)**:
```json
{
  "error": "Web search is disabled"
}
```

**Session Access Denied (403)**:
```json
{
  "error": "Session not found or access denied"
}
```

**Inadequate Search Keywords (400)**:
```json
{
  "error": "Cannot perform web search: no adequate keywords found. Query too generic or lacks searchable terms.",
  "search_failed": true
}
```

**Model Not Found (404)**:
```json
{
  "error": "Model 'invalid-model' not found in Ollama",
  "available_models": ["gemma3:12b", "llama3.2:latest"]
}
```

**Invalid Parameters (400)**:
```json
{
  "error": "Temperature must be between 0.0 and 1.0"
}
```

---

## 📝 Code Examples

### JavaScript - Complete Chat Flow

```javascript
// 1. Login
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});

const { session_token } = await loginResponse.json();

// Set headers for authenticated requests
const headers = {
  'Authorization': `Bearer ${session_token}`,
  'Content-Type': 'application/json'
};

// 2. Start a conversation
const chatResponse = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    message: 'Hello, can you help me with Python programming?'
  })
});

const chatResult = await chatResponse.json();
console.log('Response:', chatResult.response);
console.log('Session ID:', chatResult.session_id);

// 3. Continue conversation
const continueResponse = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    message: 'How do I create a class in Python?',
    session_id: chatResult.session_id
  })
});

const continueResult = await continueResponse.json();
console.log('Response:', continueResult.response);

// 4. RAG chat with knowledge base
const ragResponse = await fetch('http://localhost:8000/api/chat/rag', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    message: 'What does our documentation say about Python best practices?',
    session_id: chatResult.session_id,
    max_results: 5
  })
});

const ragResult = await ragResponse.json();
console.log('RAG Response:', ragResult.response);
console.log('Results used:', ragResult.search_results_count);

// 5. Web search chat
const searchResponse = await fetch('http://localhost:8000/api/chat/web-search', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    message: 'Latest AI developments in 2024',
    max_results: 5
  })
});

const searchResult = await searchResponse.json();
if (searchResult.search_failed) {
  console.log('Search failed:', searchResult.error);
} else {
  console.log('Search Response:', searchResult.response);
  console.log('Keywords used:', searchResult.keyword_extraction_used);
  console.log('Search results:', searchResult.search_results);
}

// 6. Get conversation history
const historyResponse = await fetch(
  `http://localhost:8000/api/conversations/${chatResult.session_id}/history`,
  { headers }
);

const history = await historyResponse.json();
console.log('Conversation history:', history.history);

// 7. Logout
await fetch('http://localhost:8000/api/auth/logout', {
  method: 'POST',
  headers
});
```

---

### Python - Conversation Management

```python
import requests
import json

class LLMAssistantClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_token = None
        self.headers = {"Content-Type": "application/json"}
    
    def login(self, username, password):
        """Login and get session token"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            headers=self.headers,
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.session_token = data["session_token"]
            self.headers["Authorization"] = f"Bearer {self.session_token}"
            print(f"✓ Logged in as {data['user']['username']}")
            return True
        else:
            print(f"✗ Login failed: {response.json().get('error')}")
            return False
    
    def chat(self, message, session_id=None, chat_type="normal", max_results=5):
        """Send chat message with optional conversation resumption"""
        endpoint_map = {
            "normal": "/api/chat",
            "rag": "/api/chat/rag",
            "web-search": "/api/chat/web-search"
        }
        
        endpoint = endpoint_map.get(chat_type, "/api/chat")
        payload = {"message": message}
        
        if session_id:
            payload["session_id"] = session_id
        
        if chat_type in ["rag", "web-search"]:
            payload["max_results"] = max_results
            
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Chat failed: {response.json().get('error')}")
            return None
    
    def list_conversations(self, limit=10):
        """Get list of conversations"""
        response = requests.get(
            f"{self.base_url}/api/conversations?limit={limit}",
            headers=self.headers
        )
        return response.json() if response.status_code == 200 else None
    
    def get_conversation_history(self, session_id, include_system=False):
        """Get conversation history"""
        response = requests.get(
            f"{self.base_url}/api/conversations/{session_id}/history?include_system={str(include_system).lower()}",
            headers=self.headers
        )
        return response.json() if response.status_code == 200 else None
    
    def configure_model(self, **params):
        """Configure model parameters"""
        response = requests.post(
            f"{self.base_url}/api/models/configure",
            headers=self.headers,
            json=params
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Configuration updated: {', '.join(data['changes'])}")
            return data
        else:
            print(f"✗ Configuration failed: {response.json().get('error')}")
            return None
    
    def apply_preset(self, preset_name):
        """Apply a model preset"""
        response = requests.post(
            f"{self.base_url}/api/models/preset/{preset_name}",
            headers=self.headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Applied preset '{preset_name}': {data['preset_description']}")
            return data
        else:
            print(f"✗ Failed to apply preset: {response.json().get('error')}")
            return None

# Example usage
client = LLMAssistantClient()

# Login
if client.login("admin", "admin123"):
    
    # Start conversation
    result = client.chat("Hello, can you help me with Python programming?")
    if result:
        session_id = result["session_id"]
        print(f"Assistant: {result['response']}")
        
        # Continue conversation
        result = client.chat(
            "How do I create a class in Python?",
            session_id=session_id
        )
        if result:
            print(f"Assistant: {result['response']}")
        
        # Use RAG in same conversation
        result = client.chat(
            "What does our documentation say about Python best practices?",
            session_id=session_id,
            chat_type="rag",
            max_results=3
        )
        if result:
            print(f"RAG Response: {result['response']}")
            print(f"Results used: {result.get('search_results_count', 0)}")
        
        # Web search in new conversation
        result = client.chat(
            "Latest AI developments in 2024",
            chat_type="web-search",
            max_results=5
        )
        if result and not result.get('search_failed'):
            print(f"Search Response: {result['response']}")
            print(f"Search results: {len(result.get('search_results', []))}")
        
        # Get conversation history
        history = client.get_conversation_history(session_id)
        if history:
            print(f"\nConversation has {len(history['history'])} messages")
        
        # Configure model for coding
        client.apply_preset("coding")
        
        # Continue with coding-optimized model
        result = client.chat(
            "Write a Python function to sort a list",
            session_id=session_id
        )
        if result:
            print(f"Coding Response: {result['response']}")
```

---

### cURL - Testing Examples

```bash
# Set variables
BASE_URL="http://localhost:8000"
TOKEN=""

# 1. Login
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.session_token')
echo "Token: $TOKEN"

# 2. Health check
curl -s $BASE_URL/health | jq '.'

# 3. Start conversation
CHAT_RESPONSE=$(curl -s -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}')

SESSION_ID=$(echo $CHAT_RESPONSE | jq -r '.session_id')
echo "Session ID: $SESSION_ID"
echo $CHAT_RESPONSE | jq '.response'

# 4. Continue conversation
curl -s -X POST $BASE_URL/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Tell me more about that\", \"session_id\": \"$SESSION_ID\"}" \
  | jq '.response'

# 5. RAG chat
curl -s -X POST $BASE_URL/api/chat/rag \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Search knowledge base for policy", "max_results": 5}' \
  | jq '.'

# 6. Web search chat
curl -s -X POST $BASE_URL/api/chat/web-search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Latest AI developments 2024", "max_results": 5}' \
  | jq '.search_results'

# 7. Direct web search
curl -s -X POST $BASE_URL/api/search/web \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "python programming tutorial", "max_results": 3}' \
  | jq '.results'

# 8. Extract keywords
curl -s -X POST $BASE_URL/api/search/extract-keywords \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "machine learning algorithms optimization"}' \
  | jq '.'

# 9. Get conversation history
curl -s -X GET "$BASE_URL/api/conversations/$SESSION_ID/history" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.history'

# 10. List conversations
curl -s -X GET "$BASE_URL/api/conversations?limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.conversations'

# 11. Configure model
curl -s -X POST $BASE_URL/api/models/configure \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.8, "num_ctx": 8192}' \
  | jq '.'

# 12. Apply preset
curl -s -X POST $BASE_URL/api/models/preset/coding \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# 13. Test model
curl -s -X POST $BASE_URL/api/models/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test the model"}' \
  | jq '.'

# 14. Get available models
curl -s -X GET $BASE_URL/api/models/available \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.models[].name'

# 15. Search status
curl -s -X GET $BASE_URL/api/search/status \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# 16. RAG stats
curl -s -X GET $BASE_URL/api/rag/stats \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.stats'

# 17. System config
curl -s -X GET $BASE_URL/api/config | jq '.'

# 18. Logout
curl -s -X POST $BASE_URL/api/auth/logout \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

---

## 📌 Version History

### v1.2.1 (October 14, 2025)
**Major Updates**:
- ✅ Fixed web search double execution issue
  - Added `search_results` to `/api/chat/web-search` response
  - Eliminated duplicate API calls from frontend
  - Disabled `query_expansion` by default
- ⚡ Performance improvements:
  - Search executes only once (was 2-3 times before)
  - 2-3x faster search performance
  - Reduced browser overhead

**Configuration Changes**:
- `config/config.json` → `web_search.keyword_extraction.query_expansion: false`
- Removed unused `config/search_config.json`
- Disabled debug Chrome mode by default

---

## 🔗 Related Documentation

- **User Guide**: `README.md`
- **Configuration Guide**: `config/config.json` (with inline comments)
- **Development Guide**: `CLAUDE.md`
- **Search Configuration**: See `config/config.json` → `web_search` section

---

## ⚠️ Important Notes

### Authentication
- Tokens expire after 24 hours
- Use HTTPS in production environments
- Change default admin password immediately (`admin` / `admin123`)

### Web Search
- Requires Chrome/Chromium browser
- May encounter CAPTCHA with high request volumes
- Keyword extraction provides better search results
- Search results now included in chat response (no duplicate calls needed)

### Model Configuration
- Configuration changes are runtime only
- To persist changes, edit `config/config.json`
- Restart server for config file changes to take effect

### Rate Limiting
- No built-in rate limiting (implement at proxy/firewall level if needed)

### Data Privacy
- Users can only access their own conversations
- Admin users can see all users but not other users' conversations
- File uploads are user-isolated

---

## 📞 Support

For issues and questions:
1. Check the [Troubleshooting section in README.md](README.md#-troubleshooting)
2. Review system logs
3. Use `/health` endpoint to verify system status
4. Test with example code provided in this documentation

---

**Last Updated**: October 14, 2025  
**API Version**: 1.2.1  
**Documentation Version**: 1.2.1

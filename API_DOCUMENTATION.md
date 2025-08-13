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

## Conversation Management & Resumption

### Overview
The system supports full conversation resumption across all chat types. Each conversation has a unique `session_id` that preserves context and message history.

### How to Continue an Existing Conversation

#### Method 1: Include session_id in chat requests
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer your-session-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What did we discuss about machine learning earlier?",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

#### Method 2: List conversations first, then continue
```bash
# 1. Get your conversations
curl -X GET http://localhost:8000/api/conversations \
  -H "Authorization: Bearer your-session-token"

# 2. Use session_id from response to continue
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer your-session-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you elaborate on what we discussed?",
    "session_id": "session-id-from-step-1"
  }'
```

### List Conversations

**Endpoint:** `GET /api/conversations`

**Description:** List user's conversation sessions

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Maximum conversations to return (default: 50)

**Success Response (200):**
```json
{
  "conversations": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Python programming help...",
      "created_at": "2025-01-08T10:30:00.123456",
      "last_activity": "2025-01-08T11:45:30.654321", 
      "total_messages": 12,
      "user_id": "user123"
    },
    {
      "id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
      "title": "Machine learning discussion...",
      "created_at": "2025-01-07T14:20:00.789012",
      "last_activity": "2025-01-07T15:30:45.345678",
      "total_messages": 8,
      "user_id": "user123"
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/conversations?limit=10" \
  -H "Authorization: Bearer your-session-token"
```

---

### Create New Conversation

**Endpoint:** `POST /api/conversations`

**Description:** Explicitly create a new conversation session

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "session_id": "c3d4e5f6-g7h8-9012-cdef-g34567890123"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/conversations \
  -H "Authorization: Bearer your-session-token"
```

---

### Get Specific Conversation

**Endpoint:** `GET /api/conversations/<session_id>`

**Description:** Get details about a specific conversation

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "conversation": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_id": "user123",
    "created_at": "2025-01-08T10:30:00.123456",
    "last_activity": "2025-01-08T11:45:30.654321",
    "messages": [...],
    "metadata": {
      "title": "Python programming help...",
      "model": "llama3.2",
      "total_messages": 12
    }
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/api/conversations/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer your-session-token"
```

---

### Get Conversation History

**Endpoint:** `GET /api/conversations/<session_id>/history`

**Description:** Get message history for a conversation

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `include_system` (optional): Include system messages (default: false)

**Success Response (200):**
```json
{
  "history": [
    {
      "role": "user",
      "content": "Hello, can you help me with Python programming?",
      "timestamp": "2025-01-08T10:30:15.123456",
      "metadata": {}
    },
    {
      "role": "assistant", 
      "content": "I'd be happy to help you with Python programming! What specific topic would you like assistance with?",
      "timestamp": "2025-01-08T10:30:18.654321",
      "metadata": {}
    },
    {
      "role": "user",
      "content": "How do I create a class in Python?",
      "timestamp": "2025-01-08T10:31:05.789012", 
      "metadata": {}
    }
  ],
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/conversations/a1b2c3d4-e5f6-7890-abcd-ef1234567890/history?include_system=false" \
  -H "Authorization: Bearer your-session-token"
```

---

### Delete Conversation

**Endpoint:** `DELETE /api/conversations/<session_id>`

**Description:** Delete a specific conversation

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "message": "Session deleted successfully"
}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/conversations/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer your-session-token"
```

---

### Clear All Conversations

**Endpoint:** `POST /api/conversations/clear`

**Description:** Delete all user's conversations

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "message": "Cleared 5 conversations",
  "deleted_count": 5
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/conversations/clear \
  -H "Authorization: Bearer your-session-token"
```

---

### Get Conversation Statistics

**Endpoint:** `GET /api/conversations/stats`

**Description:** Get statistics about user's conversations

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
  "stats": {
    "total_sessions": 5,
    "total_messages": 47,
    "max_context_length": 4000,
    "session_timeout_hours": 24
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/api/conversations/stats \
  -H "Authorization: Bearer your-session-token"
```

---

### Conversation Resumption Examples

#### JavaScript Example
```javascript
// Get conversations
const conversationsResponse = await fetch('/api/conversations', {
  headers: { 'Authorization': 'Bearer your-session-token' }
});
const conversations = await conversationsResponse.json();

// Continue with the first conversation
const sessionId = conversations.conversations[0].id;

const chatResponse = await fetch('/api/chat', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-session-token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "Let's continue our previous discussion",
    session_id: sessionId
  })
});

const result = await chatResponse.json();
console.log(result.response);
```

#### Complete Chat Flow Example (Bash)
```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.session_token')

# 2. Start a conversation
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me with Python?"}' | jq -r '.session_id')

echo "Started conversation: $SESSION_ID"

# 3. Continue the conversation
curl -s -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Can you explain classes in Python?\", \"session_id\": \"$SESSION_ID\"}" | jq '.response'

# 4. Get conversation history
curl -s -X GET "http://localhost:8000/api/conversations/$SESSION_ID/history" \
  -H "Authorization: Bearer $TOKEN" | jq '.history'

# 5. Continue with RAG chat in same session
curl -s -X POST http://localhost:8000/api/chat/rag \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What does our documentation say about Python best practices?\", \"session_id\": \"$SESSION_ID\"}" | jq '.response'
```

#### Python Example Scripts

**Basic conversation resumption:**
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
    
    def chat(self, message, session_id=None, chat_type="normal"):
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
    
    def delete_conversation(self, session_id):
        """Delete a conversation"""
        response = requests.delete(
            f"{self.base_url}/api/conversations/{session_id}",
            headers=self.headers
        )
        return response.status_code == 200

# Example usage
def main():
    client = LLMAssistantClient()
    
    # 1. Login
    if not client.login("admin", "admin123"):
        return
    
    # 2. Start a new conversation
    print("\n--- Starting new conversation ---")
    result = client.chat("Hello, can you help me with Python programming?")
    if result:
        session_id = result["session_id"]
        print(f"Assistant: {result['response']}")
        print(f"Session ID: {session_id}")
    
    # 3. Continue the conversation
    print("\n--- Continuing conversation ---")
    result = client.chat("How do I create a class in Python?", session_id=session_id)
    if result:
        print(f"Assistant: {result['response']}")
    
    # 4. Try RAG chat in same session
    print("\n--- RAG chat in same session ---")
    result = client.chat("What does our documentation say about Python best practices?", 
                        session_id=session_id, chat_type="rag")
    if result:
        print(f"Assistant: {result['response']}")
        print(f"RAG results used: {result.get('search_results_count', 0)}")
    
    # 5. Get conversation history
    print("\n--- Conversation History ---")
    history = client.get_conversation_history(session_id)
    if history:
        for msg in history["history"]:
            role = msg["role"].capitalize()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"{role}: {content}")
    
    # 6. List all conversations
    print("\n--- All Conversations ---")
    conversations = client.list_conversations()
    if conversations:
        for conv in conversations["conversations"]:
            print(f"ID: {conv['id']}")
            print(f"Title: {conv['title']}")
            print(f"Messages: {conv['total_messages']}")
            print(f"Last activity: {conv['last_activity']}")
            print("---")

if __name__ == "__main__":
    main()
```

**Advanced conversation management:**
```python
import requests
import json
from datetime import datetime
from typing import Optional, List, Dict

class ConversationManager:
    def __init__(self, base_url="http://localhost:8000", username="admin", password="admin123"):
        self.base_url = base_url
        self.session_token = None
        self.headers = {"Content-Type": "application/json"}
        self.login(username, password)
    
    def login(self, username: str, password: str) -> bool:
        """Login and authenticate"""
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
    
    def create_conversation(self) -> Optional[str]:
        """Create a new conversation explicitly"""
        response = requests.post(
            f"{self.base_url}/api/conversations",
            headers=self.headers
        )
        return response.json().get("session_id") if response.status_code == 200 else None
    
    def send_message(self, message: str, session_id: Optional[str] = None, 
                    chat_type: str = "normal", max_results: int = 5) -> Dict:
        """Send message with full parameter support"""
        endpoint_map = {
            "normal": "/api/chat",
            "rag": "/api/chat/rag",
            "web-search": "/api/chat/web-search"
        }
        
        payload = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        if chat_type in ["rag", "web-search"]:
            payload["max_results"] = max_results
            
        response = requests.post(
            f"{self.base_url}{endpoint_map[chat_type]}",
            headers=self.headers,
            json=payload
        )
        
        return response.json() if response.status_code == 200 else {"error": response.text}
    
    def get_conversations(self, limit: int = 50) -> List[Dict]:
        """Get all conversations with metadata"""
        response = requests.get(
            f"{self.base_url}/api/conversations?limit={limit}",
            headers=self.headers
        )
        return response.json().get("conversations", []) if response.status_code == 200 else []
    
    def find_conversation_by_title(self, title_keyword: str) -> Optional[Dict]:
        """Find conversation by title keyword"""
        conversations = self.get_conversations()
        for conv in conversations:
            if title_keyword.lower() in conv["title"].lower():
                return conv
        return None
    
    def resume_conversation(self, session_id: str, message: str, chat_type: str = "normal") -> Dict:
        """Resume a conversation with context awareness"""
        # Get some recent history for context
        history = self.get_conversation_history(session_id, limit=3)
        
        if history:
            print("📖 Recent conversation context:")
            for msg in history["history"][-3:]:  # Last 3 messages
                role = "👤" if msg["role"] == "user" else "🤖"
                content = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
                print(f"   {role} {content}")
            print()
        
        return self.send_message(message, session_id, chat_type)
    
    def get_conversation_history(self, session_id: str, include_system: bool = False, 
                               limit: Optional[int] = None) -> Dict:
        """Get conversation history with optional limiting"""
        response = requests.get(
            f"{self.base_url}/api/conversations/{session_id}/history?include_system={str(include_system).lower()}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if limit:
                data["history"] = data["history"][-limit:]  # Get last N messages
            return data
        return {}
    
    def conversation_stats(self) -> Dict:
        """Get conversation statistics"""
        response = requests.get(
            f"{self.base_url}/api/conversations/stats",
            headers=self.headers
        )
        return response.json().get("stats", {}) if response.status_code == 200 else {}
    
    def interactive_conversation_picker(self) -> Optional[str]:
        """Interactive conversation picker"""
        conversations = self.get_conversations(limit=20)
        
        if not conversations:
            print("No existing conversations found.")
            return None
        
        print("\n📋 Your Recent Conversations:")
        print("-" * 80)
        
        for i, conv in enumerate(conversations[:10], 1):
            # Format date
            last_activity = datetime.fromisoformat(conv["last_activity"].replace('Z', '+00:00'))
            formatted_date = last_activity.strftime("%Y-%m-%d %H:%M")
            
            print(f"{i:2d}. {conv['title'][:50]:<50}")
            print(f"     💬 {conv['total_messages']} messages | 🕐 {formatted_date}")
            print(f"     🆔 {conv['id']}")
            print()
        
        try:
            choice = input("Enter conversation number to resume (or press Enter for new): ").strip()
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(conversations):
                    return conversations[idx]["id"]
        except (ValueError, KeyboardInterrupt):
            pass
        
        return None

# Advanced example usage
def advanced_example():
    """Demonstrate advanced conversation management"""
    manager = ConversationManager()
    
    print("🚀 Advanced Conversation Management Example")
    print("=" * 50)
    
    # Show stats
    stats = manager.conversation_stats()
    print(f"📊 You have {stats.get('total_sessions', 0)} conversations with {stats.get('total_messages', 0)} total messages")
    
    # Interactive conversation selection
    session_id = manager.interactive_conversation_picker()
    
    if session_id:
        print(f"\n✅ Resuming conversation: {session_id}")
        
        # Resume with context
        result = manager.resume_conversation(
            session_id, 
            "Let's continue where we left off. Can you summarize what we discussed?",
            chat_type="normal"
        )
        
        if "error" not in result:
            print(f"🤖 Assistant: {result['response']}")
            print(f"⚡ Processing time: {result.get('processing_time', 0)}ms")
        
    else:
        print("\n✨ Starting new conversation")
        
        # Create new conversation
        session_id = manager.create_conversation()
        result = manager.send_message(
            "Hello! I'd like to learn about advanced Python concepts. Can you help?",
            session_id=session_id
        )
        
        if "error" not in result:
            print(f"🤖 Assistant: {result['response']}")
            print(f"🆔 New session ID: {session_id}")
    
    # Demonstrate multi-type chat in same session
    if session_id:
        print("\n🔍 Trying RAG search in same conversation...")
        rag_result = manager.send_message(
            "What does our documentation say about Python best practices?",
            session_id=session_id,
            chat_type="rag",
            max_results=3
        )
        
        if "error" not in rag_result:
            print(f"📚 RAG Response: {rag_result['response'][:200]}...")
            print(f"🔎 Used {rag_result.get('search_results_count', 0)} knowledge base results")

if __name__ == "__main__":
    # Run basic example
    print("Running basic example...")
    main()
    
    print("\n" + "="*60 + "\n")
    
    # Run advanced example
    print("Running advanced example...")
    advanced_example()
```

**Simple utility script:**
```python
#!/usr/bin/env python3
"""
Simple LLM Assistant conversation utility
Usage: python chat_client.py "Your message here" [session_id]
"""

import requests
import sys
import json
import os
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"  # Change as needed
PASSWORD = "admin123"  # Change as needed

def get_session_token() -> Optional[str]:
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    return response.json().get("session_token") if response.status_code == 200 else None

def send_chat(message: str, session_id: Optional[str] = None, chat_type: str = "normal") -> dict:
    """Send chat message"""
    token = get_session_token()
    if not token:
        return {"error": "Authentication failed"}
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    endpoint_map = {
        "normal": "/api/chat",
        "rag": "/api/chat/rag",
        "search": "/api/chat/web-search"
    }
    
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    
    response = requests.post(
        f"{BASE_URL}{endpoint_map[chat_type]}",
        headers=headers,
        json=payload
    )
    
    return response.json() if response.status_code == 200 else {"error": response.text}

def main():
    if len(sys.argv) < 2:
        print("Usage: python chat_client.py \"Your message\" [session_id] [chat_type]")
        print("Chat types: normal, rag, search")
        sys.exit(1)
    
    message = sys.argv[1]
    session_id = sys.argv[2] if len(sys.argv) > 2 else None
    chat_type = sys.argv[3] if len(sys.argv) > 3 else "normal"
    
    print(f"💭 Sending message: {message}")
    if session_id:
        print(f"🔄 Resuming session: {session_id}")
    
    result = send_chat(message, session_id, chat_type)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"\n🤖 Response:\n{result['response']}")
        print(f"\n📝 Session ID: {result.get('session_id')}")
        if result.get('processing_time'):
            print(f"⚡ Time: {result['processing_time']}ms")

if __name__ == "__main__":
    main()
```

### Key Features

- **Cross-Chat-Type Support**: Same session_id works with `/api/chat`, `/api/chat/rag`, and `/api/chat/web-search`
- **Automatic Context**: LLM sees full conversation history when resuming
- **User Isolation**: Users can only access their own conversations
- **Session Validation**: Invalid session_id returns 403 error
- **Auto-Creation**: Omitting session_id creates new conversation
- **24-Hour Timeout**: Sessions expire after 24 hours of inactivity
- **Context Trimming**: Long conversations are automatically trimmed to fit context limits

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
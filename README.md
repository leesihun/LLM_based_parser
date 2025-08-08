# HE Team LLM Assistant

A complete multi-user, offline-capable local LLM system using Ollama with secure authentication and per-user data storage.

## Features

- **🔐 Multi-User Authentication**: Secure login system with role-based access control
- **👥 Per-User Data**: Each user has private conversation history and settings
- **🌐 Offline Operation**: Runs completely offline with local Ollama models
- **💻 Modern Web Interface**: Professional dark-themed chat interface
- **🔧 REST API**: Backend API for integration with other applications
- **⚙️ Configurable**: JSON-based configuration for all settings
- **🏗️ Modular Design**: Separate client, server, and frontend components
- **🤖 Model Management**: List and switch between available Ollama models
- **🌍 Network Access**: Configurable to allow local network connections
- **👨‍💼 Admin Panel**: User management and system administration

## Prerequisites

- Python 3.7+
- [Ollama](https://ollama.ai/) installed and running
- At least one Ollama model pulled (e.g., `ollama pull llama3.2`)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/leesihun/LLM_backbone.git
   cd LLM_backbone
   ```

2. **Install dependencies and start the system**
   ```bash
   pip install -r requirements.txt
   python server.py
   ```

3. **Access the login page**
   - **Local access**: `http://localhost:8000/login.html`
   - **Network access**: `http://YOUR_IP_ADDRESS:8000/login.html`

4. **Default login credentials**
   - **Username**: `admin`
   - **Password**: `admin123`
   - **⚠️ Change password immediately after first login!**

5. **Start chatting**
   - After login, you'll be redirected to the main chat interface
   - Your conversations are automatically saved per user

## Configuration

Edit `config.json` to customize settings:

```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "model": "llama3.2",
    "timeout": 30000,
    "num_ctx": 8192,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40
  },
  "server": {
    "port": 8000,
    "host": "0.0.0.0"
  },
  "ui": {
    "title": "HE Team LLM Assistant",
    "theme": "dark"
  }
}
```

## Architecture

### Core Components

- **`user_management.py`** - User authentication and session management
- **`conversation_memory.py`** - Per-user conversation storage and memory
- **`llm_client.py`** - Main LLM interface and communication with Ollama
- **`server.py`** - Flask REST API backend with authentication
- **`index.html`** - Main chat interface (requires authentication)
- **`login.html`** - User login page
- **`config.json`** - System configuration settings
- **`start.py`** - Easy startup script

### API Endpoints

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/change-password` - Change user password

#### Chat & Conversations (Authenticated)
- `POST /api/chat` - Chat completion with conversation memory
- `GET /api/conversations` - List user's conversations
- `GET /api/conversations/<id>/history` - Get conversation history
- `DELETE /api/conversations/<id>` - Delete conversation
- `POST /api/conversations/clear` - Clear all user conversations

#### System
- `GET /api/models` - List available Ollama models
- `GET /api/config` - Get current configuration
- `GET /health` - Health check endpoint

#### Admin Only
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/<username>` - Update user
- `DELETE /api/admin/users/<username>` - Delete user
- `POST /api/admin/users/<username>/reset-password` - Reset user password
- `GET /api/admin/sessions` - List active sessions
- `GET /api/admin/stats` - System statistics

## Usage Examples

### Web Interface
1. Run `python start.py`
2. Open `http://localhost:8000/login.html`
3. Login with default credentials (admin/admin123)
4. Start chatting with your AI assistant

### Command Line (Direct LLM)
```bash
python llm_client.py "What is the capital of France?"
```

### API Integration (Authenticated)
```python
import requests

# Login first
login_response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = login_response.json()['session_token']

# Chat with authentication
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost:8000/api/chat', 
    headers=headers,
    json={'message': 'Hello, AI!'})
print(response.json()['response'])

# List user's conversations
conversations = requests.get('http://localhost:8000/api/conversations', headers=headers)
print(conversations.json())
```

## User Management

### Default Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Administrator
- **⚠️ IMPORTANT**: Change the default password immediately after first login!

### Managing Users

#### Where to Configure Users & Passwords

**1. Programmatically via Admin API:**
```python
import requests

# Login as admin first
admin_login = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
admin_token = admin_login.json()['session_token']
admin_headers = {'Authorization': f'Bearer {admin_token}'}

# Create new user
new_user = requests.post('http://localhost:8000/api/admin/users',
    headers=admin_headers,
    json={
        'username': 'john_doe',
        'password': 'secure_password123',
        'email': 'john@company.com',
        'role': 'user',
        'display_name': 'John Doe'
    })

# Reset user password
reset_pw = requests.post('http://localhost:8000/api/admin/users/john_doe/reset-password',
    headers=admin_headers,
    json={'new_password': 'new_secure_password123'})

# List all users
users = requests.get('http://localhost:8000/api/admin/users', headers=admin_headers)
print(users.json())
```

**2. Direct File Configuration:**

Users are stored in `auth/users.json` (created automatically):
```json
{
  "admin": {
    "user_id": "uuid-here",
    "username": "admin",
    "email": "admin@heteam.com",
    "password_hash": "hashed-password",
    "salt": "random-salt",
    "role": "admin",
    "display_name": "Administrator",
    "created_at": "2025-01-01T00:00:00",
    "is_active": true
  }
}
```

**3. Change Default Admin Password:**
```python
# Method 1: Via API
import requests
headers = {'Authorization': f'Bearer {your_admin_token}'}
requests.post('http://localhost:8000/api/auth/change-password',
    headers=headers,
    json={
        'old_password': 'admin123',
        'new_password': 'your_new_secure_password'
    })

# Method 2: Admin reset (if you forget password, delete auth/users.json and restart)
```

**4. Web Admin Panel:**

User management is handled through the web interface:
- **Login as admin** - Use admin credentials to access admin features
- **Admin Panel** - Available through the web interface for admin users
- **API Endpoints** - Use the REST API endpoints for programmatic user management:
  - `GET /api/admin/users` - List all users
  - `POST /api/admin/users` - Create new user
  - `PUT /api/admin/users/{username}` - Update user
  - `DELETE /api/admin/users/{username}` - Delete user
  - `POST /api/admin/users/{username}/reset-password` - Reset password

### User Roles

**Admin Users:**
- Can create, modify, and delete other users
- Can reset passwords for any user
- Can view system statistics and all active sessions
- Full access to all admin endpoints

**Regular Users:**
- Can chat with AI assistant
- Can manage their own conversations
- Can change their own password
- Cannot access admin functions

### Data Storage Structure

```
project_root/
├── auth/                   # Authentication files
│   ├── users.json         # User accounts
│   └── user_sessions.json # Active sessions
└── conversations/          # Per-user conversation storage
    ├── user-id-1/          # User 1's conversations
    │   ├── session-1.json
    │   └── session-2.json
    └── user-id-2/          # User 2's conversations
        ├── session-1.json
        └── session-2.json
```

## File Structure

```
LLM_based_parser/
├── README.md                 # This file
├── CLAUDE.md                # Development instructions
├── requirements.txt         # Python dependencies
├── server.py               # Main application server
├── setup_system.py         # System setup script
├── config/
│   └── config.json         # System configuration
├── core/                   # Core system modules
│   ├── conversation_memory.py
│   ├── llm_client.py
│   └── user_management.py
├── src/                    # Source modules
│   ├── excel_to_md_converter.py
│   ├── file_handler.py
│   └── rag_system.py
├── data/                   # Data directory
│   ├── chroma_db/         # RAG vector database
│   ├── combined_data.md   # Combined Excel data
│   └── *.xlsx             # Original Excel files
├── uploads/               # File uploads (user-organized)
├── static/                # Static web files
│   ├── index.html         # Main chat interface
│   └── login.html         # Login page
└── auth/                  # Authentication files
    ├── users.json         # User accounts (auto-generated)
    └── user_sessions.json # Active sessions (auto-generated)
```

## Installation Details

### Manual Installation
```bash
pip install -r requirements.txt
python server.py
```

### Dependencies
- `flask==2.3.3` - Web framework
- `flask-cors==4.0.0` - CORS support  
- `requests==2.31.0` - HTTP client

## Network Access

### Allowing Others to Connect

The server is configured to accept connections from other devices on your network:

1. **Find your IP address**
   ```bash
   # Windows
   ipconfig
   
   # Linux/Mac
   ifconfig
   ```

2. **Share the URL with others**
   - Format: `http://YOUR_IP_ADDRESS:3000`
   - Example: `http://192.168.1.100:3000`

3. **Firewall Configuration**
   - **Windows**: Allow Python through Windows Defender Firewall
   - **Mac**: System Preferences > Security & Privacy > Firewall
   - **Linux**: Configure iptables or ufw as needed

4. **Network Requirements**
   - All users must be on the same network (WiFi/LAN)
   - Router must allow internal network communication
   - No VPN conflicts

### Security Considerations

🔒 **Multi-User Security Features:**

- **User Authentication**: Secure login system with session tokens
- **Password Hashing**: PBKDF2 with salt for password security
- **Session Management**: 24-hour session timeout with token validation
- **Role-Based Access**: Admin and user roles with different permissions
- **Data Isolation**: Users can only access their own conversations
- **API Protection**: All endpoints require valid authentication

⚠️ **Network Security:**

- **HTTPS Recommended**: Use reverse proxy (nginx) with SSL for production
- **Firewall Configuration**: Only allow trusted IPs for network access
- **VPN Access**: Consider VPN for remote access to maintain security
- **Change Default Credentials**: Immediately change admin password from default

## Troubleshooting

### Common Issues

**Ollama Connection Error**
- Ensure Ollama is running: `ollama serve`
- Check Ollama URL in `config.json`
- Verify firewall settings

**No Models Available**
- Pull a model: `ollama pull llama3.2`
- Check available models: `ollama list`

**Port Already in Use**
- Change port in `config.json` (default: 8000)
- Kill existing process: `netstat -ano | findstr :8000`

**Login Issues**
- Verify default credentials: admin/admin123
- Check `auth/users.json` file exists and is readable
- Clear browser cache and cookies
- Ensure JavaScript is enabled

**Authentication Errors**
- Check session token hasn't expired (24-hour timeout)
- Verify API requests include Authorization header
- Ensure user account is active (`is_active: true`)

**Can't Create Users**
- Ensure you're logged in as admin
- Check username/email aren't already taken
- Verify password meets minimum requirements (6+ characters)

**Permission Errors**
- Run as administrator (Windows)
- Check file permissions (Linux/Mac)

## Development

### Adding New Features
1. Modify `llm_client.py` for new LLM functionality
2. Add API endpoints in `server.py`  
3. Update frontend in `index.html`
4. Test with different Ollama models

### Custom Models
- Pull any Ollama-compatible model
- Update `config.json` with model name
- Restart the server

## Security Notes

- System runs on localhost by default
- No authentication implemented
- Intended for local development use
- Configure firewall for network access

## License

MIT License - feel free to use and modify as needed.

## System Prompt Configuration

### Overview
The system supports configurable system prompts that define the AI assistant's behavior and personality. You can set different system prompts for different modes of operation.

### Configuration Location
System prompts are configured in `config/config.json` under the `system_prompt` section:

```json
{
  "system_prompt": {
    "enabled": true,
    "universal": "You are an AI assistant for the HE team. Always be professional, accurate, and helpful. Provide clear, concise responses and ask for clarification when needed.",
    "default": "You provide general assistance with various tasks including programming, analysis, and problem-solving.",
    "rag_mode": "You have access to the team's knowledge base. Use the provided context to answer questions accurately. If the context doesn't contain relevant information, say so and provide general guidance if possible.",
    "document_mode": "You are analyzing a document for the user. Provide detailed insights, summaries, and answer questions based on the document content provided.",
    "file_mode": "You are analyzing a specific file for the user. Examine the file content carefully and provide detailed analysis, insights, or answers to the user's questions about the file."
  }
}
```

### System Prompt Types
1. **`universal`** - Base prompt applied to ALL modes (defines core personality and behavior)
2. **`default`** - Additional instructions for normal chat conversations
3. **`rag_mode`** - Additional instructions for RAG knowledge base searches
4. **`document_mode`** - Additional instructions for document analysis
5. **`file_mode`** - Additional instructions for file analysis

### How System Prompts Combine
The system automatically combines prompts as: **Universal + Mode-Specific**

For example, in RAG mode, the final system prompt becomes:
```
You are an AI assistant for the HE team. Always be professional, accurate, and helpful. Provide clear, concise responses and ask for clarification when needed.

You have access to the team's knowledge base. Use the provided context to answer questions accurately. If the context doesn't contain relevant information, say so and provide general guidance if possible.
```

### How to Change System Prompts
1. **Edit the config file**: Modify `config/config.json`
2. **Restart the server**: Changes take effect after restarting
3. **Enable/Disable**: Set `enabled: false` to disable all system prompts

### Examples of Custom System Prompts

**For Technical Support Team:**
```json
{
  "universal": "You are a technical support specialist for the HE team. Always prioritize safety and best practices. Be patient and thorough in your explanations.",
  "default": "Provide step-by-step solutions and ask clarifying questions when needed.",
  "file_mode": "Analyze code or configuration files for issues, bugs, or security vulnerabilities. Suggest specific improvements."
}
```

**For Research Team:**
```json
{
  "universal": "You are a research assistant for the HE team. Be thorough, cite sources when possible, and acknowledge limitations in your knowledge.",
  "rag_mode": "Use the knowledge base to provide comprehensive answers. If information is incomplete, suggest additional research directions.",
  "document_mode": "Analyze research documents for key findings, methodologies, and potential applications."
}
```

**For Development Team:**
```json
{
  "universal": "You are a senior software engineer for the HE team. Focus on code quality, performance, and maintainability.",
  "file_mode": "Review code for bugs, performance issues, security vulnerabilities, and suggest improvements. Be constructive and educational.",
  "default": "Help with programming questions, architecture decisions, and debugging."
}
```

## Recent Updates

### Version 1.2.1 (Latest - December 19, 2024)
- **Tavily API Integration**: Added comprehensive Tavily search API testing and integration
- **Corporate Proxy Support**: Full proxy configuration support for corporate environments
- **Interactive Setup Tools**: Multiple proxy configuration methods (interactive, config-based, environment variables)
- **Connectivity Testing**: Comprehensive network and API connectivity testing tools
- **Integration Guides**: Complete setup guides and troubleshooting documentation

**New Testing Tools:**
- `test_tavily.py` - Comprehensive Tavily API tester with proxy support
- `test_tavily_simple.py` - Interactive proxy setup and testing
- `test_tavily_with_config.py` - Configuration file-based testing
- `proxy_config.json` - Easy proxy configuration template
- `PROXY_SETUP_GUIDE.md` - Complete proxy setup and troubleshooting guide

### Version 1.2 (December 2024)
- **Internet Search**: Added web search functionality using DuckDuckGo
- **Search Mode**: New search mode in the frontend for current web information
- **Array System Prompts**: Support for array format in system prompt configuration
- **Enhanced Context**: Web search results integrated into AI responses

### Version 1.1
- **New Chat Button**: Added "New Chat" button to easily start fresh conversations
- **Enhanced Context Control**: Added configurable context size for Ollama models
- **Model Parameters**: Added temperature, top_p, and top_k configuration options
- **Improved UI**: Better visual styling for the new chat functionality

### Features Added:
1. **Web Search Integration**: Real-time internet search using DuckDuckGo API
2. **Search Mode**: Dedicated search mode that combines web results with AI responses
3. **New Chat Button**: Green "New Chat" button in the header that clears current conversation and starts fresh
4. **Context Size Configuration**: Set `num_ctx` in config.json to control model context window (default: 8192 tokens)
5. **Model Parameters**: Fine-tune model behavior with temperature, top_p, and top_k settings
6. **Array System Prompts**: Support for multi-line system prompts using arrays
7. **User Management**: Complete admin panel for adding/managing users programmatically

### Configuration Options:
```json
{
  "ollama": {
    "num_ctx": 8192,        // Context window size (tokens)
    "temperature": 0.7,     // Creativity level (0.0-1.0)
    "top_p": 0.9,          // Nucleus sampling
    "top_k": 40            // Top-k sampling
  },
  "system_prompt": {
    "enabled": true,        // Enable/disable system prompts
    "universal": "Base prompt for all modes...",
    "default": "Additional prompt for normal chat...",
    "rag_mode": "Additional prompt for RAG searches...",
    "document_mode": "Additional prompt for document analysis...",
    "file_mode": "Additional prompt for file analysis...",
    "search_mode": "Additional prompt for web search..."
  },
  "web_search": {
    "enabled": true,        // Enable/disable web search
    "max_results": 5,       // Maximum search results to return
    "timeout": 10,          // Search timeout in seconds
    "user_agent": "Mozilla/5.0..."  // User agent string
  }
}
```

## Web Search Feature

### Overview
The system now includes real-time internet search capabilities using DuckDuckGo, allowing the AI to provide current and up-to-date information.

### How It Works
1. **User Query**: User asks a question in search mode
2. **Web Search**: System automatically searches DuckDuckGo for relevant results
3. **Context Integration**: Search results are provided to the AI as context
4. **Enhanced Response**: AI responds using both its knowledge and current web information

### Configuration
```json
{
  "web_search": {
    "enabled": true,        // Enable/disable web search
    "max_results": 5,       // Maximum search results per query
    "timeout": 10,          // Search timeout in seconds
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  }
}
```

### API Endpoints
- `POST /api/search/web` - Direct web search (returns raw results)
- `POST /api/search/chat` - Search with AI integration (returns AI response with web context)

### Usage Examples

**Direct Search:**
```bash
curl -X POST http://localhost:8000/api/search/web \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "latest AI developments 2024", "max_results": 3}'
```

**Search with AI Integration:**
```bash
curl -X POST http://localhost:8000/api/search/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "What are the latest AI developments?", "session_id": "your_session"}'
```

### Features
- **No API Keys Required**: Uses DuckDuckGo which doesn't require registration
- **Privacy Focused**: DuckDuckGo doesn't track users
- **Fallback Mechanisms**: Multiple search methods for reliability
- **Rate Limiting**: Built-in timeout and error handling
- **Source Citation**: AI responses include source URLs when available

### Limitations
- **No Real-time Updates**: Search results are fetched at query time, not continuously
- **Rate Limits**: Subject to search provider rate limiting
- **Content Filtering**: Some content may be filtered by search providers
- **Language**: Primarily optimized for English searches
- **Network Dependencies**: Requires internet access and may be affected by firewalls/proxies

### Troubleshooting Search Issues

If web search is not working in your environment, try these solutions:

#### 1. **Run Diagnostic Tool**
```bash
python test_search.py
```
This will test all search providers and diagnose connectivity issues.

#### 2. **Common Issues & Solutions**

**Issue: "All search providers are currently unavailable"**
- **Solution**: Check internet connection and firewall settings
- **Check**: Run `ping google.com` to verify basic connectivity
- **Fix**: Allow Python to access the internet through firewall

**Issue: "DuckDuckGo search error"**
- **Solution**: DuckDuckGo may be blocked in your region/network
- **Fix**: Change provider order in config.json to use Bing first:
```json
{
  "web_search": {
    "providers": ["bing", "duckduckgo", "manual"]
  }
}
```

**Issue: "Bing search error"**
- **Solution**: Bing may be blocking automated requests
- **Fix**: Try different user agent or enable Google Custom Search

**Issue: Corporate network/proxy**
- **Solution**: Configure proxy settings or use manual fallback
- **Fix**: Set `providers: ["manual"]` for manual search links

#### 3. **Testing Tavily API (New)**

For testing the new Tavily search API integration:

**Quick Test:**
```bash
python test_tavily_with_config.py
```

**Interactive Setup:**
```bash
python test_tavily_simple.py
```

**Corporate Proxy Issues:**
1. Edit `proxy_config.json` with your company's proxy settings
2. Run the configuration-based tester
3. See `PROXY_SETUP_GUIDE.md` for detailed troubleshooting

**Common Proxy Formats:**
- No auth: `http://proxy.company.com:8080`
- With auth: `http://username:password@proxy.company.com:8080`

#### 3. **Alternative Configurations**

**For restricted networks:**
```json
{
  "web_search": {
    "enabled": true,
    "providers": ["manual"],
    "timeout": 5
  }
}
```

**For Google Custom Search (requires API key):**
```json
{
  "web_search": {
    "providers": ["google_custom", "bing", "manual"],
    "google_api_key": "YOUR_API_KEY",
    "google_search_engine_id": "YOUR_SEARCH_ENGINE_ID"
  }
}
```

**For maximum reliability:**
```json
{
  "web_search": {
    "providers": ["bing", "duckduckgo", "google_custom", "manual"],
    "timeout": 15,
    "max_results": 3
  }
}
```

#### 4. **Getting Google Custom Search API**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Custom Search API
3. Create API key
4. Create Custom Search Engine at [cse.google.com](https://cse.google.com/)
5. Add credentials to config.json

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly  
5. Submit pull request

## Support

For issues and questions:
- Check troubleshooting section
- Review Ollama documentation
- Open GitHub issue with details
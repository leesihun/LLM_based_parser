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
    "timeout": 30000
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
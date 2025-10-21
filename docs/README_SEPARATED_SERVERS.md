# Separated Frontend and Backend Servers

This document explains how to run the frontend and backend as separate servers.

## Overview

The application has been refactored to separate the frontend and backend:

- **Backend Server**: Provides REST API endpoints (runs on port 8000 by default)
- **Frontend Server**: Serves static HTML/CSS/JS files (runs on port 3000 by default)

This separation allows for:
- Independent deployment of frontend and backend
- Better scalability
- Easier development (can work on frontend/backend independently)
- Production-ready architecture

## Quick Start

### Option 1: Run Both Servers (Recommended for Development)

Open **two separate terminals**:

#### Terminal 1 - Backend API Server
```bash
python run_backend.py
```

This will start the backend API server on `http://localhost:8000`

#### Terminal 2 - Frontend Server
```bash
python run_frontend.py
```

This will start the frontend server on `http://localhost:3000`

Then open your browser and navigate to: **http://localhost:3000**

### Option 2: Run with Environment Variables

You can customize the ports using environment variables:

```bash
# Terminal 1 - Backend
set BACKEND_HOST=0.0.0.0
set BACKEND_PORT=8000
python run_backend.py

# Terminal 2 - Frontend
set FRONTEND_HOST=0.0.0.0
set FRONTEND_PORT=3000
python run_frontend.py
```

## Configuration

### Backend Configuration

The backend API URL is configured in: `frontend/static/config.js`

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000'
};
```

**Change this if your backend is running on a different host or port.**

For example, if running backend on a different machine:
```javascript
const CONFIG = {
    API_BASE_URL: 'http://192.168.1.100:8000'
};
```

### CORS Settings

The backend is configured to accept requests from any origin during development:

```python
# In backend/app/__init__.py
CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": {"origins": "*"}},
    ...
)
```

**For production**, change `"origins": "*"` to your specific frontend URL:
```python
resources={r"/api/*": {"origins": "http://your-frontend-domain.com"}}
```

## Project Structure

```
LLM_based_parser/
├── run_backend.py           # Backend server entry point
├── run_frontend.py          # Frontend server entry point
├── server.py                # Old combined server (deprecated)
│
├── backend/                 # Backend API code
│   ├── app/
│   │   ├── __init__.py     # Flask app factory (API only)
│   │   └── routes/         # API route handlers
│   ├── core/               # Core business logic
│   └── services/           # Services (LLM, RAG, etc.)
│
└── frontend/               # Frontend static files
    └── static/
        ├── index.html      # Main application UI
        ├── login.html      # Login page
        └── config.js       # Frontend configuration
```

## API Endpoints

The backend provides the following main endpoints:

### Health & Status
- `GET /` - API status
- `GET /health` - System health check

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/change-password` - Change password

### Chat
- `POST /api/chat` - Normal chat
- `POST /api/chat/rag` - RAG-enabled chat
- `POST /api/chat/web-search` - Web search chat

### Files
- `GET /api/files` - List uploaded files
- `POST /api/files/upload` - Upload a file
- `POST /api/files/{id}/read` - Analyze a file
- `DELETE /api/files/{id}` - Delete a file

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/models` - List available LLM models

### RAG
- `GET /api/rag/stats` - Get RAG statistics

## Testing the Separation

1. **Start Backend Only**:
   ```bash
   python run_backend.py
   ```
   Visit http://localhost:8000 - you should see JSON API status

2. **Start Frontend Only**:
   ```bash
   python run_frontend.py
   ```
   Visit http://localhost:3000 - you should see the login page
   (It won't work until backend is also running)

3. **Start Both**:
   Start both servers, then visit http://localhost:3000
   The application should work normally

## Migration from Old Server

If you were previously using `server.py`:

### Old Way (Deprecated):
```bash
python server.py
# Served both API and frontend from http://localhost:8000
```

### New Way:
```bash
# Terminal 1
python run_backend.py    # API on http://localhost:8000

# Terminal 2
python run_frontend.py   # Frontend on http://localhost:3000
```

## Production Deployment

For production, consider using:

### Backend
- **WSGI Server**: Use Gunicorn or uWSGI instead of Flask's built-in server
  ```bash
  gunicorn -w 4 -b 0.0.0.0:8000 "backend.app:create_app()"
  ```

### Frontend
- **Static File Hosting**: Use Nginx, Apache, or a CDN
- **Environment-specific Config**: Update `frontend/static/config.js` with production API URL

### Example Nginx Configuration

```nginx
# Frontend
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/LLM_based_parser/frontend/static;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Backend (reverse proxy)
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then update `frontend/static/config.js`:
```javascript
const CONFIG = {
    API_BASE_URL: 'http://api.your-domain.com'
};
```

## Troubleshooting

### Frontend Can't Connect to Backend

**Problem**: Frontend shows connection errors

**Solutions**:
1. Make sure backend server is running: `python run_backend.py`
2. Check `frontend/static/config.js` has correct backend URL
3. Check CORS settings in `backend/app/__init__.py`
4. Check browser console for error messages

### CORS Errors

**Problem**: Browser shows CORS policy errors

**Solution**: Update CORS configuration in `backend/app/__init__.py` to allow your frontend origin

### Port Already in Use

**Problem**: "Address already in use" error

**Solutions**:
```bash
# Find and kill process using port 8000 (backend)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Find and kill process using port 3000 (frontend)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

Or use different ports:
```bash
set BACKEND_PORT=8001
set FRONTEND_PORT=3001
```

## Features

- ✅ Complete separation of frontend and backend
- ✅ Independent deployment capability
- ✅ Configurable API URL
- ✅ CORS properly configured
- ✅ Production-ready architecture
- ✅ Backward compatible (old `server.py` still works)

## Support

For questions or issues, contact s.hun.lee

---

**Version**: 2.2.0
**Date**: 2025-10-21
**Status**: ✅ Production Ready

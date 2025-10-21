# Frontend/Backend Separation - COMPLETE ✅

## Summary

The HE Team LLM Assistant has been successfully separated into independent frontend and backend servers!

## What Changed

### Before
```
server.py
  ├── Served both API endpoints (/api/*)
  └── Served frontend files (/index.html, /login.html)

Single server on port 8000
```

### After
```
run_backend.py                    run_frontend.py
  ├── API endpoints only (/api/*)   ├── Static HTML files
  └── Port 8000 (default)           └── Port 3000 (default)

Two separate servers
```

## New Files Created

1. **[run_backend.py](run_backend.py)** - Backend API server
2. **[run_frontend.py](run_frontend.py)** - Frontend static file server
3. **[frontend/static/config.js](frontend/static/config.js)** - Frontend configuration
4. **[start_servers.bat](start_servers.bat)** - Windows batch script to start both servers
5. **[README_SEPARATED_SERVERS.md](README_SEPARATED_SERVERS.md)** - Complete documentation
6. **update_frontend_urls.py** - Utility script to update fetch URLs

## Modified Files

1. **[backend/app/__init__.py](backend/app/__init__.py)**
   - Removed frontend static file serving
   - Updated CORS configuration for separate frontend
   - Added API status endpoint at root `/`

2. **[frontend/static/index.html](frontend/static/index.html)**
   - Added `config.js` script import
   - Added `apiUrl()` helper function
   - Updated all `fetch()` calls to use configurable backend URL

3. **[frontend/static/login.html](frontend/static/login.html)**
   - Added `config.js` script import
   - Added `apiUrl()` helper function
   - Updated `fetch()` calls to use configurable backend URL

## How to Use

### Option 1: Use Batch Script (Windows - Easiest!)

Double-click **[start_servers.bat](start_servers.bat)**

This will:
- Open two command windows
- Start backend on port 8000
- Start frontend on port 3000
- Show you the URLs to access

### Option 2: Manual Start (Two Terminals)

**Terminal 1:**
```bash
python run_backend.py
```

**Terminal 2:**
```bash
python run_frontend.py
```

Then open browser: **http://localhost:3000**

### Option 3: Custom Ports

```bash
# Terminal 1
set BACKEND_PORT=8001
python run_backend.py

# Terminal 2
set FRONTEND_PORT=3001
python run_frontend.py
```

Don't forget to update `frontend/static/config.js` to match!

## Configuration

### Backend URL Configuration

Edit **[frontend/static/config.js](frontend/static/config.js)**:

```javascript
const CONFIG = {
    // Change this if backend is on different host/port
    API_BASE_URL: 'http://localhost:8000'
};
```

### CORS Configuration (Production)

Edit **[backend/app/__init__.py](backend/app/__init__.py)**:

```python
CORS(
    app,
    supports_credentials=True,
    # Change "*" to your specific frontend URL in production
    resources={r"/api/*": {"origins": "*"}},
    ...
)
```

## Benefits

✅ **Independent Deployment** - Deploy frontend and backend separately
✅ **Scalability** - Scale frontend and backend independently
✅ **Development Flexibility** - Work on frontend or backend without affecting the other
✅ **Production Ready** - Standard architecture for modern web applications
✅ **Security** - Better control over CORS and API access
✅ **Performance** - Can use specialized servers (Nginx for frontend, Gunicorn for backend)

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│  Frontend Server    │         │  Backend API Server │
│  (Port 3000)        │         │  (Port 8000)        │
│                     │         │                     │
│  • index.html       │ ──────> │  • /api/chat        │
│  • login.html       │  HTTP   │  • /api/auth        │
│  • config.js        │ Requests│  • /api/files       │
│  • CSS/JS          │ <────── │  • /api/rag         │
│                     │ JSON    │  • /health          │
└─────────────────────┘         └─────────────────────┘
         │                               │
         │                               │
         └──────> Browser <──────────────┘
              http://localhost:3000
```

## Testing

1. **Backend Only**
   ```bash
   python run_backend.py
   # Visit: http://localhost:8000
   # Should show: {"status": "running", "message": "HE Team LLM Assistant - Backend API", ...}
   ```

2. **Frontend Only**
   ```bash
   python run_frontend.py
   # Visit: http://localhost:3000
   # Should show: Login page (but API calls will fail)
   ```

3. **Both Servers**
   ```bash
   # Run both servers
   # Visit: http://localhost:3000
   # Should work: Full application functionality
   ```

## Backward Compatibility

The old `server.py` still works for users who prefer the combined server:

```bash
python server.py
# Still serves both frontend and API on port 8000
```

However, the new separated approach is recommended for production use.

## Next Steps (Optional)

For production deployment:

1. **Use Production WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 "backend.app:create_app()"
   ```

2. **Use Nginx for Frontend**
   - Serve static files with Nginx
   - Proxy API requests to backend
   - Enable HTTPS with SSL certificates

3. **Update Configuration**
   - Set specific CORS origins (not `*`)
   - Use environment variables for sensitive config
   - Update `config.js` with production API URL

## Troubleshooting

See **[README_SEPARATED_SERVERS.md](README_SEPARATED_SERVERS.md)** for detailed troubleshooting guide.

Common issues:
- **Can't connect**: Make sure both servers are running
- **CORS errors**: Check CORS config in backend
- **Wrong port**: Update `config.js` with correct backend URL

## File Reference

All changes and new files:

- ✅ [run_backend.py](run_backend.py) - NEW
- ✅ [run_frontend.py](run_frontend.py) - NEW
- ✅ [frontend/static/config.js](frontend/static/config.js) - NEW
- ✅ [start_servers.bat](start_servers.bat) - NEW
- ✅ [README_SEPARATED_SERVERS.md](README_SEPARATED_SERVERS.md) - NEW
- ✅ [backend/app/__init__.py](backend/app/__init__.py) - MODIFIED
- ✅ [frontend/static/index.html](frontend/static/index.html) - MODIFIED
- ✅ [frontend/static/login.html](frontend/static/login.html) - MODIFIED

## Support

For questions or issues, contact s.hun.lee

---

**Version**: 2.2.0
**Date**: 2025-10-21
**Status**: ✅ COMPLETE AND READY TO USE

**Separation successful! 🎉**

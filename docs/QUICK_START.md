# Quick Start Guide - Separated Servers

## Fastest Way to Start (Windows)

1. Double-click **`start_servers.bat`**
2. Open browser to **http://localhost:3000**
3. Login with default credentials:
   - Username: `guest`
   - Password: `guest_test1`

That's it! 🎉

---

## Manual Start (Any OS)

### Step 1: Start Backend
```bash
python run_backend.py
```
✓ Backend API running on http://localhost:8000

### Step 2: Start Frontend (in new terminal)
```bash
python run_frontend.py
```
✓ Frontend UI running on http://localhost:3000

### Step 3: Open Browser
Navigate to **http://localhost:3000**

---

## What's Running?

| Server | Port | Purpose | URL |
|--------|------|---------|-----|
| Backend | 8000 | API endpoints | http://localhost:8000 |
| Frontend | 3000 | User interface | http://localhost:3000 |

---

## Configure Backend URL

If backend is on different host/port, edit **`frontend/static/config.js`**:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://YOUR_BACKEND_IP:8000'
};
```

---

## Stop Servers

Press **Ctrl+C** in each terminal window

---

## Troubleshooting

**Frontend can't connect to backend?**
1. Make sure backend is running: `python run_backend.py`
2. Check `frontend/static/config.js` has correct URL
3. Check browser console for errors

**Port already in use?**
```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
set BACKEND_PORT=8001
python run_backend.py
```

---

## Default Login

- **Username**: `guest`
- **Password**: `guest_test1`

For your own ID, contact s.hun.lee

---

## More Info

- **Complete Guide**: [README_SEPARATED_SERVERS.md](README_SEPARATED_SERVERS.md)
- **Summary**: [SEPARATION_COMPLETE.md](SEPARATION_COMPLETE.md)
- **Old Combined Server**: `python server.py` (still works!)

---

✅ **Ready to use!**

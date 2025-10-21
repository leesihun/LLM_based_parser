@echo off
REM Start both frontend and backend servers
REM This script opens two command windows

echo Starting HE Team LLM Assistant Servers...
echo.

REM Start backend in new window
start "Backend API Server" cmd /k "python run_backend.py"

REM Wait a moment for backend to initialize
timeout /t 2 /nobreak > nul

REM Start frontend in new window
start "Frontend Server" cmd /k "python run_frontend.py"

REM Wait a moment for frontend to start
timeout /t 2 /nobreak > nul

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo Frontend UI:  http://localhost:3000
echo.
echo Open your browser and go to:
echo http://localhost:3000
echo.
echo Press Ctrl+C in each window to stop the servers
echo ========================================
echo.
pause

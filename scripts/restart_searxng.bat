@echo off
REM SearXNG Restart Script for Windows
REM Restarts the SearXNG Docker container via WSL

echo Restarting SearXNG container...

wsl -d Ubuntu -e docker restart searxng

if %ERRORLEVEL% EQU 0 (
    echo [OK] SearXNG container restarted successfully

    echo Waiting for SearXNG to be ready...
    timeout /t 3 /nobreak > nul

    echo Testing SearXNG connection...
    wsl bash -c "curl -s --max-time 5 'http://localhost:8080/search?q=test&format=json&language=en' | head -c 50"

    if %ERRORLEVEL% EQU 0 (
        echo [OK] SearXNG is responding
    ) else (
        echo [WARNING] SearXNG may not be responding yet
    )
) else (
    echo [FAILED] Could not restart SearXNG container
    exit /b 1
)

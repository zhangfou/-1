@echo off
setlocal
cd /d "%~dp0"
echo Starting RP Hub local server. Close this window to stop it.
start "" "http://localhost:8000"
python -m http.server 8000 --bind 127.0.0.1
if errorlevel 1 (
    echo.
    echo Python was not found. Install Python or use VS Code Live Server.
)
pause
endlocal

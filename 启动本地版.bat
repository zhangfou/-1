@echo off
setlocal
cd /d "%~dp0"
echo Starting RP Hub local gateway. Close this window to stop it.
echo LAN access is enabled for phones on the same Wi-Fi.
ipconfig | findstr /i "IPv4"
python local-gateway.py --host 0.0.0.0 --port 8000 --open
if errorlevel 1 (
    py -3 local-gateway.py --host 0.0.0.0 --port 8000 --open
)
if errorlevel 1 (
    echo.
    echo Python was not found. Install Python 3 or use VS Code Live Server.
)
pause
endlocal

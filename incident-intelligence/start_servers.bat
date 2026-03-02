@echo off
echo Starting IntelResponse Backend...
start "IntelResponse Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

echo Starting IntelResponse Frontend...
start "IntelResponse Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Both servers are starting. 
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173

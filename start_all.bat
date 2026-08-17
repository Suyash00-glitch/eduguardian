@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo   Starting EduGuardian AI System (All Services)
echo ========================================================
echo.

echo [0/3] Freeing ports 8000, 8001, 8002, 8003, 5173...
powershell -Command "Get-NetTCPConnection -LocalPort 8000,8001,8002,8003,5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>&1
timeout /t 2 /nobreak >nul

echo [1/3] Starting A2A Agent Microservices (:8001, :8002, :8003)...
start "A2A_Agents" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe chatbot/run_a2a_services.py"

timeout /t 3 /nobreak >nul

echo [2/3] Starting FastAPI Gateway (:8000)...
start "FastAPI_Gateway" cmd /k "cd /d "%~dp0" && .venv\Scripts\uvicorn.exe chatbot.backend.api.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend UI (:5173)...
start "Frontend_UI" cmd /k "cd /d "%~dp0chatbot\frontend" && npm.cmd run dev"

echo.
echo ========================================================
echo   All 3 services launched in separate windows!
echo   Frontend UI:  http://localhost:5173/
echo   API Docs:     http://localhost:8000/docs
echo ========================================================
echo.
pause

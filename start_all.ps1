$ROOT = $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting EduGuardian AI System (All Services)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[0/3] Stopping any old instances..." -ForegroundColor Yellow
Get-Process python,uvicorn,node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "[1/3] Starting A2A Agent Microservices (:8001, :8002, :8003)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT'; .venv\Scripts\python.exe chatbot/run_a2a_services.py"
Start-Sleep -Seconds 3

Write-Host "[2/3] Starting FastAPI Gateway & LangGraph (:8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT'; .venv\Scripts\uvicorn.exe chatbot.backend.api.main:app --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 3

Write-Host "[3/3] Starting Frontend React UI (:5173)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT\chatbot\frontend'; npm run dev"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  All services started!" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:5173/" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan


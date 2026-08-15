# Starts all services silently in background without extra terminal popups
Write-Host "Stopping any old instances..." -ForegroundColor Yellow
Get-Process python,uvicorn,node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "Starting A2A Agent Services, FastAPI Gateway, and Frontend in background..." -ForegroundColor Cyan
Start-Process -FilePath "c:\hackthon_2\eduguardian\.venv\Scripts\python.exe" -ArgumentList "chatbot/run_a2a_services.py" -WorkingDirectory "c:\hackthon_2\eduguardian" -WindowStyle Hidden
Start-Sleep -Seconds 2

Start-Process -FilePath "c:\hackthon_2\eduguardian\.venv\Scripts\uvicorn.exe" -ArgumentList "chatbot.backend.api.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory "c:\hackthon_2\eduguardian" -WindowStyle Hidden
Start-Sleep -Seconds 2

Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "c:\hackthon_2\eduguardian\chatbot\frontend" -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  All services are running silently in the background!" -ForegroundColor Green
Write-Host "  Frontend:  http://localhost:5173/" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  To stop: run ./stop_all.bat" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green

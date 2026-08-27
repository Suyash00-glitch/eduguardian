@echo off
title EduGuardian AI - Stop All
echo Stopping all EduGuardian AI processes...
powershell -Command "Get-Process python,uvicorn,node -ErrorAction SilentlyContinue | Stop-Process -Force"
echo All services stopped.
pause

@echo off
echo Stopping all services...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im caddy.exe >nul 2>&1
taskkill /f /im llama-server.exe >nul 2>&1
echo All services stopped
@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting All Services...
echo.

REM Kill any existing services
call stop-services.bat >nul 2>&1

REM Start Caddy
echo Starting Caddy...
start "Caddy" /min cmd /c "caddy run"

REM Start API Server
echo Starting API Server...
start "API Server" /min cmd /c "cd api_server && python -m uvicorn api_server:app --host 0.0.0.0 --port 8000"

REM Start Blazor App
echo Starting Blazor App...
timeout /t 2 >nul
start "Blazor" /min cmd /c "cd blazor-app\publish\wwwroot && python -m http.server 5000"

REM Start Llama (if model exists)
echo Checking for Llama...
dir models\*.gguf >nul 2>&1
if %errorlevel% equ 0 (
    if exist "llama-server.exe" (
        echo Starting Llama Server...
        start "Llama" /min cmd /c "start-llama.bat"
    ) else (
        echo Llama server not available
    )
) else (
    echo No model files found for Llama
)

echo.
echo Waiting for services to start...
timeout /t 5 >nul

echo.
echo ========================================
echo Services Status:
echo ========================================
call :check_service 5000 "Blazor App"
call :check_service 8000 "API Server" 
call :check_service 8080 "Llama Server"
call :check_service 80 "Caddy Proxy"

echo.
echo ========================================
echo Access URLs:
echo ========================================
echo Main Portal: http://localhost
echo Blazor Direct: http://localhost:5000
echo API Direct: http://localhost:8000
if exist "models\*.gguf" if exist "llama-server.exe" echo Llama Direct: http://localhost:8080
echo.
echo Press any key to stop all services...
pause >nul

call stop-services.bat
exit /b 0

:check_service
netstat -ano | findstr ":%1 " >nul
if %errorlevel% equ 0 (
    echo ✅ %~2
) else (
    echo ❌ %~2
)
exit /b 0
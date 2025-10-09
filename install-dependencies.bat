@echo off
chcp 65001 >nul
echo Installing Dependencies...
cd /d "%~dp0"

echo ========================================
echo 1. Checking Python...
echo ========================================
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python manually from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
) else (
    python --version
    echo Installing Python dependencies...
    pip install searxng fastapi uvicorn requests
    pip install beautifulsoup4

)

echo.
echo ========================================
echo 2. Checking Caddy...
echo ========================================
where caddy >nul 2>nul
if %errorlevel% neq 0 (
    echo Downloading Caddy...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/caddyserver/caddy/releases/download/v2.7.6/caddy_2.7.6_windows_amd64.zip' -OutFile 'caddy.zip'"
    powershell -Command "Expand-Archive -Path 'caddy.zip' -DestinationPath '.' -Force"
    del caddy.zip
    echo Caddy installed locally.
) else (
    echo Caddy already installed.
)

echo.
echo ========================================
echo 3. Checking .NET...
echo ========================================
where dotnet >nul 2>nul
if %errorlevel% neq 0 (
    echo .NET not found. We'll use standalone publish for Blazor app.
) else (
    dotnet --version
    echo .NET already installed.
)

echo.
echo ========================================
echo 4. Setting up Llama.cpp...
echo ========================================
if not exist "llama-server.exe" (
    echo Downloading Llama.cpp binary package...
    
    REM Download the complete binary package
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ggml-org/llama.cpp/releases/download/b6715/llama-b6715-bin-win-vulkan-x64.zip' -OutFile 'llama-bin.zip'"
    
    if exist "llama-bin.zip" (
        echo Extracting Llama.cpp binaries...
        powershell -Command "Expand-Archive -Path 'llama-bin.zip' -DestinationPath 'llama-temp' -Force"
        
        REM Look for the server executable in the extracted files
        if exist "llama-temp\server.exe" (
            copy "llama-temp\server.exe" "llama-server.exe"
            echo Llama server extracted successfully.
        ) else if exist "llama-temp\bin\server.exe" (
            copy "llama-temp\bin\server.exe" "llama-server.exe"
            echo Llama server extracted successfully.
        ) else (
            echo Searching for server executable in extracted files...
            dir llama-temp /s /b | findstr /i "server.exe"
        )
        
        REM Clean up
        if exist "llama-temp" rmdir /s /q "llama-temp"
        if exist "llama-bin.zip" del "llama-bin.zip"
        
        if not exist "llama-server.exe" (
            echo WARNING: Could not find server.exe in the downloaded package.
            echo Please extract manually and rename server.exe to llama-server.exe
        )
    ) else (
        echo Failed to download Llama.cpp package.
        echo Please download manually from:
        echo https://github.com/ggml-org/llama.cpp/releases
    )
) else (
    echo Llama.cpp server already exists.
)

echo.
echo ========================================
echo 5. Creating project structure...
echo ========================================
if not exist "models" mkdir models
if not exist "searxng" mkdir searxng
if not exist "api_server" mkdir api_server
if not exist "blazor-app" mkdir blazor-app

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo Next steps:
if not exist "llama-server.exe" (
    echo 1. MANUAL STEP: Download and extract llama-server.exe
    echo    Get from: https://github.com/ggml-org/llama.cpp/releases
)
echo 1. Place your model file in models\ folder
echo 2. Add SearXNG settings to searxng\ folder  
echo 3. Add your API server code to api_server\
echo 4. Add your Blazor app to blazor-app\
echo.
echo Run start-services.bat to start all services
pause
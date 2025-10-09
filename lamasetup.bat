@echo off
chcp 65001 >nul
echo Downloading Llama.cpp...
echo.

echo Downloading from:
echo https://github.com/ggml-org/llama.cpp/releases/download/b6719/llama-b6719-bin-win-vulkan-x64.zip
echo.

powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ggml-org/llama.cpp/releases/download/b6719/llama-b6719-bin-win-vulkan-x64.zip' -OutFile 'llama.zip'"

if not exist "llama.zip" (
    echo ❌ Download failed
    pause
    exit /b 1
)

echo Extracting...
powershell -Command "Expand-Archive -Path 'llama.zip' -DestinationPath '.' -Force"

echo Looking for server executable...
if exist "llama-server.exe" (
    echo ✅ Found llama-server.exe
    goto :success
)

REM The files might be in a subdirectory
for /d %%i in (*) do (
    if exist "%%i\llama-server.exe" (
        echo Found in subdirectory: %%i
        copy "%%i\llama-server.exe" "llama-server.exe"
        goto :success
    )
)

echo ❌ Could not find llama-server.exe in the extracted files
echo Contents:
dir /b
pause
exit /b 1

:success
echo.
echo ✅ Llama server ready!
echo Cleanup...
del llama.zip
for /d %%i in (*) do (
    if exist "%%i\llama-server.exe" (
        echo Removing temp directory: %%i
        rmdir /s /q "%%i"
    )
)

echo.
echo Test the server:
echo llama-server --host 0.0.0.0 --port 8080
pause
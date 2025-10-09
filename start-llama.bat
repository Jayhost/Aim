@echo off
chcp 65001 >nul
echo Starting Llama Server...
echo.

if not exist "llama-server.exe" (
    echo ❌ llama-server.exe not found
    pause
    exit /b 1
)

echo Looking for model files...
dir models\*.gguf /b >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ No .gguf model files found in models\ folder
    echo.
    echo Download a model file first, for example:
    echo https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
    pause
    exit /b 1
)

echo Found models:
for /f "delims=" %%i in ('dir models\*.gguf /b') do echo   - %%i

echo.
echo Using first model found...
for /f "delims=" %%i in ('dir models\*.gguf /b') do (
    echo Starting with model: %%i
    llama-server --model models\%%i --host 0.0.0.0 -ngl 99 --port 8080 --jinja
    goto :end
)

:end
echo.
pause
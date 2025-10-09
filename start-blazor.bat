@echo off
cd /d "%~dp0"

echo Starting Blazor WebAssembly App...

REM Check for Blazor WebAssembly static files
if exist "blazor-app\publish\wwwroot\index.html" (
    echo Starting Blazor WebAssembly from: publish\wwwroot
    start "Blazor App" /min cmd /c "cd blazor-app\publish\wwwroot && python -m http.server 5000"
    goto :end
)

if exist "blazor-app\publish\index.html" (
    echo Starting Blazor WebAssembly from: publish
    start "Blazor App" /min cmd /c "cd blazor-app\publish && python -m http.server 5000"
    goto :end
)

if exist "blazor-app\bin\Release\net8.0\publish\wwwroot\index.html" (
    echo Starting Blazor WebAssembly from: bin\Release\net8.0\publish\wwwroot
    start "Blazor App" /min cmd /c "cd blazor-app\bin\Release\net8.0\publish\wwwroot && python -m http.server 5000"
    goto :end
)

echo ❌ No Blazor WebAssembly files found
echo Creating placeholder...
if not exist "blazor-placeholder" mkdir blazor-placeholder
cd blazor-placeholder
echo ^<html^>^<body^>^<h1^>Blazor App^</h1^>^<p^>Publish your Blazor WebAssembly app first^</p^>^</body^>^</html^> > index.html
start "Blazor App" /min cmd /c "cd blazor-placeholder && python -m http.server 5000"

:end
echo Blazor WebAssembly app starting on http://localhost:5000
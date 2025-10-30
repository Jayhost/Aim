#!/bin/bash

cd "$(dirname "$0")"

echo "Starting Blazor WebAssembly App..."

# Check for Blazor WebAssembly static files
if [ -f "blazor-app/publish/wwwroot/index.html" ]; then
    echo "Starting Blazor WebAssembly from: publish/wwwroot"
    cd blazor-app/publish/wwwroot
    python3 -m http.server 5000 &
    exit 0
fi

if [ -f "blazor-app/publish/index.html" ]; then
    echo "Starting Blazor WebAssembly from: publish"
    cd blazor-app/publish
    python3 -m http.server 5000 &
    exit 0
fi

if [ -f "blazor-app/bin/Release/net8.0/publish/wwwroot/index.html" ]; then
    echo "Starting Blazor WebAssembly from: bin/Release/net8.0/publish/wwwroot"
    cd blazor-app/bin/Release/net8.0/publish/wwwroot
    python3 -m http.server 5000 &
    exit 0
fi

echo "❌ No Blazor WebAssembly files found"
echo "Creating placeholder..."
mkdir -p blazor-placeholder
cd blazor-placeholder
cat > index.html << 'EOF'
<html><body><h1>Blazor App</h1><p>Publish your Blazor WebAssembly app first</p></body></html>
EOF
python3 -m http.server 5000 &
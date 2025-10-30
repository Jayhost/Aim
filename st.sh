#!/bin/bash

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting All Services from: $SCRIPT_DIR"
echo

# Kill any existing services first
if [ -f "./stop-services.sh" ]; then
    ./stop-services.sh > /dev/null 2>&1
fi
sleep 2

# Function to check if a port is in use
check_port() {
    netstat -tuln 2>/dev/null | grep ":$1 " > /dev/null
}

# Simple PID tracking
PIDS=""
PID_FILE="$SCRIPT_DIR/.service_pids"

echo "=== Starting Services (No Caddy Proxy) ==="

# Skip Caddy to avoid proxy issues with search
echo "📦 Caddy skipped to avoid proxy interference with search"

# 1. Start API Server
echo "🐍 Starting API Server..."
# Kill anything on port 8000 first
pkill -f "uvicorn" 2>/dev/null
sleep 1

if [ -f "api_server/api_server.py" ]; then
    cd api_server
    python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 &
    API_PID=$!
    PIDS="$PIDS $API_PID"
    cd ..
    echo "✅ API Server started from api_server/ directory (PID: $API_PID)"
    # Wait longer for API server to start
    sleep 5
else
    echo "❌ api_server.py not found in api_server/ directory"
fi

# 2. Start Llama Server with ABSOLUTE paths
echo "🧠 Starting Llama Server..."
if [ -f "llama.cpp/build/bin/llama-server" ]; then
    LLAMA_PATH="$SCRIPT_DIR/llama.cpp/build/bin/llama-server"
    echo "Found llama-server at: $LLAMA_PATH"
    
    # Find model with absolute path
    MODEL_FILE=$(find "$SCRIPT_DIR/models" -name "*.gguf" -type f | head -1)
    if [ -n "$MODEL_FILE" ]; then
        echo "Using model: $MODEL_FILE"
        
        # Start llama server with absolute path to model
        cd "$SCRIPT_DIR/llama.cpp/build/bin"
        ./llama-server --model "$MODEL_FILE" -ngl 99 --host 0.0.0.0 -c 16000 --port 8080 --jinja &
        LLAMA_PID=$!
        PIDS="$PIDS $LLAMA_PID"
        cd "$SCRIPT_DIR"
        echo "✅ Llama Server started (PID: $LLAMA_PID)"
        
        # Wait a bit for llama server to initialize
        echo "⏳ Waiting for Llama Server to load model..."
        sleep 15
    else
        echo "❌ No GGUF model files found in $SCRIPT_DIR/models/"
        echo "Available files:"
        ls -la "$SCRIPT_DIR/models/" 2>/dev/null || echo "Models directory not found"
    fi
else
    echo "❌ llama-server not found at $SCRIPT_DIR/llama.cpp/build/bin/llama-server"
fi

# 3. Start Blazor App with proper SSE support
echo "🌐 Starting Blazor App..."
# Kill anything on port 5000 first
pkill -f "python3.*5000" 2>/dev/null
pkill -f "http-server.*5000" 2>/dev/null
pkill -f "node.*5000" 2>/dev/null
sleep 2

# Find the publish directory
BLAZOR_DIR=""
if [ -d "blazor-app/publish/wwwroot" ] && [ -f "blazor-app/publish/wwwroot/index.html" ]; then
    BLAZOR_DIR="blazor-app/publish/wwwroot"
    echo "✅ Found Blazor app at: $BLAZOR_DIR"
elif [ -d "blazor-app/publish" ] && [ -f "blazor-app/publish/index.html" ]; then
    BLAZOR_DIR="blazor-app/publish"
    echo "✅ Found Blazor app at: $BLAZOR_DIR"
else
    BLAZOR_DIR="blazor-static"
    mkdir -p "$BLAZOR_DIR"
    cat > "$BLAZOR_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Cluj AI</title>
    <style>body { font-family: Arial, sans-serif; margin: 40px; }</style>
</head>
<body>
    <h1>Cluj AI Assistant</h1>
    <p>Static mode with streaming support</p>
</body>
</html>
EOF
    echo "⚠️  Using placeholder Blazor app at: $BLAZOR_DIR"
fi

# Check if port 5000 is available
if check_port 5000; then
    echo "❌ Port 5000 is already in use"
    echo "Killing processes on port 5000..."
    fuser -k 5000/tcp 2>/dev/null
    sleep 2
fi

# Start the server - FIX: redirect stdin from /dev/null to prevent stopping
cd "$BLAZOR_DIR"
if command -v npx &> /dev/null; then
    echo "🚀 Starting with npx http-server..."
    npx http-server -p 5000 --cors -c-1 < /dev/null &
    BLAZOR_PID=$!
    PIDS="$PIDS $BLAZOR_PID"
    cd "$SCRIPT_DIR"
    echo "✅ Blazor App with SSE support (PID: $BLAZOR_PID)"
else
    echo "🚀 Starting with Python HTTP server..."
    python3 -m http.server 5000 < /dev/null &
    BLAZOR_PID=$!
    PIDS="$PIDS $BLAZOR_PID"
    cd "$SCRIPT_DIR"
    echo "✅ Blazor App with Python server (PID: $BLAZOR_PID)"
fi

# Save PIDs to file
echo "$PIDS" | tr ' ' '\n' | grep -v '^$' > "$PID_FILE"

echo
echo "⏳ Waiting for all services to initialize..."
sleep 5

echo
echo "=== Final Service Status ==="
check_service() {
    if check_port "$1"; then
        echo "✅ $2 (port $1)"
    else
        echo "❌ $2 (port $1)"
    fi
}

check_service 5000 "Blazor App"
check_service 8000 "API Server"
check_service 8080 "Llama Server"

echo
echo "=== Direct Access URLs ==="
echo "🌐 Blazor App: http://localhost:5000"
echo "🔧 API Server: http://localhost:8000"
echo "🧠 Llama Server: http://localhost:8080"

echo
echo "Services started without Caddy proxy."
echo "To stop: ./stop-services.sh"
echo
echo "Press Ctrl+C to exit (services will keep running)"

# Keep running
wait
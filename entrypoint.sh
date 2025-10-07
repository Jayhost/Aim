#!/bin/bash

# Set up environment
export PYTHONPATH="/app"

# Start searxng (web search server)
echo "Starting searxng..."
cd /app/searxng
python3 searxng.py --config /app/searxng/config.json --port 5000 &

# Start llama.cpp (as a Python wrapper)
# This assumes you have a GGUF model (e.g., llama-3-8b-instruct-q4_0.gguf) in /app/llama.cpp/models/
echo "Starting llama.cpp (LLM service)..."
cd /app/llama.cpp
python3 -m llama_cpp.server --model /app/llama.cpp/models/llama-3-8b-instruct-q4_0.gguf --port 8080 --host 0.0.0.0 &

# Wait for services to start
sleep 10

# Start Flask server to serve Blazor app and APIs
echo "Starting Flask server to serve Blazor app..."
cd /app/blazor-app
python3 -m flask run --host=0.0.0.0 --port=5000 --no-debugger

# This is the entry point for the container

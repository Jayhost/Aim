#!/bin/bash

echo "Starting Llama Server..."
echo

if [ ! -f "llama-server" ]; then
    echo "❌ llama-server not found"
    exit 1
fi

echo "Looking for model files..."
MODEL_FILES=(models/*.gguf)
if [ ${#MODEL_FILES[@]} -eq 0 ]; then
    echo "❌ No .gguf model files found in models/ folder"
    echo
    echo "Download a model file first, for example:"
    echo "wget -O models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \\"
    echo "  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    exit 1
fi

echo "Found models:"
for model in "${MODEL_FILES[@]}"; do
    echo "  - $(basename "$model")"
done

echo
echo "Using first model found..."
FIRST_MODEL="${MODEL_FILES[0]}"
echo "Starting with model: $(basename "$FIRST_MODEL")"
./llama-server --model "$FIRST_MODEL" --host 0.0.0.0 -ngl 99 --port 8080 --jinja
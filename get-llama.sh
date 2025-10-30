#!/bin/bash

echo "Downloading Llama.cpp..."
echo

echo "Downloading from:"
echo "https://github.com/ggml-org/llama.cpp/releases/download/b6719/llama-b6719-bin-linux-x64.tar.gz"
echo

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    ARCH="x64"
elif [ "$ARCH" = "aarch64" ]; then
    ARCH="arm64"
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

wget -O llama.tar.gz "https://github.com/ggml-org/llama.cpp/releases/download/b6719/llama-b6719-bin-linux-$ARCH.tar.gz"

if [ ! -f "llama.tar.gz" ]; then
    echo "❌ Download failed"
    exit 1
fi

echo "Extracting..."
tar -xzf llama.tar.gz

echo "Looking for server executable..."
if [ -f "server" ]; then
    echo "✅ Found server"
    mv server llama-server
    chmod +x llama-server
else
    # The files might be in a subdirectory
    if [ -f "bin/server" ]; then
        echo "Found in bin directory"
        mv bin/server llama-server
        chmod +x llama-server
    else
        echo "❌ Could not find server in the extracted files"
        echo "Contents:"
        ls -la
        exit 1
    fi
fi

echo
echo "✅ Llama server ready!"
echo "Cleanup..."
rm -f llama.tar.gz
rm -rf bin include lib share 2>/dev/null

echo
echo "Test the server:"
echo "./llama-server --host 0.0.0.0 --port 8080"
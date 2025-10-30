#!/bin/bash

echo "Installing Dependencies..."
cd "$(dirname "$0")"

echo "========================================"
echo "1. Checking Python..."
echo "========================================"
if ! command -v python3 &> /dev/null; then
    echo "Python not found. Please install Python manually:"
    echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "Arch: sudo pacman -S python python-pip"
    exit 1
else
    python3 --version
    echo "Installing Python dependencies..."
    pip3 install searxng fastapi uvicorn requests beautifulsoup4
fi

echo
echo "========================================"
echo "2. Checking Caddy..."
echo "========================================"
if ! command -v caddy &> /dev/null; then
    echo "Installing Caddy..."
    # Ubuntu/Debian
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
        sudo apt update
        sudo apt install caddy
    # CentOS/RHEL
    elif command -v yum &> /dev/null; then
        sudo yum install yum-utils
        sudo yum-config-manager --add-repo 'https://dl.cloudsmith.io/public/caddy/stable/rpm/linux/any-version/caddy-stable.repo'
        sudo yum install caddy
    # Arch
    elif command -v pacman &> /dev/null; then
        sudo pacman -S caddy
    else
        echo "Please install Caddy manually from: https://caddyserver.com/docs/install"
    fi
else
    echo "Caddy already installed."
    caddy version
fi

# echo
# echo "========================================"
# echo "3. Checking .NET..."
# echo "========================================"
# if ! command -v dotnet &> /dev/null; then
#     echo ".NET not found. We'll use standalone publish for Blazor app."
# else
#     dotnet --version
#     echo ".NET already installed."
# fi

# echo
# echo "========================================"
# echo "4. Setting up Llama.cpp..."
# echo "========================================"
# if [ ! -f "llama-server" ]; then
#     echo "Downloading Llama.cpp..."
    
#     # Detect architecture
#     ARCH=$(uname -m)
#     if [ "$ARCH" = "x86_64" ]; then
#         ARCH="x64"
#     elif [ "$ARCH" = "aarch64" ]; then
#         ARCH="arm64"
#     fi
    
#     # Download the binary
#     wget -O llama-bin.tar.gz "https://github.com/ggml-org/llama.cpp/releases/download/b6719/llama-b6719-bin-linux-$ARCH.tar.gz"
    
#     if [ -f "llama-bin.tar.gz" ]; then
#         echo "Extracting Llama.cpp binaries..."
#         tar -xzf llama-bin.tar.gz
        
#         # Look for the server executable
#         if [ -f "server" ]; then
#             mv server llama-server
#             chmod +x llama-server
#             echo "Llama server extracted successfully."
#         elif [ -f "bin/server" ]; then
#             mv bin/server llama-server
#             chmod +x llama-server
#             echo "Llama server extracted successfully."
#         else
#             echo "Searching for server executable in extracted files..."
#             find . -name "server" -type f
#         fi
        
#         # Clean up
#         rm -f llama-bin.tar.gz
#         rm -rf bin/ include/ lib/ share/ 2>/dev/null
        
#         if [ ! -f "llama-server" ]; then
#             echo "WARNING: Could not find server in the downloaded package."
#             echo "Please extract manually and rename server to llama-server"
#         fi
#     else
#         echo "Failed to download Llama.cpp package."
#         echo "Please download manually from:"
#         echo "https://github.com/ggml-org/llama.cpp/releases"
#     fi
# else
#     echo "Llama.cpp server already exists."
# fi

echo
echo "========================================"
echo "5. Creating project structure..."
echo "========================================"
mkdir -p models searxng api_server blazor-app

echo
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo "Next steps:"
if [ ! -f "llama-server" ]; then
    echo "1. MANUAL STEP: Download and extract llama-server"
    echo "   Get from: https://github.com/ggml-org/llama.cpp/releases"
fi
echo "1. Place your model file in models/ folder"
echo "2. Add SearXNG settings to searxng/ folder"  
echo "3. Add your API server code to api_server/"
echo "4. Add your Blazor app to blazor-app/"
echo
echo "Run ./start-services.sh to start all services"
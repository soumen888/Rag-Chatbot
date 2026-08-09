#!/usr/bin/env bash
# RAGChat Installer Script for macOS & Linux
# Installs RAGChat via Git clone or zip download, sets up Python virtualenv, installs dependencies, and creates a global 'ragchat' command.

set -e

REPO_URL="https://github.com/soumen888/Rag-Chatbot.git"
INSTALL_DIR="$HOME/.ragchat"
BIN_DIR="$HOME/.local/bin"

echo "=================================================="
echo "          RAGChat Universal Installer             "
echo "=================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is required but not installed."
    echo "    Please install Python 3.9+ and run this script again."
    exit 1
fi

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[+] Detected Python $PYTHON_VER"

# Clone or Update Repository
if [ -d "$INSTALL_DIR" ]; then
    echo "[*] Updating existing RAGChat installation in $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    if [ -d ".git" ]; then
        git pull --quiet
    fi
else
    echo "[*] Installing RAGChat to $INSTALL_DIR..."
    if command -v git &> /dev/null; then
        git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    else
        mkdir -p "$INSTALL_DIR"
        curl -fsSL https://github.com/soumen888/Rag-Chatbot/archive/refs/heads/main.tar.gz | tar -xz -C "$INSTALL_DIR" --strip-components=1
    fi
fi

cd "$INSTALL_DIR"

# Create Virtual Environment
echo "[*] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Dependencies
echo "[*] Installing required dependencies (LiteLLM, ChromaDB, etc.)..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Playwright Browsers setup
echo "[*] Setting up web crawler headless browser..."
python3 -m playwright install chromium --quiet || true

# Create executable launcher script
mkdir -p "$BIN_DIR"
LAUNCHER="$BIN_DIR/ragchat"

cat << 'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
INSTALL_DIR="$HOME/.ragchat"
if [ -d "$INSTALL_DIR" ]; then
    source "$INSTALL_DIR/venv/bin/activate"
    python3 "$INSTALL_DIR/main.py" "$@"
else
    echo "[!] RAGChat installation not found at $INSTALL_DIR"
    exit 1
fi
EOF

chmod +x "$LAUNCHER"

echo ""
echo "=================================================="
echo "        RAGChat Installed Successfully!           "
echo "=================================================="
echo ""
echo "You can now run RAGChat by typing:"
echo "  ragchat"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Note: Add $BIN_DIR to your PATH if 'ragchat' command is not recognized:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

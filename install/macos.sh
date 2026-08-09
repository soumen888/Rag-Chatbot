#!/usr/bin/env bash
# RAGChat Universal Installer for macOS & Linux
set -e

REPO_URL="https://github.com/soumen888/Rag-Chatbot.git"
INSTALL_DIR="$HOME/.ragchat"
BIN_DIR="$HOME/.local/bin"

echo "=================================================="
echo "          Installing RAGChat                      "
echo "=================================================="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is required. Download at: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 9 ]; then
    echo "[!] RAGChat requires Python 3.9+. Please upgrade at: https://www.python.org/downloads/"
    exit 1
fi

# 2. Download / Clone Repository
echo "[*] Downloading application packages..."
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    if [ -d ".git" ]; then
        git pull --quiet
    fi
else
    if command -v git &> /dev/null; then
        git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    else
        mkdir -p "$INSTALL_DIR"
        curl -# -L "https://github.com/soumen888/Rag-Chatbot/archive/refs/heads/main.tar.gz" | tar -xz -C "$INSTALL_DIR" --strip-components=1
    fi
fi

cd "$INSTALL_DIR"

# 3. Setup Virtual Environment & Install Dependencies with Progress
echo "[*] Setting up environment & dependencies..."
python3 -m venv venv
source venv/bin/activate

# Progress bar indicator during pip installation
pip install --upgrade pip --quiet
pip install -r requirements.txt --progress-bar on

# 4. Playwright Headless Setup
echo "[*] Setting up web crawler..."
python3 -m playwright install chromium > /dev/null 2>&1 || true

# 5. Global Command Link Setup
INSTALL_BIN="/usr/local/bin"
if [ ! -w "$INSTALL_BIN" ]; then
    INSTALL_BIN="$BIN_DIR"
    mkdir -p "$INSTALL_BIN"
fi

LAUNCHER="$INSTALL_BIN/ragchat"

cat << 'EOF' > "$LAUNCHER" 2>/dev/null || sudo cat << 'EOF' > "$LAUNCHER"
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

chmod +x "$LAUNCHER" 2>/dev/null || sudo chmod +x "$LAUNCHER"

# Persistent PATH addition
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    for PROFILE in "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.bashrc"; do
        if [ -f "$PROFILE" ] || [ "$(basename "$PROFILE")" = ".zshrc" ]; then
            if ! grep -q "$BIN_DIR" "$PROFILE" 2>/dev/null; then
                echo "" >> "$PROFILE"
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
            fi
        fi
    done
fi

echo ""
echo "=================================================="
echo "  [+] RAGChat installed successfully!             "
echo "  [+] Run command:  ragchat                       "
echo "=================================================="
echo ""


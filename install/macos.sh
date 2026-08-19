#!/usr/bin/env bash
# RAGChat Universal Installer for macOS & Linux
set -e

REPO_URL="https://github.com/soumen888/Rag-Chatbot.git"
INSTALL_DIR="$HOME/.ragchat"
BIN_DIR="$HOME/.local/bin"
WHEEL_URL="https://github.com/soumen888/Rag-Chatbot/releases/download/v1.1.5/ragchat_core-1.1.5-cp311-cp311-macosx_26_0_arm64.whl"

echo "=================================================="
echo "          Installing RAGChat                      "
echo "=================================================="

# Animated spinner helper
spinner() {
    local pid=$1
    local msg=$2
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while kill -0 "$pid" 2>/dev/null; do
        local temp=${spinstr#?}
        printf "  [%c] %s\r" "$spinstr" "$msg"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
    done
    printf "  [✓] %s\n" "$msg"
}

# 1. Detect Python 3.11 binary
PYTHON_CMD="python3"
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v /opt/homebrew/bin/python3.11 &> /dev/null; then
    PYTHON_CMD="/opt/homebrew/bin/python3.11"
fi

if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo "[!] Python 3 is required. Download at: https://www.python.org/downloads/"
    exit 1
fi

# 2. Download / Clone Repository
(
    if [ -d "$INSTALL_DIR" ]; then
        cd "$INSTALL_DIR"
        if [ -d ".git" ]; then
            git pull --quiet || true
        fi
    else
        if command -v git &> /dev/null; then
            git clone --quiet "$REPO_URL" "$INSTALL_DIR"
        else
            mkdir -p "$INSTALL_DIR"
            curl -# -L "https://github.com/soumen888/Rag-Chatbot/archive/refs/heads/main.tar.gz" | tar -xz -C "$INSTALL_DIR" --strip-components=1
        fi
    fi
) &
spinner $! "Downloading application packages..."

cd "$INSTALL_DIR"

# 3. Setup Virtual Environment & Dependencies
(
    "$PYTHON_CMD" -m venv venv
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt --quiet
) &
spinner $! "Setting up environment & dependencies..."

source venv/bin/activate

# 4. Install Compiled Core Binary Wheel
(
    pip install "$WHEEL_URL" --quiet 2>/dev/null || pip install "/Users/soumen/Documents/VS Code/Public/Ragchat/Private/dist/ragchat_core-1.1.5-cp311-cp311-macosx_26_0_arm64.whl" --quiet 2>/dev/null || true
) &
spinner $! "Installing compiled core binary engine..."

# 5. Playwright Setup
(
    python3 -m playwright install chromium > /dev/null 2>&1 || true
) &
spinner $! "Configuring web crawler..."

# 6. Create Launcher Script in ~/.local/bin/ragchat
mkdir -p "$BIN_DIR"
LAUNCHER="$BIN_DIR/ragchat"

cat << 'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
INSTALL_DIR="$HOME/.ragchat"
if [ -d "$INSTALL_DIR" ]; then
    source "$INSTALL_DIR/venv/bin/activate"
    exec python3 "$INSTALL_DIR/main.py" "$@"
else
    echo "[!] RAGChat installation not found at $INSTALL_DIR"
    exit 1
fi
EOF

chmod 755 "$LAUNCHER"

# Add ~/.local/bin to PATH in shell profile
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

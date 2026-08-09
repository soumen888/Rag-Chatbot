#!/usr/bin/env bash
# RAG Chat macOS / Linux Installer Script
set -e

echo "=================================================="
echo "          RAG Chat Installer                      "
echo "=================================================="

OS="$(uname -s)"
case "$OS" in
    Linux*)     ASSET="ragchat-linux-x64";;
    Darwin*)    ASSET="ragchat-macos-x64";;
    *)          echo "[!] Unsupported operating system: $OS"; exit 1;;
esac

DOWNLOAD_URL="https://github.com/soumen888/homebrew-ragchat/releases/latest/download/${ASSET}"
INSTALL_DIR="/usr/local/bin"

# Fallback to ~/.ragchat/bin if /usr/local/bin is not writable
if [ ! -w "$INSTALL_DIR" ]; then
    INSTALL_DIR="$HOME/.ragchat/bin"
    mkdir -p "$INSTALL_DIR"
    
    # Add to PATH in shell profile if needed
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        SHELL_PROFILE="$HOME/.bashrc"
        if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
            SHELL_PROFILE="$HOME/.zshrc"
        fi
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_PROFILE"
        echo "[*] Added $INSTALL_DIR to $SHELL_PROFILE"
    fi
fi

TARGET="$INSTALL_DIR/ragchat"

echo "[*] Downloading $ASSET..."
curl -fsSL "$DOWNLOAD_URL" -o "$TARGET"
chmod +x "$TARGET"

echo "=================================================="
echo "[+] RAG Chat installed successfully to $TARGET!"
echo "[+] Type 'ragchat' in your terminal to start."
echo "=================================================="

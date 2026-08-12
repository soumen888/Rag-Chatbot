## Installation

### Option 1: curl (macOS / Linux)

Run the one-liner installer in terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/soumen888/Rag-Chatbot/main/install/macos.sh | bash
```

Once installed, launch from anywhere:

```bash
ragchat
```

### Option 2: Homebrew (macOS / Linux)

```bash
brew install soumen888/ragchat/ragchat
```

Once installed, launch from anywhere:

```bash
ragchat
```

### Option 3: Manual Installation (Git & Python)

```bash
git clone https://github.com/soumen888/Rag-Chatbot.git
cd Rag-Chatbot
pip install -r requirements.txt
python3 main.py
```

## CLI Commands & Reference

For the complete reference guide of all available direct CLI commands (Google Drive, Gmail, Sheets, Outlook, OneDrive, Telegram, Discord, and time windows), check out the **[CLI Commands Reference Guide](commands.md)**.

## Uninstallation

### Uninstall curl installation:

```bash
rm -rf ~/.ragchat ~/.local/bin/ragchat /usr/local/bin/ragchat
```

### Uninstall Homebrew installation:

```bash
brew uninstall ragchat
brew untap soumen888/ragchat
```

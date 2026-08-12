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

### Option 2: PowerShell (Windows)

Run the one-liner installer in PowerShell:

```powershell
irm https://raw.githubusercontent.com/soumen888/Rag-Chatbot/main/install/windows.ps1 | iex
```

Once installed, restart PowerShell and launch from anywhere:

```powershell
ragchat
```

### Option 3: Homebrew (macOS / Linux)

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

### Uninstall macOS / Linux curl installation:

```bash
rm -rf ~/.ragchat ~/.local/bin/ragchat /usr/local/bin/ragchat
```

### Uninstall Windows PowerShell installation:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.ragchat"
```

### Uninstall Homebrew installation:

```bash
brew uninstall ragchat
brew untap soumen888/ragchat
```

---

## Supported Connections

RAGChat allows you to index and search across your personal and work workspace apps:

- **Google**: Gmail, Drive, Sheets, Docs, Tasks, and Calendar.
- **Microsoft**: Outlook Mail, OneDrive, Tasks, and Calendar.
- **Messaging**: Telegram channels/groups and Discord servers/DMs.
- **Web**: Website web crawling and documentation indexing.


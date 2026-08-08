# 🤖 RAG Chat

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **An intelligent terminal RAG companion for websites, Telegram channels, and Discord servers.** Crawls and embeds documentation sites, links stealth users or bots to index chat channels, and lets you chat with your local database using any cloud or local LLM.

---

## ⚡ Direct Installation (macOS)

The easiest way to install RAG Chat natively on macOS is via Homebrew:

```bash
# Install directly from the repository tap in a single command
brew install soumen888/Rag-Chatbot/ragchat
```

Once installed, simply run the following command in your terminal:
```bash
ragchat
```

---

## ✨ Key Features

- 🌐 **Web Crawler & Parser** — Recursively crawls documentation domains, auto-detects and extracts static/SPA content (Next.js/React/Vue) using Playwright only when necessary.
- 📱 **Telegram Syncing** — Connects via MTProto to import channels or chat histories into vector memory.
- 💬 **Discord Ingestion Engine** — Supports stealth user token authentication and official Developer Bot integrations to index server channels, skipping categories/voice interfaces.
- 📊 **24-Hour Summarizer** — Generates executive timeline summaries of chat activity over the past 24 hours.
- 🧠 **Privacy-First Search** — Embeds text locally using `all-MiniLM-L6-v2` and searches with ChromaDB. Your private data never leaves your machine.
- 🔌 **Plug-and-Play LLMs** — Works out-of-the-box with Gemini/Gemma, Ollama, LM Studio, Groq, OpenAI, and Anthropic.
- 🖥️ **Premium Terminal UI** — Live CPU/RAM/Storage panel resource monitor, rich Markdown chat rendering, and status loaders.

---

## ⚙️ Configuration (`.env`)

On first launch, if no `.env` file exists, RAG Chat will run a **Setup Wizard** to configure your LLM provider.

To manually configure your integrations, create a `.env` file in the root:

```env
# LLM Configuration
LLM_PROVIDER=google
LLM_API_KEY=your_google_ai_studio_api_key
LLM_MODEL=gemma-4-31b-it

# Telegram Credentials (from my.telegram.org)
TG_API_ID=12345678
TG_API_HASH=your_hash_here
TG_CHANNELS=@watcher_guru,https://t.me/cointelegraph
TG_INITIAL_LOOKBACK_DAYS=7

# Discord Settings (Guild IDs and Channels to auto-sync)
DISCORD_TARGETS=1234567890:9876543210
```

---

## 🚀 Manual Installation

If you prefer to run it manually using Python:

### macOS & Linux
```bash
# 1. Clone the repository
git clone https://github.com/soumen888/Rag-Chatbot.git
cd Rag-Chatbot

# 2. Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# 3. Launch RAG Chat
python main.py
```

### Windows
```powershell
git clone https://github.com/soumen888/Rag-Chatbot.git
cd Rag-Chatbot
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
python main.py
```

---

## 🔄 Background Syncing

To run the continuous sync daemon in the background to keep all your configured Telegram and Discord channels up-to-date:

```bash
python sync_daemon.py
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

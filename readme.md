# 🤖 Universal Documentation Chatbot (RAG)

[![Release](https://img.shields.io/github/v/release/soumen888/Rag-Chatbot?color=orange)](https://github.com/soumen888/Rag-Chatbot/releases)
[![CI Pipeline](https://github.com/soumen888/Rag-Chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/soumen888/Rag-Chatbot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Talk to any documentation website or Telegram channel using AI.** Crawls docs sites and indexes Telegram channels into a local vector database, then answers your questions using any cloud or local LLM — with exact source URL citations.

---

## ✨ Key Features

- 🌐 **Universal Web Crawler** — Point it at any documentation URL. Recursively crawls sub-pages, stays strictly on-domain, and filters out media assets.

- ⚡ **Adaptive JavaScript & SPA Engine** — Auto-detects if a site needs Playwright headless Chromium (React/Next.js/Vue) or fast `requests`. Uses Playwright only when needed.

- 📜 **Infinite Scroll & Lazy-Load Handling** — Scrolls and waits for network idle before extracting content, so nothing is missed.

- 💾 **Stateful Resume & Incremental Indexing** — Pause and resume crawls anytime. Skips already-visited pages automatically.

- 📱 **Telegram Channel Ingestion** — Connects via MTProto (Telethon). Accepts any channel username, invite link, or numeric Peer ID. Indexes historical messages into vector memory.

- 📊 **24-Hour Executive Digest** — Generates a structured AI summary of everything discussed in a Telegram channel over the past 24 hours, with clickable message links.

- 🔌 **Bring Your Own LLM (Cloud or Local)** — Switch between providers in `.env` without touching any code (see table below).

- 🧠 **Privacy-First Local Vector Search** — Embeddings are generated locally using `all-MiniLM-L6-v2` and stored in ChromaDB. Your content never leaves your machine.

- 🖥️ **Clean Interactive Terminal UI** — Modular menu with sub-sections, rich Markdown responses, and `back` navigation from any prompt.

---

## ⚙️ Supported LLM Providers

| Provider | `LLM_PROVIDER` | API Key Required? | Default Model |
|---|---|---|---|
| **Google AI Studio** *(Default)* | `google` | Yes | `gemma-4-31b-it` |
| **Ollama** *(Local)* | `ollama` | ❌ No | `llama3` |
| **LM Studio** *(Local)* | `lmstudio` | ❌ No | `local-model` |
| **OpenAI** | `openai` | Yes | `gpt-4o-mini` |
| **Groq Cloud** | `groq` | Yes | `llama-3.3-70b-versatile` |
| **Anthropic** | `anthropic` | Yes | `claude-3-5-sonnet-20241022` |
| **Together AI** | `together` | Yes | `meta-llama/Llama-3-8b-chat-hf` |
| **Mistral AI** | `mistral` | Yes | `mistral-small-latest` |
| **Custom OpenAI API** | `custom` | Optional | Set via `LLM_MODEL` & `LLM_BASE_URL` |

---

## 🚀 Quick Start

### Option A: Docker (Recommended — No Python Setup Required)

```bash
# 1. Clone the repo
git clone https://github.com/soumen888/Rag-Chatbot.git
cd Rag-Chatbot

# 2. Copy and configure your environment file
cp .env.example .env
# Edit .env with your API keys (see Configuration section below)

# 3. Build & run interactively
docker compose run --rm doc-chat
```

---

### Option B: Local Python Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/soumen888/Rag-Chatbot.git
cd Rag-Chatbot
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install Headless Browser (for JS/SPA sites)

```bash
python -m playwright install chromium
```

#### 4. Configure Environment

```bash
cp .env.example .env
```

Open `.env` and fill in your values (see **Configuration** below).

#### 5. Launch

```bash
python main.py
```

---

## ⚙️ Configuration (`.env`)

### Minimum Setup (Docs-only, no Telegram)

```env
LLM_PROVIDER=google
LLM_API_KEY=your_google_ai_studio_api_key
LLM_MODEL=gemma-4-31b-it
```

> Get a free Google AI Studio API key at [aistudio.google.com](https://aistudio.google.com)

### Adding Telegram Support

1. Get your Telegram API credentials at [my.telegram.org](https://my.telegram.org) → **API Development Tools**.

```env
TG_API_ID=12345678
TG_API_HASH=your_hash_here

# Channels to auto-sync (comma-separated: usernames, links, or numeric Peer IDs)
TG_CHANNELS=@python_news, https://t.me/tech_updates, 1234567890

# How many days of history to pre-fill for new channels (default: 7)
TG_INITIAL_LOOKBACK_DAYS=7

# Background sync interval in minutes (used by sync_daemon.py)
TG_SYNC_INTERVAL_MINUTES=30
```

> On first run, the app will prompt for your phone number and a one-time Telegram login code (input is hidden). After that, the session is cached locally and no further auth is needed.

---

## 💬 Usage Guide

When you run `python main.py`, the interactive menu appears:

```text
--- MAIN MENU ---
1. Website (Crawl & Embed)
2. Telegram (Index & 24h Summary)
3. Chat with Knowledge Base
4. Manage Collections (List & Delete)
5. Exit
```

### 1 — Website

- Enter any documentation base URL (e.g. `https://fastapi.tiangolo.com/`).
- The crawler auto-detects static vs JavaScript-rendered pages.
- Type `back` at any prompt to return to the main menu.

### 2 — Telegram

Sub-options:
- **Sync TG_CHANNELS** — Runs incremental sync on all channels configured in `.env`. Only new messages since the last sync are fetched.
- **Index a specific channel** — Enter any username, invite link, or Peer ID.
- **24-Hour Digest** — Get an AI-generated executive summary of the last 24 hours of any channel.

### 3 — Chat

Select any indexed collection (docs site or Telegram channel) and start asking questions. Every answer includes direct source URL citations or Telegram message links.

Type `back` or `exit` to return to the main menu from anywhere.

### 4 — Manage Collections

List or delete any indexed collection.

---

## 🔄 Background Sync Daemon (Optional)

To keep Telegram channels continuously up-to-date in the background:

```bash
python sync_daemon.py
```

This runs an infinite loop, syncing all `TG_CHANNELS` every `TG_SYNC_INTERVAL_MINUTES` minutes. Combine with Docker for a persistent background service:

```bash
docker compose up -d doc-chat-sync
```

---

## 🔒 Security & Privacy

| Protection | Status |
|---|---|
| `.env` excluded from git | ✅ `.gitignore` |
| Telegram `.session` files excluded from git | ✅ `.gitignore` |
| Embeddings generated 100% locally | ✅ Never sent to cloud |
| Crawler locked to base domain | ✅ Never follows external links |
| 2FA password & OTP hidden while typing | ✅ Uses `getpass` |
| Chunk deduplication across syncs | ✅ Content-hash IDs |

---

## 🤝 Contributing & PR Workflow

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. Commit your changes and push.
3. Open a **Pull Request** targeting the `main` branch.
4. All PRs must pass the **CI Pipeline** before merging.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

# 🤖 Universal Documentation Chatbot (RAG)

[![Release](https://img.shields.io/github/v/release/soumen888/Rag-Chatbot?color=orange)](https://github.com/soumen888/Rag-Chatbot/releases)
[![CI Pipeline](https://github.com/soumen888/Rag-Chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/soumen888/Rag-Chatbot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Talk to any documentation website using AI.** DocChat recursively crawls documentation sites, indexes them into a local vector database, and answers questions using any cloud or local LLM — complete with exact source URL citations.

---

## ✨ Key Features

- 🌐 **Universal Web Crawler**  
  Point it at any documentation URL. Automatically crawls sub-pages while staying strictly on-domain and filtering out media assets (`.pdf`, `.png`, `.zip`, etc.).

- ⚡ **Adaptive JavaScript & SPA Engine**  
  Auto-detects if a site requires client-side JavaScript (React, Next.js, Vue SPAs) or static HTML. Uses Playwright headless Chromium only when necessary to ensure maximum crawling speed without missing content.

- 📜 **Infinite Scroll & Lazy-Load Handling**  
  Automatically scrolls down pages and waits for network idle states to trigger lazy-loaded elements before extracting content.

- 💾 **Stateful Resume & Incremental Indexing**  
  Pause and resume crawl sessions anytime. Automatically skips already-visited pages to save time and bandwidth.

- 🔌 **Bring Your Own LLM (Cloud or Local)**  
  Switch seamlessly between models via `.env` without modifying any code:
  - **Cloud APIs**: Google AI Studio (Gemini/Gemma), OpenAI (GPT-4o), Groq, Together AI, Mistral AI, Anthropic (Claude).
  - **Local Models**: Ollama (`llama3`, `mistral`, `phi3`), LM Studio, or any custom OpenAI-compatible endpoint.

- 🧠 **Privacy-First Local Vector Search**  
  Text embeddings are generated 100% locally using `sentence-transformers/all-MiniLM-L6-v2` and stored in a persistent local ChromaDB instance. Your documentation content never leaves your machine.

- 📖 **Transparent Source Citations**  
  Every generated answer ends with clickable, direct source URLs so you can verify answers against the official documentation.

- 🖥️ **Rich Interactive Terminal Interface**  
  Features an interactive CLI menu with syntax-highlighted Markdown responses, formatted headers, and clean layout using `rich`.

---

## ⚙️ Supported LLM Providers

| Provider | `LLM_PROVIDER` | API Key Required? | Default / Example Model |
|---|---|---|---|
| **Google AI Studio** *(Default)* | `google` | Yes | `gemma-4-31b-it`, `gemini-2.0-flash` |
| **Ollama** *(Local)* | `ollama` | ❌ No | `llama3`, `mistral`, `codellama` |
| **LM Studio** *(Local)* | `lmstudio` | ❌ No | `local-model` |
| **OpenAI** | `openai` | Yes | `gpt-4o-mini`, `gpt-4o` |
| **Groq Cloud** | `groq` | Yes | `llama-3.3-70b-versatile` |
| **Anthropic** | `anthropic` | Yes | `claude-3-5-sonnet-20241022` |
| **Together AI** | `together` | Yes | `meta-llama/Llama-3-8b-chat-hf` |
| **Mistral AI** | `mistral` | Yes | `mistral-small-latest` |
| **Custom OpenAI API** | `custom` | Optional | Set via `LLM_MODEL` & `LLM_BASE_URL` |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/soumen888/Rag-Chatbot.git
cd Rag-Chatbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Headless Browser (for JS/SPA Crawling)

```bash
python -m playwright install chromium
```

### 4. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` to select your preferred provider and add your API key:

```env
LLM_PROVIDER=google
LLM_API_KEY=your_api_key_here
LLM_MODEL=gemma-4-31b-it
```

*(If using **Ollama** or **LM Studio**, set `LLM_PROVIDER=ollama` — no API key required!)*

### 5. Launch the Application

```bash
python main.py
```

---

## 💬 Usage Guide

When you run `python main.py`, an interactive menu appears:

```text
--- MENU ---
1. Index a new documentation site (Crawl & Embed)
2. Chat with an indexed documentation site
3. List all indexed documentation sites
4. Delete an indexed documentation site
5. Exit
```

1. **Option 1**: Enter any documentation URL (e.g. `https://fastapi.tiangolo.com/` or `https://docs.slack.dev/`).
2. **Option 2**: Select an indexed documentation database and ask any question!

---

## 🔒 Security & Privacy

- 🛡️ **API Key Safety**: `.env` is listed in `.gitignore` to prevent secret leaks.
- 🔒 **Local Vector Data**: All website text chunk embeddings are generated locally. Documentation content is never sent to third-party embedding services.
- 🔒 **Domain Lockdown**: The crawler will never traverse links outside the base URL domain.

---

## 🤝 Contributing & PR Workflow

Contributions are welcome! Please follow these steps:

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. Commit your changes and push to your fork.
3. Open a **Pull Request** targeting the `main` branch.
4. All PRs must pass the **CI Pipeline verification checks** before merging.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

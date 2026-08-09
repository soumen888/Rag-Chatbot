# Universal Documentation & Community Chatbot (RAGChat)

An intelligent terminal-based RAG assistant that ingests technical documentation, Telegram channels, and Discord communities to answer your questions with precise citations.

---

## 🚀 Quick Start & Installation

### Option 1: For Non-Tech Users (`curl` One-Liner)

Simply paste this single command into your macOS or Linux terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/soumen888/Rag-Chatbot/main/install.sh | bash
```

Once installed, you can launch RAGChat from anywhere by typing:
```bash
ragchat
```

---

### Option 2: For Developers & Tech Users (Homebrew)

If you use Homebrew on macOS or Linux:

```bash
brew tap soumen888/tap
brew install ragchat
```

---

### Option 3: Manual Installation (Git & Python)

```bash
# 1. Clone repo
git clone https://github.com/soumen888/Rag-Chatbot.git
cd Rag-Chatbot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run application
python3 main.py
```

---

## ⚡ Features

- **LiteLLM Engine**: Works out-of-the-box with **Google Gemini**, OpenAI GPT-4, Anthropic Claude, Groq, Together AI, Mistral, and local models via Ollama / LM Studio.
- **Persistent Vector DB**: Uses ChromaDB stored locally in `./ragchat_db` so your collections and embeddings persist across restarts.
- **Multi-Source Ingestion**: Web crawling with Playwright, Telegram channels via Telethon, and Discord server messages.
- **Real-Time Context**: Includes time-aware prompt handling for relative date context.

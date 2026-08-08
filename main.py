import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

# Load variables from .env file relative to this script
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from website import DocCrawler
from telegram import TelegramIngestor
from core import DocChunker, VectorDB, get_provider, PROVIDER_INFO
from urllib.parse import urlparse

def print_banner():
    banner = """
==================================================
        Universal Documentation Chat (RAG)        
==================================================
    """
    print(banner)

def format_col_display(col_name):
    """Formats a ChromaDB collection name for display in menus."""
    if col_name == "telegram_all":
        return "Telegram: All Channels (telegram_all)"
    elif col_name.startswith("tg_"):
        raw_name = col_name[3:].replace("_", " ").title()
        return f"Telegram: {raw_name} ({col_name})"
    else:
        return f"Docs: {col_name}"

def init_llm_provider():
    """Initialize the LLM provider from env vars. Returns provider or None on failure."""
    provider_name = os.environ.get("LLM_PROVIDER", "google").lower().strip()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "").strip()

    info = PROVIDER_INFO.get(provider_name, {})
    provider_display = info.get("name", provider_name)
    local_providers = {"ollama", "lmstudio"}

    if provider_name not in local_providers and not api_key:
        print(f"[!] LLM_API_KEY not set in .env for provider '{provider_display}'.")
        api_key = input("Enter your API key: ").strip()
        if not api_key:
            print("[!] API key is required. Set LLM_API_KEY in your .env file.")
            return None
        os.environ["LLM_API_KEY"] = api_key

    if model:
        os.environ["LLM_MODEL"] = model
    if base_url:
        os.environ["LLM_BASE_URL"] = base_url

    try:
        provider = get_provider()
        effective_model = model or info.get("model_default", "")
        print(f"[+] LLM Provider: {provider_display} | Model: {effective_model}")
        return provider
    except Exception as e:
        print(f"[!] Failed to initialize LLM provider: {e}")
        print("[!] Check your LLM_PROVIDER, LLM_API_KEY and LLM_MODEL in .env")
        return None

def handle_website_menu(db):
    print("\n--- WEBSITE MENU ---")
    print("1. Crawl & Index a new documentation site")
    print("2. Back to main menu")
    
    sub = input("\nSelect option (1-2): ").strip()
    if sub != "1":
        return

    url = input("Enter documentation base URL (or type 'back' to cancel): ").strip()
    if not url or url.lower() in ["back", "b"]:
        return
        
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        print("[!] Invalid URL scheme or domain.")
        return
        
    collection_name = parsed.netloc
    safe_col_name = db.sanitize_collection_name(collection_name)
    
    cache_dir = "./.crawl_cache"
    cache_file = os.path.join(cache_dir, f"{safe_col_name}.json")
    
    resume = False
    if os.path.exists(cache_file):
        print(f"\n[!] Found previous crawl state for '{safe_col_name}'.")
        print("1. Resume crawling (crawl new pages, append to database)")
        print("2. Start fresh (delete existing collection & cache, crawl from scratch)")
        print("3. Back to main menu")
        sub_choice = input("Select option (1-3, default 1): ").strip()
        if sub_choice == "3" or sub_choice.lower() in ["back", "b"]:
            return
        elif sub_choice == "2":
            print(f"[*] Deleting existing collection and cache for '{safe_col_name}'...")
            db.delete_collection(collection_name)
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                except Exception:
                    pass
        else:
            resume = True
    
    max_pages_input = input("Max pages to crawl this session (default 50): ").strip()
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else 50
    
    crawler = DocCrawler(base_url=url, max_pages=max_pages)
    if resume:
        crawler.load_state(cache_file)
        
    pages = crawler.crawl()
    
    if not pages:
        print("[!] No new pages crawled this session.")
        if resume:
            crawler.save_state(cache_file)
        return
        
    print("[*] Parsing and chunking HTML content...")
    chunker = DocChunker()
    chunks = chunker.process_pages(pages)
    print(f"[+] Created {len(chunks)} chunks from {len(pages)} new pages.")
    
    db.add_chunks(collection_name, chunks)
    crawler.save_state(cache_file)
    print(f"[+] Collection '{safe_col_name}' is ready to chat!")

def handle_telegram_menu(db, chatbot):
    print("\n--- TELEGRAM MENU ---")
    configured_chs = os.environ.get("TG_CHANNELS", "")
    print(f"1. Sync configured TG_CHANNELS from .env [{configured_chs}]")
    print("2. Index a specific Telegram channel (by username/link/Peer ID)")
    print("3. Generate 24-Hour Channel Catch-Up Digest")
    print("4. Back to main menu")
    
    sub = input("\nSelect option (1-4): ").strip()

    ingestor = TelegramIngestor()
    chunker = DocChunker()

    if sub == "1":
        try:
            ingestor.sync_configured_channels(db, chunker)
        except Exception as e:
            print(f"[!] Batch sync failed: {e}")
            
    elif sub == "2":
        channel_input = input("Enter Telegram channel username/link/Peer ID (or type 'back'): ").strip()
        if not channel_input or channel_input.lower() in ["back", "b"]:
            return
            
        limit_input = input("Max messages to fetch (default 500): ").strip()
        limit = int(limit_input) if limit_input.isdigit() else 500

        try:
            messages, peer_id, channel_title = ingestor.fetch_messages(channel_input, limit=limit)
            if messages:
                safe_title = db.sanitize_collection_name(channel_title)
                collection_name = f"tg_{safe_title}"
                chunks = chunker.process_telegram_messages(messages)
                db.add_chunks(collection_name, chunks)
                print(f"[+] Telegram channel '{channel_title}' indexed into collection '{db.sanitize_collection_name(collection_name)}' successfully!")
        except Exception as e:
            print(f"[!] Telegram indexing failed: {e}")
            
    elif sub == "3":
        channel_input = input("Enter Telegram channel username/link/Peer ID (or type 'back'): ").strip()
        if not channel_input or channel_input.lower() in ["back", "b"]:
            return

        try:
            messages, peer_id, channel_title = ingestor.fetch_messages(channel_input, hours=24)
            
            if not messages:
                print(f"[!] No messages found in '{channel_title}' within the last 24 hours.")
                return

            if not chatbot:
                chatbot = init_llm_provider()
            if not chatbot:
                print("[!] Cannot generate digest without an active LLM provider.")
                return chatbot

            messages_context = "\n".join([
                f"[{m['date_str']}] {m['sender']}: {m['text']} (Link: {m['link']})"
                for m in reversed(messages)
            ])

            print(f"[*] Generating 24-hour digest for '{channel_title}' using LLM...")
            fake_chunk = [{
                "text": messages_context,
                "metadata": {"source": f"Telegram @{channel_title}", "title": f"24h Digest for {channel_title}"}
            }]
            answer = chatbot.generate_answer("Provide an executive 24-hour catch-up digest of this channel activity.", fake_chunk)
            
            console = Console()
            print(f"\n24-Hour Digest for '{channel_title}':")
            console.print(Markdown(answer))
            print()
        except Exception as e:
            print(f"[!] Failed to generate 24h digest: {e}")

    return chatbot

def handle_chat_menu(db, chatbot):
    collections = db.list_collections()
    if not collections:
        print("[!] No indexed collections found. Please index a website or Telegram channel first.")
        return chatbot
        
    print("\nAvailable indexed collections:")
    print("0. Back to main menu")
    for idx, col in enumerate(collections):
        print(f"{idx + 1}. {format_col_display(col)}")
        
    sel = input(f"Select a collection to chat (0-{len(collections)}): ").strip()
    if sel == "0" or sel.lower() in ["back", "b"]:
        return chatbot
    if not sel.isdigit() or int(sel) < 1 or int(sel) > len(collections):
        print("[!] Invalid selection.")
        return chatbot
        
    selected_collection = collections[int(sel) - 1]
    print(f"\n[+] Started chat session with '{format_col_display(selected_collection)}'")
    print("Type 'exit' or 'back' to return to the main menu.\n")
    
    if not chatbot:
        chatbot = init_llm_provider()
    if not chatbot:
        print("[!] Cannot start chat without a configured LLM provider.")
        return chatbot
            
    while True:
        user_query = input("You: ").strip()
        if not user_query:
            continue
        if user_query.lower() in ["exit", "back", "b"]:
            break
            
        print("[*] Searching vector database...")
        results = db.query(selected_collection, user_query, n_results=10)
        
        if not results:
            print("Bot: No relevant context found in database.")
            continue
            
        print("[*] Generating answer from LLM...")
        answer = chatbot.generate_answer(user_query, results)
        console = Console()
        print("\nBot:")
        console.print(Markdown(answer))
        print()

    return chatbot

def handle_collections_menu(db):
    print("\n--- COLLECTIONS MENU ---")
    print("1. List all indexed collections")
    print("2. Delete an indexed collection")
    print("3. Back to main menu")
    
    sub = input("\nSelect option (1-3): ").strip()
    
    if sub == "1":
        collections = db.list_collections()
        if not collections:
            print("[!] No indexed collections found.")
        else:
            print("\nIndexed collections:")
            for col in collections:
                print(f"- {format_col_display(col)}")
                
    elif sub == "2":
        collections = db.list_collections()
        if not collections:
            print("[!] No indexed collections found.")
            return
            
        print("\nAvailable indexed collections:")
        print("0. Back to main menu")
        for idx, col in enumerate(collections):
            print(f"{idx + 1}. {format_col_display(col)}")
            
        sel = input(f"Select a collection to delete (0-{len(collections)}): ").strip()
        if sel == "0" or sel.lower() in ["back", "b"]:
            return
        if not sel.isdigit() or int(sel) < 1 or int(sel) > len(collections):
            print("[!] Invalid selection.")
            return
            
        col_to_delete = collections[int(sel) - 1]
        confirm = input(f"Are you sure you want to delete '{format_col_display(col_to_delete)}'? (y/n): ").strip().lower()
        if confirm == 'y':
            db.delete_collection(col_to_delete)
            cache_file = os.path.join("./.crawl_cache", f"{col_to_delete}.json")
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                except Exception:
                    pass

def main():
    print_banner()
    
    db = VectorDB()
    chatbot = init_llm_provider()
    
    while True:
        print("\n--- MAIN MENU ---")
        print("1. Website (Crawl & Embed)")
        print("2. Telegram (Index & 24h Summary)")
        print("3. Chat with Knowledge Base")
        print("4. Manage Collections (List & Delete)")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == "1":
            handle_website_menu(db)
        elif choice == "2":
            chatbot = handle_telegram_menu(db, chatbot)
        elif choice == "3":
            chatbot = handle_chat_menu(db, chatbot)
        elif choice == "4":
            handle_collections_menu(db)
        elif choice == "5":
            print("Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Please select between 1 and 5.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)

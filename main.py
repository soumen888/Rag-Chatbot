import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown


# Load variables from .env file relative to this script
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from crawler import DocCrawler
from chunker import DocChunker
from vector_db import VectorDB
from chatbot import get_provider, PROVIDER_INFO
from urllib.parse import urlparse

def print_banner():
    banner = """
==================================================
        Universal Documentation Chat (RAG)        
==================================================
    """
    print(banner)

def init_llm_provider():
    """Initialize the LLM provider from env vars. Returns provider or None on failure."""
    provider_name = os.environ.get("LLM_PROVIDER", "google").lower().strip()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "").strip()

    info = PROVIDER_INFO.get(provider_name, {})
    provider_display = info.get("name", provider_name)
    local_providers = {"ollama", "lmstudio"}

    # For cloud providers, prompt for API key if missing
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

def main():
    print_banner()
    
    # Initialize DB (downloads embedding model on startup)
    db = VectorDB()
    
    # Initialize LLM provider
    chatbot = init_llm_provider()
    
    while True:
        print("\n--- MENU ---")
        print("1. Index a new documentation site (Crawl & Embed)")
        print("2. Chat with an indexed documentation site")
        print("3. List all indexed documentation sites")
        print("4. Delete an indexed documentation site")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == "1":
            url = input("Enter documentation base URL (e.g., https://fastapi.tiangolo.com/): ").strip()
            if not url:
                print("[!] Invalid URL.")
                continue
                
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                print("[!] Invalid URL scheme or domain.")
                continue
                
            collection_name = parsed.netloc
            safe_col_name = db.sanitize_collection_name(collection_name)
            
            # Setup cache path
            cache_dir = "./.crawl_cache"
            cache_file = os.path.join(cache_dir, f"{safe_col_name}.json")
            
            resume = False
            if os.path.exists(cache_file):
                print(f"\n[!] Found previous crawl state for '{safe_col_name}'.")
                print("1. Resume crawling (crawl new pages, append to database)")
                print("2. Start fresh (delete existing collection & cache, crawl from scratch)")
                sub_choice = input("Select option (1 or 2, default 1): ").strip()
                if sub_choice == "2":
                    print(f"[*] Deleting existing collection and cache for '{safe_col_name}'...")
                    db.delete_collection(collection_name)
                    if os.path.exists(cache_file):
                        try:
                            os.remove(cache_file)
                        except Exception:
                            pass
                else:
                    resume = True
            
            # Ask for custom crawl limits or use defaults
            max_pages_input = input("Max pages to crawl this session (default 50): ").strip()
            max_pages = int(max_pages_input) if max_pages_input.isdigit() else 50
            
            # Start Crawling
            crawler = DocCrawler(base_url=url, max_pages=max_pages)
            if resume:
                crawler.load_state(cache_file)
                
            pages = crawler.crawl()
            
            if not pages:
                print("[!] No new pages crawled this session.")
                if resume:
                    crawler.save_state(cache_file)
                continue
                
            # Chunking
            print("[*] Parsing and chunking HTML content...")
            chunker = DocChunker()
            chunks = chunker.process_pages(pages)
            print(f"[+] Created {len(chunks)} chunks from {len(pages)} new pages.")
            
            # Store in DB (Appends new chunks automatically)
            db.add_chunks(collection_name, chunks)
            
            # Save crawl state
            crawler.save_state(cache_file)
            print(f"[+] Collection '{safe_col_name}' is ready to chat!")
            
        elif choice == "2":
            collections = db.list_collections()
            if not collections:
                print("[!] No indexed sites found. Please index a site first (Option 1).")
                continue
                
            print("\nAvailable indexed sites:")
            for idx, col in enumerate(collections):
                print(f"{idx + 1}. {col}")
                
            sel = input(f"Select a site to chat (1-{len(collections)}): ").strip()
            if not sel.isdigit() or int(sel) < 1 or int(sel) > len(collections):
                print("[!] Invalid selection.")
                continue
                
            selected_collection = collections[int(sel) - 1]
            print(f"\n[+] Started chat session with '{selected_collection}'")
            print("Type 'exit' or 'back' to return to the main menu.\n")
            
            # Ensure provider is initialized
            if not chatbot:
                chatbot = init_llm_provider()
            if not chatbot:
                print("[!] Cannot start chat without a configured LLM provider.")
                print("[!] Set LLM_PROVIDER and LLM_API_KEY in your .env file.")
                continue
                    
            while True:
                user_query = input("You: ").strip()
                if not user_query:
                    continue
                if user_query.lower() in ["exit", "back"]:
                    break
                    
                # Retrieve from ChromaDB
                print("[*] Searching vector database...")
                results = db.query(selected_collection, user_query, n_results=10)
                
                if not results:
                    print("Bot: No relevant context found in database.")
                    continue
                    
                # Generate Answer
                print("[*] Generating answer from Gemini API...")
                answer = chatbot.generate_answer(user_query, results)
                console = Console()
                print("\nBot:")
                console.print(Markdown(answer))
                print()
                
        elif choice == "3":
            collections = db.list_collections()
            if not collections:
                print("[!] No indexed sites found.")
            else:
                print("\nIndexed sites:")
                for col in collections:
                    print(f"- {col}")
                    
        elif choice == "4":
            collections = db.list_collections()
            if not collections:
                print("[!] No indexed sites found.")
                continue
                
            print("\nAvailable indexed sites:")
            for idx, col in enumerate(collections):
                print(f"{idx + 1}. {col}")
                
            sel = input(f"Select a site to delete (1-{len(collections)}): ").strip()
            if not sel.isdigit() or int(sel) < 1 or int(sel) > len(collections):
                print("[!] Invalid selection.")
                continue
                
            col_to_delete = collections[int(sel) - 1]
            confirm = input(f"Are you sure you want to delete '{col_to_delete}'? (y/n): ").strip().lower()
            if confirm == 'y':
                db.delete_collection(col_to_delete)
                # Clean up cache file
                cache_file = os.path.join("./.crawl_cache", f"{col_to_delete}.json")
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except Exception:
                        pass
                
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

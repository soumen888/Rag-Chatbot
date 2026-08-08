import os
import sys
import psutil
from dotenv import load_dotenv
from rich.console import Console

# Load variables from .env file relative to this script
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from core import (
    VectorDB,
    ConfigManager,
    handle_website_menu,
    handle_telegram_menu,
    handle_discord_menu,
    handle_chat_menu,
    handle_collections_menu,
    handle_settings_menu,
    interactive_setup_wizard,
    init_llm_provider_wrapper
)

def get_dir_size(path):
    total = 0
    try:
        if os.path.exists(path):
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(entry.path)
    except Exception:
        pass
    return total

def print_system_stats():
    """Returns process CPU, RAM, and vector database size formatted string."""
    try:
        process = psutil.Process(os.getpid())
        process_mem = process.memory_info().rss / (1024 * 1024) # MB
        total_mem = psutil.virtual_memory().total / (1024 * 1024 * 1024) # GB
        mem_percent = psutil.virtual_memory().percent
        cpu_percent = process.cpu_percent(interval=None)
        db_size = get_dir_size("./chroma_db") / (1024 * 1024) # MB
        
        return (
            f"RAM: {process_mem:.1f} MB (System: {total_mem:.1f} GB, {mem_percent}%) | "
            f"CPU: {cpu_percent:.1f}% | "
            f"DB Storage: {db_size:.2f} MB"
        )
    except Exception:
        return "System resource details unavailable"

def print_banner():
    # ANSI escape code to clear terminal screen and move cursor to top-left (0,0)
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()

    stats_str = print_system_stats()
    
    console = Console()
    console.print("[bold cyan]========================================================================[/bold cyan]")
    console.print("[bold white]                   Universal Documentation Chat (RAG)                  [/bold white]")
    console.print(f"[dim]  {stats_str}  [/dim]")
    console.print("[bold cyan]========================================================================[/bold cyan]")

def main():
    print_banner()
    cfg = ConfigManager()
    
    # Run setup wizard if no LLM configured
    if not os.environ.get("LLM_PROVIDER") or not os.environ.get("LLM_API_KEY") and os.environ.get("LLM_PROVIDER") not in ["ollama", "lmstudio"]:
        interactive_setup_wizard(cfg)
        # Reload environment
        load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'), override=True)

    db = VectorDB()
    chatbot = init_llm_provider_wrapper()
    
    while True:
        print("\n--- MAIN MENU ---")
        print("1. Website (Crawl & Embed)")
        print("2. Telegram (Index & 24h Summary)")
        print("3. Discord (Index & 24h Summary)")
        print("4. Chat with Knowledge Base")
        print("5. Manage Collections (List & Delete)")
        print("6. Settings & Account Connections")
        print("7. Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        if choice == "1":
            handle_website_menu(db)
        elif choice == "2":
            chatbot = handle_telegram_menu(db, chatbot, cfg)
        elif choice == "3":
            chatbot = handle_discord_menu(db, chatbot, cfg)
        elif choice == "4":
            chatbot = handle_chat_menu(db, chatbot)
        elif choice == "5":
            handle_collections_menu(db)
        elif choice == "6":
            handle_settings_menu(cfg)
        elif choice == "7":
            print("Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Please select between 1 and 7.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)

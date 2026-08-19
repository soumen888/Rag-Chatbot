import os
import sys
from dotenv import load_dotenv

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
from main.stats import print_banner
from main.cli import handle_cli_commands

def run_app():
    # Handle direct CLI flags first
    if handle_cli_commands():
        return
        
    print_banner()
    cfg = ConfigManager()
    
    # Run setup wizard if no LLM configured and not explicitly skipped
    llm_provider = os.environ.get("LLM_PROVIDER")
    if not llm_provider:
        # Prompt option to configure, but don't force blocking wizard if they want to skip
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

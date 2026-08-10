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
        db_size = get_dir_size("./ragchat_db") / (1024 * 1024) # MB
        
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

def parse_time_window(window_str):
    """Parses time window strings like '10h', '2d', '1w', '1m' to epoch offset."""
    import re
    import time
    match = re.match(r"^(\d+)([hdwmy])$", window_str.lower().strip())
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    
    seconds = 0
    if unit == 'h':
        seconds = value * 3600
    elif unit == 'd':
        seconds = value * 86400
    elif unit == 'w':
        seconds = value * 86400 * 7
    elif unit == 'm':
        seconds = value * 86400 * 30
    elif unit == 'y':
        seconds = value * 86400 * 365
        
    return int(time.time() - seconds)

def handle_cli_commands():
    """Handles structured non-interactive CLI commands (e.g., ragchat -g dev 10h)."""
    import sys
    import time
    from core.sync import GoogleSyncEngine
    from core.db import LocalDB
    from rich.table import Table
    
    args = sys.argv[1:]
    if not args:
        return False
        
    # Example: -g dev 10h
    if args[0] == '-g':
        if len(args) < 3:
            print("[!] Usage: python main.py -g <profile_name> <time_window> (e.g., -g dev 10h)")
            sys.exit(1)
            
        profile_name = args[1]
        time_window_str = args[2]
        
        since_timestamp = parse_time_window(time_window_str)
        if since_timestamp is None:
            print(f"[!] Invalid time window format: '{time_window_str}'. Use format like '10h', '2d', '1w'.")
            sys.exit(1)
            
        # 1. Sync recent emails first
        sync_engine = GoogleSyncEngine()
        print(f"[*] Syncing recent emails for '{profile_name}'...")
        sync_engine.sync_gmail(profile_name)
        
        # 2. Query local SQLite
        db_conn = LocalDB()
        emails = db_conn.get_emails(profile_name, since_timestamp=since_timestamp, limit=100)
        
        if not emails:
            print(f"[-] No emails found for profile '{profile_name}' in the last {time_window_str}.")
            sys.exit(0)
            
        # 3. Print formatted table using Rich
        console = Console()
        table = Table(title=f"Emails for '{profile_name}' (Last {time_window_str})", show_lines=True)
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("From", style="green")
        table.add_column("Subject", style="magenta")
        table.add_column("Snippet", style="white")
        
        for email_data in emails:
            # Shorten date for readable formatting
            dt_str = email_data['date']
            if len(dt_str) > 16:
                dt_str = dt_str[:16].replace('T', ' ')
            
            from_str = f"{email_data['sender_name']} <{email_data['sender']}>" if email_data['sender_name'] else email_data['sender']
            table.add_row(dt_str, from_str, email_data['subject'], email_data['snippet'])
            
        console.print(table)
        sys.exit(0)
        
    return False

def main():
    # Handle direct CLI flags first
    if handle_cli_commands():
        return
        
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

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

def show_help_menu():
    """Displays a clean, standard developer CLI help guide."""
    console = Console()
    
    # Title
    console.print("[bold cyan]ragchat[/bold cyan] - Universal Documentation & Workspace Chatbot\n")
    console.print("[bold white]USAGE:[/bold white]")
    console.print("  ragchat <command> [arguments]\n")
    
    console.print("[bold white]CORE COMMANDS:[/bold white]")
    console.print("  [bold green]-g <profile> <time>[/bold green]         Sync and list emails from a Google profile (zero LLM cost)")
    console.print("  [bold green]-m <profile> <time>[/bold green]         Sync and list emails from a Microsoft profile (zero LLM cost)")
    console.print("  [bold green]link <service> <profile>[/bold green]   Link a new account profile (google, microsoft, telegram, discord)")
    console.print("  [bold green]chat <collection>[/bold green]          Start interactive chat with an ingested collection")
    console.print("  [bold green]sync[/bold green]                        Run full sync daemon on connected channels")
    console.print("  [bold green]help[/bold green]                        Show this help usage menu\n")
    
    console.print("[bold white]TIME WINDOW FORMATS:[/bold white]")
    console.print("  Provide values like [cyan]10h[/cyan], [cyan]2d[/cyan], [cyan]1w[/cyan], [cyan]3m[/cyan], [cyan]1y[/cyan] where:")
    console.print("  [bold yellow]h[/bold yellow] : Hours    [bold yellow]d[/bold yellow] : Days    [bold yellow]w[/bold yellow] : Weeks    [bold yellow]m[/bold yellow] : Months (30 days)    [bold yellow]y[/bold yellow] : Years (365 days)\n")
    
    console.print("[bold white]EXAMPLES:[/bold white]")
    console.print("  ragchat -g dev 10h                # List dev Gmail emails from last 10 hours")
    console.print("  ragchat link google dev           # Authenticate and link a new Google account named 'dev'")
    console.print("  ragchat link telegram personal    # Connect a Telegram account named 'personal'")
    console.print("  ragchat chat work_docs            # Start chatting with the work_docs collection")
    console.print("  ragchat                           # Launch the interactive text menu\n")

def handle_cli_commands():
    """Handles structured non-interactive CLI commands (e.g., ragchat -g dev 10h)."""
    import sys
    import time
    import getpass
    from core.sync import GoogleSyncEngine, MicrosoftSyncEngine
    from core.db import LocalDB
    from Google.auth import GoogleAuthManager
    from Google.client import GoogleClient
    from microsoft.auth import MicrosoftAuthManager
    from telegram.ingestor import TelegramIngestor
    from core.config_manager import ConfigManager
    from core.menu_handlers import db_safe_profile_name
    from rich.table import Table
    
    args = sys.argv[1:]
    if not args:
        return False
        
    if args[0] in ['-h', '--help', 'help']:
        show_help_menu()
        sys.exit(0)

    # Example: link google dev
    if args[0] == 'link':
        if len(args) < 3:
            print("[!] Usage: ragchat link <service> <profile_name> (e.g. link google dev)")
            sys.exit(1)
        
        service = args[1].lower()
        profile_name = args[2]
        cfg = ConfigManager()

        if service == 'google':
            try:
                g_manager = GoogleAuthManager()
                g_manager.authenticate_profile(profile_name)
                print(f"[+] Google profile '{profile_name}' successfully linked!")
            except Exception as e:
                print(f"[!] Google authorization failed: {e}")
            sys.exit(0)

        elif service == 'microsoft':
            try:
                ms_manager = MicrosoftAuthManager()
                ms_manager.authenticate_profile(profile_name)
                print(f"[+] Microsoft profile '{profile_name}' successfully linked!")
            except Exception as e:
                print(f"[!] Microsoft authorization failed: {e}")
            sys.exit(0)

        elif service == 'telegram':
            session_file = f"tg_session_{db_safe_profile_name(profile_name)}"
            ingestor = TelegramIngestor(
                api_id=ConfigManager.DEFAULT_TG_API_ID,
                api_hash=ConfigManager.DEFAULT_TG_API_HASH,
                session_name=session_file
            )
            try:
                ingestor.connect()
                cfg.add_tg_profile(profile_name, session_file)
                print(f"[+] Telegram profile '{profile_name}' successfully connected!")
            except Exception as e:
                print(f"[!] Authorization failed: {e}")
            sys.exit(0)

        elif service == 'discord':
            print("Select Discord connection mode:")
            print("1. Admin Bot (Requires Bot Token)")
            print("2. Paste Discord User Token directly")
            mode = input("Select (1-2): ").strip()
            
            token = getpass.getpass("Enter Token: ").strip()
            if token:
                is_bot = (mode == "1")
                cfg.add_ds_profile(profile_name, token, is_bot=is_bot)
                print(f"[+] Discord profile '{profile_name}' added!")
            else:
                print("[!] Token cannot be empty.")
            sys.exit(0)

    # Example: sheet dev create "My Workbook"
    # Example: sheet dev <spreadsheet_id> add-tab "Sheet2"
    # Example: sheet dev <spreadsheet_id> append "Sheet1!A1" "row1_val1,row1_val2"
    if args[0] == 'sheet':
        if len(args) < 3:
            print("[!] Usage:")
            print("  ragchat sheet <profile> list")
            print("  ragchat sheet <profile> create <title>")
            print("  ragchat sheet <profile> <spreadsheet_id> add-tab <tab_title>")
            print("  ragchat sheet <profile> <spreadsheet_id> append <range> <comma_separated_values>")
            sys.exit(1)
            
        profile_name = args[1]
        action_or_id = args[2]
        
        if action_or_id.lower() not in ['list'] and len(args) < 4:
            print("[!] Usage:")
            print("  ragchat sheet <profile> create <title>")
            print("  ragchat sheet <profile> <spreadsheet_id> add-tab <tab_title>")
            print("  ragchat sheet <profile> <spreadsheet_id> append <range> <comma_separated_values>")
            sys.exit(1)
        
        try:
            creds = GoogleAuthManager().get_credentials(profile_name)
            client = GoogleClient(creds)
        except Exception as e:
            print(f"[!] Authentication failed for Google profile '{profile_name}': {e}")
            sys.exit(1)
            
        if action_or_id.lower() == 'list':
            try:
                # Query Google Drive for Sheets files (mimeType = application/vnd.google-apps.spreadsheet)
                query = "mimeType = 'application/vnd.google-apps.spreadsheet'"
                files = client.drive.list_drive_files(max_results=50, query=query)
                if not files:
                    print("[-] No spreadsheets found in your Drive.")
                else:
                    print("[+] Spreadsheets in Google Drive:")
                    for f in files:
                        print(f"  - {f['name']} (ID: {f['id']})")
            except Exception as e:
                print(f"[!] Failed to list spreadsheets: {e}")
            sys.exit(0)

        elif action_or_id.lower() == 'create':
            title = args[3]
            try:
                result = client.sheets.create_spreadsheet(title)
                print(f"[+] Spreadsheet created successfully!")
                print(f"    ID: {result.get('spreadsheetId')}")
                print(f"    URL: https://docs.google.com/spreadsheets/d/{result.get('spreadsheetId')}/edit")
            except Exception as e:
                print(f"[!] Failed to create spreadsheet: {e}")
            sys.exit(0)
            
        else:
            spreadsheet_id = action_or_id
            sub_action = args[3].lower()
            
            if sub_action == 'add-tab':
                if len(args) < 5:
                    print("[!] Missing tab title. Usage: sheet <profile> <spreadsheet_id> add-tab <tab_title>")
                    sys.exit(1)
                tab_title = args[4]
                try:
                    client.sheets.add_sheet(spreadsheet_id, tab_title)
                    print(f"[+] Added tab '{tab_title}' to spreadsheet '{spreadsheet_id}'.")
                except Exception as e:
                    print(f"[!] Failed to add sheet tab: {e}")
                sys.exit(0)
                
            elif sub_action == 'append':
                if len(args) < 6:
                    print("[!] Missing parameters. Usage: sheet <profile> <spreadsheet_id> append <range> <comma_separated_values>")
                    sys.exit(1)
                range_name = args[4]
                raw_values = args[5]
                # Split comma separated parameters into a list of row values
                row_data = [val.strip() for val in raw_values.split(',')]
                try:
                    client.sheets.append_spreadsheet_values(spreadsheet_id, range_name, [row_data])
                    print(f"[+] Appended row {row_data} to range '{range_name}'.")
                except Exception as e:
                    print(f"[!] Failed to append values: {e}")
                sys.exit(0)
                
            elif sub_action == 'delete-tab':
                if len(args) < 5:
                    print("[!] Missing tab title. Usage: sheet <profile> <spreadsheet_id> delete-tab <tab_title>")
                    sys.exit(1)
                tab_title = args[4]
                try:
                    client.sheets.delete_sheet(spreadsheet_id, tab_title)
                    print(f"[+] Deleted tab '{tab_title}' from spreadsheet '{spreadsheet_id}'.")
                except Exception as e:
                    print(f"[!] Failed to delete sheet tab: {e}")
                sys.exit(0)
                
            elif sub_action == 'get-tabs':
                try:
                    tabs = client.sheets.get_sheet_names(spreadsheet_id)
                    print(f"[+] Tabs in spreadsheet '{spreadsheet_id}':")
                    for tab in tabs:
                        print(f"  - {tab}")
                except Exception as e:
                    print(f"[!] Failed to fetch tab names: {e}")
                sys.exit(0)
                
            else:
                print(f"[!] Unknown sheet action: '{sub_action}'. Use: add-tab, append, get-tabs")
                sys.exit(1)
                
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

    # Example: -m dev 10h (Microsoft Outlook sync and query)
    if args[0] == '-m':
        if len(args) < 3:
            print("[!] Usage: python main.py -m <profile_name> <time_window> (e.g., -m dev 10h)")
            sys.exit(1)
            
        profile_name = args[1]
        time_window_str = args[2]
        
        since_timestamp = parse_time_window(time_window_str)
        if since_timestamp is None:
            print(f"[!] Invalid time window format: '{time_window_str}'. Use format like '10h', '2d', '1w'.")
            sys.exit(1)
            
        # 1. Sync recent emails first
        sync_engine = MicrosoftSyncEngine()
        print(f"[*] Syncing recent Outlook emails for '{profile_name}'...")
        sync_engine.sync_outlook(profile_name)
        
        # 2. Query local SQLite
        db_conn = LocalDB()
        emails = db_conn.get_microsoft_emails(profile_name, since_timestamp=since_timestamp, limit=100)
        
        if not emails:
            print(f"[-] No Outlook emails found for profile '{profile_name}' in the last {time_window_str}.")
            sys.exit(0)
            
        # 3. Print formatted table using Rich
        console = Console()
        table = Table(title=f"Outlook Emails for '{profile_name}' (Last {time_window_str})", show_lines=True)
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

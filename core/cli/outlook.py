import sys
from rich.console import Console
from rich.table import Table
from core.sync import MicrosoftSyncEngine
from core.db import LocalDB
from core.cli_handlers import parse_time_window

def handle_outlook_cli(args):
    """Syncs and lists recent Microsoft Outlook messages."""
    if len(args) < 3:
        print("[!] Usage: python main.py -m <profile_name> <time_window> (e.g., -m dev 10h)")
        sys.exit(1)
        
    profile_name = args[1]
    time_window_str = args[2]
    
    since_timestamp = parse_time_window(time_window_str)
    if since_timestamp is None:
        print(f"[!] Invalid time window format: '{time_window_str}'. Use format like '10h', '2d', '1w'.")
        sys.exit(1)
        
    sync_engine = MicrosoftSyncEngine()
    print(f"[*] Syncing recent Outlook emails for '{profile_name}'...")
    sync_engine.sync_outlook(profile_name)
    
    db_conn = LocalDB()
    emails = db_conn.get_microsoft_emails(profile_name, since_timestamp=since_timestamp, limit=100)
    
    if not emails:
        print(f"[-] No Outlook emails found for profile '{profile_name}' in the last {time_window_str}.")
        sys.exit(0)
        
    console = Console()
    table = Table(title=f"Outlook Emails for '{profile_name}' (Last {time_window_str})", show_lines=True)
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("From", style="green")
    table.add_column("Subject", style="magenta")
    table.add_column("Snippet", style="white")
    
    for email_data in emails:
        dt_str = email_data['date']
        if len(dt_str) > 16:
            dt_str = dt_str[:16].replace('T', ' ')
        
        from_str = f"{email_data['sender_name']} <{email_data['sender']}>" if email_data['sender_name'] else email_data['sender']
        table.add_row(dt_str, from_str, email_data['subject'], email_data['snippet'])
        
    console.print(table)
    sys.exit(0)

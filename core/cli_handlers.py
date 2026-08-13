import sys
import time

def parse_time_window(window_str):
    """Parses time window strings like '10h', '2d', '1w', '1m' to epoch offset."""
    import re
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

# Forwarding handlers to separate service subfiles
def handle_rename_profile_cli(args):
    from core.cli.auth import handle_rename_profile_cli as impl
    impl(args)

def handle_sync_cli(args):
    from core.cli.sync import handle_sync_cli as impl
    impl(args)

def handle_link_cli(args):
    from core.cli.auth import handle_link_cli as impl
    impl(args)

def handle_drive_cli(args):
    from core.cli.gdrive import handle_drive_cli as impl
    impl(args)

def handle_onedrive_cli(args):
    from core.cli.onedrive import handle_onedrive_cli as impl
    impl(args)

def handle_sheet_cli(args):
    from core.cli.gsheets import handle_sheet_cli as impl
    impl(args)

def handle_gmail_cli(args):
    from core.cli.gmail import handle_gmail_cli as impl
    impl(args)

def handle_outlook_cli(args):
    from core.cli.outlook import handle_outlook_cli as impl
    impl(args)

def handle_telegram_cli(args):
    from core.cli.telegram import handle_telegram_cli as impl
    impl(args)

def handle_discord_cli(args):
    from core.cli.discord import handle_discord_cli as impl
    impl(args)

def handle_bind_cli(args):
    from core.cli.auth import handle_bind_cli as impl
    impl(args)

def handle_list_profiles_cli(args):
    from core.cli.auth import handle_list_profiles_cli as impl
    impl(args)

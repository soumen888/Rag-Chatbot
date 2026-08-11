import sys
import getpass
from core.config_manager import ConfigManager
from core.db import LocalDB
from services.google.auth import GoogleAuthManager
from services.microsoft.auth import MicrosoftAuthManager
from services.telegram.ingestor import TelegramIngestor

def db_safe_profile_name(name):
    import re
    return re.sub(r'[^a-zA-Z0-9]', '_', name)

def handle_rename_profile_cli(args):
    """Handles profile renaming operations."""
    if len(args) < 4:
        print("[!] Usage: ragchat rename-profile <service> <old_name> <new_name>")
        sys.exit(1)
    service = args[1].lower()
    old_name = args[2]
    new_name = args[3]

    if service not in ['google', 'microsoft']:
        print(f"[!] Unsupported service for rename: '{service}'. Only 'google' and 'microsoft' are supported.")
        sys.exit(1)

    try:
        if service == 'google':
            auth = GoogleAuthManager()
        else:
            auth = MicrosoftAuthManager()

        success = auth.rename_profile(old_name, new_name)
        if not success:
            print(f"[!] Failed to rename credential profile. Check if profile '{old_name}' exists.")
            sys.exit(1)

        db = LocalDB()
        db.rename_profile(service, old_name, new_name)
        print(f"[+] Successfully renamed {service} profile '{old_name}' to '{new_name}' across credentials and database!")
    except Exception as e:
        print(f"[!] Error during rename-profile: {e}")
    sys.exit(0)

def handle_link_cli(args):
    """Handles authorization link configurations."""
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

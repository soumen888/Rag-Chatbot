import sys
from ragchat_core.core.sync import GoogleSyncEngine, MicrosoftSyncEngine

def handle_sync_cli(args):
    """Handles full account synchronization."""
    if len(args) < 4:
        print("[!] Usage: ragchat sync <service> <profile_name> all")
        sys.exit(1)
    service = args[1].lower()
    profile_name = args[2]
    sync_mode = args[3].lower()

    if service not in ['google', 'microsoft']:
        print(f"[!] Unsupported service for sync: '{service}'. Only 'google' and 'microsoft' are supported.")
        sys.exit(1)
    if sync_mode != 'all':
        print(f"[!] Unsupported sync mode: '{sync_mode}'. Use 'all' to sync full history.")
        sys.exit(1)

    try:
        if service == 'google':
            sync_engine = GoogleSyncEngine()
            print(f"[*] Beginning full history sync for Google profile '{profile_name}'...")
            sync_engine.sync_gmail(profile_name, sync_all=True)
        else:
            sync_engine = MicrosoftSyncEngine()
            print(f"[*] Beginning full history sync for Microsoft profile '{profile_name}'...")
            sync_engine.sync_outlook(profile_name, sync_all=True)
    except Exception as e:
        print(f"[!] Error during full sync: {e}")
    sys.exit(0)

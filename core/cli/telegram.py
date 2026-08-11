import os
import sys
from core.chunker import DocChunker
from core.config_manager import ConfigManager
from core.vector_db import VectorDB
from services.telegram import TelegramIngestor

def handle_telegram_cli(args):
    """Handles Telegram CLI sync commands."""
    if len(args) < 3 or args[2].lower() != 'sync':
        print("[!] Usage:")
        print("  ragchat telegram <profile> sync")
        sys.exit(1)

    profile_name = args[1]
    cfg = ConfigManager()
    profiles = cfg.load_tg_profiles()

    if profile_name not in profiles:
        print(f"[!] Telegram profile '{profile_name}' not found. Please link it first.")
        sys.exit(1)

    session_name = profiles[profile_name]["session_name"]
    print(f"[*] Starting Telegram sync for profile '{profile_name}'...")

    ingestor = TelegramIngestor(
        api_id=ConfigManager.DEFAULT_TG_API_ID,
        api_hash=ConfigManager.DEFAULT_TG_API_HASH,
        session_name=session_name
    )
    chunker = DocChunker()
    db = VectorDB()

    try:
        ingestor.sync_configured_channels(db, chunker)
        print(f"[+] Telegram profile '{profile_name}' sync finished successfully!")
    except Exception as e:
        print(f"[!] Telegram batch sync failed: {e}")
        sys.exit(1)
    sys.exit(0)

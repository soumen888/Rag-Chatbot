import os
import sys
from core.chunker import DocChunker
from core.config_manager import ConfigManager
from core.vector_db import VectorDB
from services.discord import DiscordIngestor

def handle_discord_cli(args):
    """Handles Discord CLI sync commands."""
    if len(args) < 3 or args[2].lower() != 'sync':
        print("[!] Usage:")
        print("  ragchat discord <profile> sync")
        sys.exit(1)

    profile_name = args[1]
    cfg = ConfigManager()
    profiles = cfg.load_ds_profiles()

    if profile_name not in profiles:
        print(f"[!] Discord profile '{profile_name}' not found. Please link it first.")
        sys.exit(1)

    prof_data = profiles[profile_name]
    token = prof_data["token"]
    is_bot = prof_data["is_bot"]
    configured_targets = os.environ.get("DISCORD_TARGETS", "")

    if not configured_targets:
        print("[!] No channels configured in DISCORD_TARGETS variable inside .env.")
        sys.exit(1)

    print(f"[*] Starting Discord sync for profile '{profile_name}'...")
    ingestor = DiscordIngestor(token=token, is_bot=is_bot)
    chunker = DocChunker()
    db = VectorDB()

    try:
        ingestor.sync_channels(db, chunker, configured_targets)
        print(f"[+] Discord profile '{profile_name}' sync finished successfully!")
    except Exception as e:
        print(f"[!] Discord batch sync failed: {e}")
        sys.exit(1)
    sys.exit(0)

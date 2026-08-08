import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from telegram import TelegramIngestor
from discord import DiscordIngestor
from core import DocChunker, VectorDB, ConfigManager

def run_daemon():
    print("==================================================")
    print("     DocChat Background Sync Daemon (TG & DS)     ")
    print("==================================================")

    auto_sync = os.environ.get("TG_AUTO_SYNC_ENABLED", "true").lower().strip() == "true"
    interval_minutes = os.environ.get("TG_SYNC_INTERVAL_MINUTES", "30").strip()
    interval_seconds = int(interval_minutes) * 60 if interval_minutes.isdigit() else 1800

    if not auto_sync:
        print("[!] TG_AUTO_SYNC_ENABLED is set to 'false'. Exiting daemon.")
        return

    print(f"[*] Background Sync Enabled. Interval: every {interval_minutes} minutes.")
    
    db = VectorDB()
    chunker = DocChunker()
    cfg = ConfigManager()

    while True:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[────────── Daemon Sync Run at {now_str} ──────────]")
        
        # 1. Sync Telegram Channels across all profiles
        tg_profiles = cfg.load_tg_profiles()
        if tg_profiles:
            print(f"[*] Syncing Telegram ({len(tg_profiles)} profiles)...")
            for profile_name, data in tg_profiles.items():
                try:
                    ingestor = TelegramIngestor(
                        api_id=ConfigManager.DEFAULT_TG_API_ID,
                        api_hash=ConfigManager.DEFAULT_TG_API_HASH,
                        session_name=data["session_name"]
                    )
                    print(f"  - Profile: '{profile_name}'")
                    ingestor.sync_configured_channels(db, chunker)
                except Exception as e:
                    print(f"  [!] Sync error on Telegram profile '{profile_name}': {e}")
        else:
            print("[*] No Telegram profiles connected. Skipping.")

        # 2. Sync Discord Channels across all profiles
        ds_profiles = cfg.load_ds_profiles()
        discord_targets = os.environ.get("DISCORD_TARGETS", "")
        if ds_profiles and discord_targets:
            print(f"[*] Syncing Discord ({len(ds_profiles)} profiles)...")
            for profile_name, data in ds_profiles.items():
                try:
                    ingestor = DiscordIngestor(
                        token=data["token"],
                        is_bot=data["is_bot"]
                    )
                    print(f"  - Profile: '{profile_name}'")
                    ingestor.sync_channels(db, chunker, discord_targets)
                except Exception as e:
                    print(f"  [!] Sync error on Discord profile '{profile_name}': {e}")
        else:
            print("[*] No Discord profiles or target channels configured. Skipping.")

        print(f"\n[*] Sync cycle finished. Sleeping for {interval_minutes} minutes until next run...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        print("\n[*] Background daemon stopped.")
        sys.exit(0)

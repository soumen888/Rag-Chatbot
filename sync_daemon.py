import os
import sys
import time
from datetime import datetime

# Ensure local workspace modules are prioritized
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Secure OS Keychain is used by default; custom backends can still be set via PYTHON_KEYRING_BACKEND

from typing import Any

try:
    from ragchat_core.core.config_manager import ConfigManager  # type: ignore
except ImportError:
    from core.config_manager import ConfigManager

# One-time migration of any existing .env file → keyring, then populate os.environ
# so all os.environ.get() calls in the daemon and imported modules resolve correctly.
_cfg = ConfigManager()
_cfg._migrate_legacy_dotenv()
_cfg.load_all_to_env()

try:
    from ragchat_core.services.telegram.ingestor import TelegramIngestor  # type: ignore
    from ragchat_core.services.discord.ingestor import DiscordIngestor  # type: ignore
    from ragchat_core.services.google.auth import GoogleAuthManager  # type: ignore
    from ragchat_core.services.microsoft.auth import MicrosoftAuthManager  # type: ignore
    from ragchat_core.core.sync import GoogleSyncEngine, MicrosoftSyncEngine  # type: ignore
    from ragchat_core.core.chunker import DocChunker  # type: ignore
    from ragchat_core.core.vector_db import VectorDB  # type: ignore
except ImportError:
    try:
        from services.telegram.ingestor import TelegramIngestor  # type: ignore
        from services.discord.ingestor import DiscordIngestor  # type: ignore
        from services.google.auth import GoogleAuthManager  # type: ignore
        from services.microsoft.auth import MicrosoftAuthManager  # type: ignore
        from core.sync import GoogleSyncEngine, MicrosoftSyncEngine  # type: ignore
        from core.chunker import DocChunker  # type: ignore
        from core.vector_db import VectorDB  # type: ignore
    except ImportError:
        TelegramIngestor: Any = None
        DiscordIngestor: Any = None
        GoogleAuthManager: Any = None
        MicrosoftAuthManager: Any = None
        GoogleSyncEngine: Any = None
        MicrosoftSyncEngine: Any = None
        DocChunker: Any = None
        VectorDB: Any = None


def run_daemon():
    print("==================================================")
    print("  RAGChat Background Sync Daemon (Mail & Chat)  ")
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

        # 3. Sync Gmail Emails across all Google profiles
        g_manager = GoogleAuthManager()
        google_profiles = g_manager.list_profiles()
        if google_profiles:
            print(f"[*] Syncing Gmail ({len(google_profiles)} profiles)...")
            g_sync = GoogleSyncEngine()
            for profile_name in google_profiles:
                try:
                    g_sync.sync_gmail(profile_name)
                except Exception as e:
                    print(f"  [!] Sync error on Gmail profile '{profile_name}': {e}")
        else:
            print("[*] No Google profiles linked. Skipping.")

        # 4. Sync Outlook Emails across all Microsoft profiles
        ms_manager = MicrosoftAuthManager()
        microsoft_profiles = ms_manager.list_profiles()
        if microsoft_profiles:
            print(f"[*] Syncing Outlook ({len(microsoft_profiles)} profiles)...")
            ms_sync = MicrosoftSyncEngine()
            for profile_name in microsoft_profiles:
                try:
                    ms_sync.sync_outlook(profile_name)
                except Exception as e:
                    print(f"  [!] Sync error on Outlook profile '{profile_name}': {e}")
        else:
            print("[*] No Microsoft profiles linked. Skipping.")

        print(f"\n[*] Sync cycle finished. Sleeping for {interval_minutes} minutes until next run...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        print("\n[*] Background daemon stopped.")
        sys.exit(0)

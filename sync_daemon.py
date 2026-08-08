import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from telegram import TelegramIngestor
from core import DocChunker, VectorDB

def run_daemon():
    print("==================================================")
    print("      Telegram Background Sync Daemon           ")
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

    while True:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[────────── Daemon Sync Run at {now_str} ──────────]")
        
        try:
            ingestor = TelegramIngestor()
            ingestor.sync_configured_channels(db, chunker)
        except Exception as e:
            print(f"[!] Sync error: {e}")

        print(f"[*] Sleeping for {interval_minutes} minutes until next sync...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        print("\n[*] Background daemon stopped.")
        sys.exit(0)

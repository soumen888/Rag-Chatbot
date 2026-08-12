import os
import json
import time
import getpass
from datetime import datetime, timedelta, timezone
from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat, User

class TelegramIngestor:
    def __init__(self, api_id=None, api_hash=None, session_name=None, cache_dir="./.crawl_cache"):
        self.api_id = api_id or os.environ.get("TG_API_ID")
        self.api_hash = api_hash or os.environ.get("TG_API_HASH")
        self.session_name = session_name or os.environ.get("TG_SESSION_NAME", "personal_agent_session")
        self.cache_dir = cache_dir
        self.client = None
        self.channels_meta_file = os.path.join(self.cache_dir, "tg_channels.json")
        self.channels_meta = self.load_channels_meta()

    def load_channels_meta(self):
        if os.path.exists(self.channels_meta_file):
            try:
                with open(self.channels_meta_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_channels_meta(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            with open(self.channels_meta_file, "w") as f:
                json.dump(self.channels_meta, f, indent=2)
        except Exception as e:
            print(f"[!] Error saving channel metadata: {e}")

    def connect(self):
        if not self.api_id or not self.api_hash:
            raise ValueError(
                "Telegram API credentials missing. Set TG_API_ID and TG_API_HASH in your .env file."
            )
        session_path = os.path.join(self.cache_dir, self.session_name)
        self.client = TelegramClient(session_path, int(self.api_id), self.api_hash)
        self.client.connect()

        if not self.client.is_user_authorized():
            print("[*] Telegram user authorization required.")
            phone = input("Enter your Telegram phone number (with country code, e.g. +1234567890): ").strip()
            self.client.send_code_request(phone)
            code = getpass.getpass("Enter the login code sent to your Telegram (hidden): ").strip()
            try:
                self.client.sign_in(phone, code)
            except Exception as e:
                if "2FA" in str(e) or "password" in str(e).lower():
                    password = getpass.getpass("Enter your 2FA Password (hidden): ").strip()
                    self.client.sign_in(password=password)
                else:
                    raise e
        print("[+] Telegram client connected successfully.")

    def resolve_entity(self, channel_input):
        """
        Resolves channel username/link/peer_id to a Telethon entity and extracts
        its immutable peer_id and current title.
        """
        if not self.client:
            self.connect()

        target_input = channel_input

        # Handle numeric input
        if str(channel_input).replace("-", "").isdigit():
            raw_id = str(channel_input).replace("-", "")
            # Telegram Channels/Supergroups start with -100
            if not str(channel_input).startswith("-100"):
                formatted_id = f"-100{raw_id}"
            else:
                formatted_id = str(channel_input)
            
            try:
                entity = self.client.get_entity(int(formatted_id))
            except Exception:
                # Fallback to integer without prefix if user passed a user/chat ID
                entity = self.client.get_entity(int(channel_input))
        else:
            entity = self.client.get_entity(channel_input)

        peer_id = str(entity.id)
        
        # Format string ID with standard Telegram channel prefix if applicable
        if isinstance(entity, Channel):
            title = entity.title
            username = entity.username or ""
        elif isinstance(entity, Chat):
            title = entity.title
            username = ""
        elif isinstance(entity, User):
            title = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
            username = entity.username or ""
        else:
            title = str(channel_input)
            username = ""

        # Update local mapping of peer_id -> current title
        self.channels_meta[peer_id] = {
            "peer_id": peer_id,
            "title": title,
            "username": username,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.save_channels_meta()

        return entity, peer_id, title

    def build_message_link(self, entity, message_id):
        """Constructs a direct clickable link to the Telegram message."""
        if hasattr(entity, 'username') and entity.username:
            return f"https://t.me/{entity.username}/{message_id}"
        else:
            # Private group / channel format
            clean_id = str(entity.id).replace("-100", "").replace("-", "")
            return f"https://t.me/c/{clean_id}/{message_id}"

    def fetch_messages(self, channel_input, hours=None, limit=500):
        """
        Fetches messages from a channel.
        If hours is provided (e.g. 24), fetches only messages from the last N hours.
        Returns a list of structured message objects.
        """
        if not self.client:
            self.connect()

        entity, peer_id, title = self.resolve_entity(channel_input)
        
        cutoff_time = None
        if hours:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            print(f"[*] Fetching messages from '{title}' (Peer ID: {peer_id}) from the last {hours} hours...")
        else:
            print(f"[*] Fetching up to {limit} messages from '{title}' (Peer ID: {peer_id})...")

        messages = []
        for msg in self.client.iter_messages(entity, limit=limit if not hours else None):
            if not msg.text:
                continue

            msg_date = msg.date.replace(tzinfo=timezone.utc) if msg.date.tzinfo is None else msg.date
            
            if cutoff_time and msg_date < cutoff_time:
                # Reached beyond our hours window
                break

            sender_name = "Unknown"
            if msg.sender:
                if hasattr(msg.sender, 'first_name'):
                    sender_name = f"{msg.sender.first_name or ''} {msg.sender.last_name or ''}".strip()
                elif hasattr(msg.sender, 'title'):
                    sender_name = msg.sender.title

            link = self.build_message_link(entity, msg.id)

            messages.append({
                "peer_id": peer_id,
                "channel_title": title,
                "message_id": msg.id,
                "sender": sender_name,
                "text": msg.text,
                "timestamp": int(msg_date.timestamp()),
                "date_str": msg_date.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "link": link
            })

        print(f"[+] Retrieved {len(messages)} messages from '{title}'.")
        self.disconnect()
        return messages, peer_id, title

    def get_configured_channels(self):
        """Reads TG_CHANNELS env var and returns a list of cleaned channel strings."""
        channels_raw = os.environ.get("TG_CHANNELS", "")
        if not channels_raw:
            return []
        return [c.strip() for c in channels_raw.split(",") if c.strip()]

    def load_sync_state(self):
        sync_file = os.path.join(self.cache_dir, "tg_sync_state.json")
        if os.path.exists(sync_file):
            try:
                with open(sync_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_sync_state(self, state):
        os.makedirs(self.cache_dir, exist_ok=True)
        sync_file = os.path.join(self.cache_dir, "tg_sync_state.json")
        try:
            with open(sync_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[!] Error saving sync state: {e}")

    def sync_configured_channels(self, db, chunker, limit=None):
        """
        Syncs all channels listed in TG_CHANNELS env var into the unified
        'telegram_all' vector collection incrementally.
        """
        channels = self.get_configured_channels()
        if not channels:
            print("[!] No channels configured in TG_CHANNELS env variable.")
            return

        # Read env settings
        lookback_days_str = os.environ.get("TG_INITIAL_LOOKBACK_DAYS", "7").strip()
        lookback_days = int(lookback_days_str) if lookback_days_str.isdigit() else 7
        
        max_msgs_str = os.environ.get("TG_MAX_MESSAGES_PER_SYNC", "500").strip()
        fetch_limit = limit or (int(max_msgs_str) if max_msgs_str.isdigit() else 500)

        sync_state = self.load_sync_state()
        unified_collection = "telegram_all"
        total_new_chunks = 0

        print(f"[*] Starting Telegram Sync for {len(channels)} configured channels...")
        for ch_input in channels:
            try:
                # Resolve entity
                if not self.client:
                    self.connect()

                entity, peer_id, title = self.resolve_entity(ch_input)
                min_id = sync_state.get(peer_id, {}).get("last_msg_id", 0)

                # For new channels (min_id == 0), filter by lookback days
                cutoff_time = None
                if min_id == 0:
                    cutoff_time = datetime.now(timezone.utc) - timedelta(days=lookback_days)
                    print(f"[*] Pre-filling new channel '{title}' (Peer ID: {peer_id}) from last {lookback_days} days...")
                else:
                    print(f"[*] Incremental sync for '{title}' (Peer ID: {peer_id})...")

                fetched = []
                max_seen_id = min_id

                for msg in self.client.iter_messages(entity, min_id=min_id, limit=fetch_limit):
                    if not msg.text:
                        continue

                    msg_date = msg.date.replace(tzinfo=timezone.utc) if msg.date.tzinfo is None else msg.date

                    if cutoff_time and msg_date < cutoff_time:
                        # Beyond our initial lookback cutoff
                        break

                    if msg.id > max_seen_id:
                        max_seen_id = msg.id

                    sender_name = "Unknown"
                    if msg.sender:
                        if hasattr(msg.sender, 'first_name'):
                            sender_name = f"{msg.sender.first_name or ''} {msg.sender.last_name or ''}".strip()
                        elif hasattr(msg.sender, 'title'):
                            sender_name = msg.sender.title

                    link = self.build_message_link(entity, msg.id)

                    fetched.append({
                        "peer_id": peer_id,
                        "channel_title": title,
                        "message_id": msg.id,
                        "sender": sender_name,
                        "text": msg.text,
                        "timestamp": int(msg_date.timestamp()),
                        "date_str": msg_date.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "link": link
                    })

                if fetched:
                    # Chunks and store in unified collection
                    chunks = chunker.process_telegram_messages(fetched)
                    db.add_chunks(unified_collection, chunks)
                    total_new_chunks += len(chunks)

                    # Update sync state checkpoint
                    sync_state[peer_id] = {
                        "channel_title": title,
                        "last_msg_id": max_seen_id,
                        "last_sync_at": datetime.now(timezone.utc).isoformat()
                    }
                    self.save_sync_state(sync_state)
                    print(f"[+] Added {len(chunks)} new chunks from '{title}'.")
                else:
                    print(f"[+] '{title}' is already up-to-date.")

            except Exception as e:
                print(f"[!] Error syncing channel '{ch_input}': {e}")

        self.disconnect()
        print(f"[+] Telegram Sync completed. Total new chunks added: {total_new_chunks}")

    def disconnect(self):
        if self.client and self.client.is_connected():
            try:
                self.client.disconnect()
            except Exception:
                pass

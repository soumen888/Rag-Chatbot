import os
import json
import time
import random
import requests
from datetime import datetime, timezone, timedelta

class DiscordIngestor:
    def __init__(self, token=None, is_bot=False, cache_dir="./.crawl_cache"):
        self.token = token
        self.is_bot = is_bot
        self.cache_dir = cache_dir
        self.sync_state_file = os.path.join(self.cache_dir, "discord_sync_state.json")
        self.base_url = "https://discord.com/api/v9"
        
        # Human browser fingerprint headers for user accounts
        self.user_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Super-Properties": "eyJvcyI6Ik1hYyBPUyBYIiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdmVyc2lvbiI6IjEyMC4wLjAuMCIsIm9zX3ZlcnNpb24iOiIxMC4xNS43IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfMTVfNykgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiY2xpZW50X2J1aWxkX251bWJlciI6MjUwMDAwLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
        }

    def _get_headers(self):
        headers = self.user_headers.copy()
        if self.is_bot:
            headers["Authorization"] = f"Bot {self.token}"
        else:
            headers["Authorization"] = self.token
        return headers



    def fetch_channel_metadata(self, channel_id):
        """Fetches channel title and parent server/guild title."""
        url = f"{self.base_url}/channels/{channel_id}"
        headers = self._get_headers()
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise ValueError(f"Failed to fetch channel metadata (HTTP {res.status_code})")
        
        ch_data = res.json()
        channel_name = ch_data.get("name", str(channel_id))
        guild_id = ch_data.get("guild_id")
        server_name = "Private"

        if guild_id:
            guild_url = f"{self.base_url}/guilds/{guild_id}"
            g_res = requests.get(guild_url, headers=headers)
            if g_res.status_code == 200:
                server_name = g_res.json().get("name", "Unknown Server")

        return channel_name, server_name, guild_id

    def fetch_messages(self, channel_id, limit=500, after_id=None, before_id=None):
        """
        Fetches message history from a Discord channel.
        Includes pagination handling and safety delays in user-account mode.
        """
        headers = self._get_headers()
        messages = []
        last_id = before_id
        
        while len(messages) < limit:
            chunk_limit = min(100, limit - len(messages))
            url = f"{self.base_url}/channels/{channel_id}/messages?limit={chunk_limit}"
            
            if last_id:
                url += f"&before={last_id}"
            elif after_id:
                url += f"&after={after_id}"
                
            res = requests.get(url, headers=headers)
            if res.status_code == 429:
                # Rate limit encountered - read sleep instruction or fallback
                retry_after = res.json().get("retry_after", 2.0)
                print(f"[!] Discord rate limited. Retrying after {retry_after}s...")
                time.sleep(retry_after)
                continue
            elif res.status_code != 200:
                print(f"[!] Error fetching messages (HTTP {res.status_code}): {res.text}")
                break
                
            batch = res.json()
            if not batch:
                break
                
            for m in batch:
                author = m.get("author", {})
                sender = author.get("global_name") or author.get("username") or "Unknown"
                username = author.get("username", "unknown")
                msg_id = m.get("id")
                
                # Direct message jump link
                guild_id = m.get("guild_id", "@me")
                link = f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                
                # Parse timestamp
                ts_str = m.get("timestamp")
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                
                messages.append({
                    "message_id": msg_id,
                    "channel_id": channel_id,
                    "sender": sender,
                    "username": username,
                    "text": m.get("content", ""),
                    "timestamp": int(dt.timestamp()),
                    "date_str": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "link": link
                })
                
            # Setup last_id for pagination (fetch older messages next run)
            if after_id:
                # When syncing 'after', we want to page forwards
                break
            else:
                last_id = batch[-1]["id"]
                
            # Apply safety delay to emulate human paging activity (user-account mode only)
            if not self.is_bot:
                time.sleep(random.uniform(1.5, 3.5))

        return messages

    def load_sync_state(self):
        if os.path.exists(self.sync_state_file):
            try:
                with open(self.sync_state_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_sync_state(self, state):
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            with open(self.sync_state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[!] Error saving sync state: {e}")

    def fetch_server_channels(self, guild_id):
        """Fetches text channels in a server."""
        url = f"{self.base_url}/guilds/{guild_id}/channels"
        headers = self._get_headers()
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise ValueError(f"Failed to fetch server channels (HTTP {res.status_code})")
        
        channels = []
        for ch in res.json():
            try:
                ch_type = int(ch.get("type", -1))
            except (ValueError, TypeError):
                continue
                
            # Type 0: Text, 5: Guild News/Announcement, 11: Public Thread, 12: Private Thread, 15: Guild Forum
            if ch_type in [0, 5, 11, 12, 15]:
                channels.append({
                    "id": ch["id"],
                    "name": ch["name"],
                    "type": ch_type
                })
        return channels

    def sync_channels(self, db, chunker, targets):
        """
        Syncs Discord targets (Format: SERVER_ID:ch1,ch2 | SERVER_ID2:all)
        or straight channel list.
        """
        sync_state = self.load_sync_state()
        headers = self._get_headers()
        
        # Resolve target channel IDs
        channels_to_sync = []
        for target in [t.strip() for t in targets.split("|") if t.strip()]:
            if ":" in target:
                guild_id, ch_spec = target.split(":", 1)
                guild_id = guild_id.strip()
                ch_spec = ch_spec.strip()
                
                if ch_spec.lower() == "all":
                    url = f"{self.base_url}/guilds/{guild_id}/channels"
                    res = requests.get(url, headers=headers)
                    if res.status_code == 200:
                        for ch in res.json():
                            # Type 0 is standard text channel, 11/12 is thread/forum
                            if ch.get("type") in [0, 11, 12]:
                                channels_to_sync.append(ch["id"])
                    else:
                        print(f"[!] Could not fetch channels for server {guild_id} (HTTP {res.status_code})")
                else:
                    for ch_id in ch_spec.split(","):
                        channels_to_sync.append(ch_id.strip())
            else:
                # Direct channel ID fallback
                channels_to_sync.append(target)

        total_new_chunks = 0
        for channel_id in channels_to_sync:
            try:
                ch_name, server_name, guild_id = self.fetch_channel_metadata(channel_id)
                safe_server = db.sanitize_collection_name(server_name)
                safe_chan = db.sanitize_collection_name(ch_name)
                collection_name = f"ds_{safe_server}_{safe_chan}"

                min_id = sync_state.get(channel_id, {}).get("last_msg_id")
                
                if min_id:
                    print(f"[*] Incremental sync for Discord: {server_name} -> #{ch_name}...")
                    messages = self.fetch_messages(channel_id, limit=200, after_id=min_id)
                else:
                    print(f"[*] Pre-filling Discord history: {server_name} -> #{ch_name}...")
                    messages = self.fetch_messages(channel_id, limit=500)

                if messages:
                    # Sort messages chronologically before processing
                    messages.sort(key=lambda x: x["timestamp"])
                    
                    # Add channel name/server name to message fields
                    for m in messages:
                        m["channel_title"] = ch_name
                        m["server_name"] = server_name

                    chunks = chunker.process_discord_messages(messages)
                    db.add_chunks(collection_name, chunks)
                    total_new_chunks += len(chunks)

                    # Update sync state checkpoint
                    max_id = max(int(m["message_id"]) for m in messages)
                    sync_state[channel_id] = {
                        "channel_title": ch_name,
                        "server_name": server_name,
                        "last_msg_id": str(max_id),
                        "last_sync_at": datetime.now(timezone.utc).isoformat()
                    }
                    self.save_sync_state(sync_state)
                    print(f"[+] Synced {len(chunks)} new chunks for #{ch_name}.")
                else:
                    print(f"[+] #{ch_name} is already up-to-date.")

                # Human delay between different channels
                if not self.is_bot:
                    time.sleep(random.uniform(2.0, 5.0))

            except Exception as e:
                print(f"[!] Error syncing Discord channel {channel_id}: {e}")

        return total_new_chunks

import os
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.markdown import Markdown
from ragchat_core.services.discord.ingestor import DiscordIngestor
from ragchat_core.core.chunker import DocChunker

def select_ds_profile(cfg):
    profiles = cfg.load_ds_profiles()
    if not profiles:
        print("[!] No connected Discord accounts found. Go to Settings (Option 6) to connect one.")
        return None
    if len(profiles) == 1:
        return list(profiles.keys())[0]
        
    print("\nAvailable Discord profiles:")
    profile_names = list(profiles.keys())
    for idx, name in enumerate(profile_names):
        is_bot = " (Bot)" if profiles[name].get("is_bot") else " (User)"
        print(f"{idx + 1}. {name}{is_bot}")
    sel = input(f"Select profile (1-{len(profile_names)}): ").strip()
    if not sel.isdigit() or int(sel) < 1 or int(sel) > len(profile_names):
        print("[!] Invalid selection.")
        return None
    return profile_names[int(sel) - 1]

def handle_discord_menu(db, chatbot, cfg):
    from core.menus.settings import init_llm_provider_wrapper
    while True:
        profile = select_ds_profile(cfg)
        if not profile:
            return chatbot

        prof_data = cfg.load_ds_profiles()[profile]
        token = prof_data["token"]
        is_bot = prof_data["is_bot"]

        while True:
            print(f"\n--- DISCORD MENU (Profile: {profile}) ---")
            configured_targets = os.environ.get("DISCORD_TARGETS", "")
            print(f"1. Sync configured DISCORD_TARGETS [{configured_targets}]")
            print("2. Index a specific Discord Channel ID or Server ID")
            print("3. Generate 24-Hour Channel Catch-Up Digest")
            print("4. Back to main menu")

            sub = input("\nSelect option (1-4): ").strip()
            if sub == "4" or sub.lower() in ["back", "b"]:
                break
            
            ingestor = DiscordIngestor(token=token, is_bot=is_bot)
            chunker = DocChunker()

            if sub == "1":
                if not configured_targets:
                    print("[!] No channels configured in DISCORD_TARGETS.")
                    continue
                try:
                    ingestor.sync_channels(db, chunker, configured_targets)
                except Exception as e:
                    print(f"[!] Discord batch sync failed: {e}")

            elif sub == "2":
                target_id = input("Enter Discord Channel ID or Server ID (or type 'back'): ").strip()
                if not target_id or target_id.lower() in ["back", "b"]:
                    continue

                limit_input = input("Max messages to fetch (default 500): ").strip()
                limit = int(limit_input) if limit_input.isdigit() else 500

                try:
                    is_server = False
                    try:
                        ch_name, server_name, guild_id = ingestor.fetch_channel_metadata(target_id)
                        channel_ids_to_index = [target_id]
                    except Exception:
                        is_server = True

                    if is_server:
                        print(f"[*] Fetching channels list for Server ID: {target_id}...")
                        channels = ingestor.fetch_server_channels(target_id)
                        if not channels:
                            print("[!] No visible text channels found on this server.")
                            continue
                        
                        print("\nAvailable Server Channels:")
                        for idx, ch in enumerate(channels):
                            print(f"{idx + 1}. #{ch['name']} (ID: {ch['id']})")
                        
                        sel = input(f"Select a channel to index (1-{len(channels)}): ").strip()
                        if not sel.isdigit() or int(sel) < 1 or int(sel) > len(channels):
                            print("[!] Invalid selection.")
                            continue
                        
                        selected_channel = channels[int(sel) - 1]
                        channel_ids_to_index = [selected_channel["id"]]
                    
                    for ch_id in channel_ids_to_index:
                        ch_name, server_name, guild_id = ingestor.fetch_channel_metadata(ch_id)
                        print(f"[*] Ingesting #{ch_name} from server '{server_name}'...")
                        messages = ingestor.fetch_messages(ch_id, limit=limit)
                        
                        if messages:
                            for m in messages:
                                m["channel_title"] = ch_name
                                m["server_name"] = server_name

                            safe_server = db.sanitize_collection_name(server_name)
                            safe_chan = db.sanitize_collection_name(ch_name)
                            collection_name = f"ds_{safe_server}_{safe_chan}"

                            chunks = chunker.process_discord_messages(messages)
                            db.add_chunks(collection_name, chunks)
                            print(f"[+] Discord channel #{ch_name} indexed into '{collection_name}' successfully!")
                            
                            if guild_id:
                                current_targets = os.environ.get("DISCORD_TARGETS", "").strip()
                                new_target = f"{guild_id}:{ch_id}"
                                
                                if not current_targets:
                                    updated_targets = new_target
                                else:
                                    target_list = [t.strip() for t in current_targets.split("|") if t.strip()]
                                    already_saved = False
                                    for target in target_list:
                                        if ":" in target:
                                            g, chs = target.split(":", 1)
                                            if g.strip() == str(guild_id):
                                                ch_list = [c.strip() for c in chs.split(",")]
                                                if "all" in ch_list or str(ch_id) in ch_list:
                                                    already_saved = True
                                                    break
                                    
                                    if not already_saved:
                                        updated = False
                                        for idx, target in enumerate(target_list):
                                            if ":" in target:
                                                g, chs = target.split(":", 1)
                                                if g.strip() == str(guild_id):
                                                    target_list[idx] = f"{guild_id}:{chs.strip()},{ch_id}"
                                                    updated = True
                                                    break
                                        if not updated:
                                            target_list.append(new_target)
                                        updated_targets = " | ".join(target_list)
                                    else:
                                        updated_targets = current_targets
                                
                                if current_targets != updated_targets:
                                    cfg.write_env_var("DISCORD_TARGETS", updated_targets)
                                    print(f"[+] Configuration auto-saved to .env: DISCORD_TARGETS={updated_targets}")
                except Exception as e:
                    print(f"[!] Discord indexing failed: {e}")

            elif sub == "3":
                channel_id = input("Enter Discord Channel ID (or type 'back'): ").strip()
                if not channel_id or channel_id.lower() in ["back", "b"]:
                    continue

                try:
                    ch_name, server_name, guild_id = ingestor.fetch_channel_metadata(channel_id)
                    messages = ingestor.fetch_messages(channel_id, limit=200)
                    
                    if not messages:
                        print(f"[!] No messages found in #{ch_name} channel.")
                        continue

                    if not chatbot:
                        chatbot = init_llm_provider_wrapper()
                    if not chatbot:
                        print("[!] Cannot generate digest without an active LLM provider.")
                        continue

                    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                    day_messages = [m for m in messages if datetime.fromtimestamp(m["timestamp"], timezone.utc) > cutoff]

                    if not day_messages:
                        print(f"[!] No messages found in #{ch_name} within the last 24 hours.")
                        continue

                    messages_context = "\n".join([
                        f"[{m['date_str']}] {m['sender']} ({m['username']}): {m['text']} (Link: {m['link']})"
                        for m in reversed(day_messages)
                    ])

                    console = Console()
                    with console.status("[bold green]Generating 24-hour digest...", spinner="dots"):
                        fake_chunk = [{
                            "text": messages_context,
                            "metadata": {"source": f"Discord #{ch_name}", "title": f"24h Digest for {ch_name}"}
                        }]
                        answer = chatbot.generate_answer(f"Provide an executive 24-hour catch-up digest of # {ch_name}.", fake_chunk)
                    
                    console.print(f"\n[bold cyan]24-Hour Digest for #{ch_name} ({server_name}):[/bold cyan]")
                    console.print(Markdown(answer))
                    print()
                except Exception as e:
                    print(f"[!] Failed to generate Discord 24h digest: {e}")
        break
    return chatbot

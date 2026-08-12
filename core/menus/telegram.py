import os
from rich.console import Console
from rich.markdown import Markdown
from ragchat_core.services.telegram.ingestor import TelegramIngestor
from ragchat_core.core.chunker import DocChunker
from ragchat_core.core.config_manager import ConfigManager

def db_safe_profile_name(name):
    import re
    return re.sub(r'[^a-zA-Z0-9]', '_', name)

def select_tg_profile(cfg):
    profiles = cfg.load_tg_profiles()
    if not profiles:
        print("[!] No connected Telegram accounts found. Go to Settings (Option 6) to connect one.")
        return None
    if len(profiles) == 1:
        return list(profiles.keys())[0]
        
    print("\nAvailable Telegram profiles:")
    profile_names = list(profiles.keys())
    for idx, name in enumerate(profile_names):
        print(f"{idx + 1}. {name}")
    sel = input(f"Select profile (1-{len(profile_names)}): ").strip()
    if not sel.isdigit() or int(sel) < 1 or int(sel) > len(profile_names):
        print("[!] Invalid selection.")
        return None
    return profile_names[int(sel) - 1]

def handle_telegram_menu(db, chatbot, cfg):
    from core.menus.settings import init_llm_provider_wrapper
    while True:
        profile = select_tg_profile(cfg)
        if not profile:
            return chatbot

        session_name = cfg.load_tg_profiles()[profile]["session_name"]
        
        while True:
            print(f"\n--- TELEGRAM MENU (Profile: {profile}) ---")
            configured_chs = os.environ.get("TG_CHANNELS", "")
            print(f"1. Sync configured TG_CHANNELS [{configured_chs}]")
            print("2. Index a specific Telegram channel (by username/link/Peer ID)")
            print("3. Generate 24-Hour Channel Catch-Up Digest")
            print("4. Back to main menu")
            
            sub = input("\nSelect option (1-4): ").strip()
            if sub == "4" or sub.lower() in ["back", "b"]:
                break
            
            ingestor = TelegramIngestor(
                api_id=ConfigManager.DEFAULT_TG_API_ID,
                api_hash=ConfigManager.DEFAULT_TG_API_HASH,
                session_name=session_name
            )
            chunker = DocChunker()

            if sub == "1":
                try:
                    ingestor.sync_configured_channels(db, chunker)
                except Exception as e:
                    print(f"[!] Batch sync failed: {e}")
                    
            elif sub == "2":
                channel_input = input("Enter Telegram channel username/link/Peer ID (or type 'back'): ").strip()
                if not channel_input or channel_input.lower() in ["back", "b"]:
                    continue
                    
                limit_input = input("Max messages to fetch (default 500): ").strip()
                limit = int(limit_input) if limit_input.isdigit() else 500

                try:
                    messages, peer_id, channel_title = ingestor.fetch_messages(channel_input, limit=limit)
                    if messages:
                        safe_title = db.sanitize_collection_name(channel_title)
                        collection_name = f"tg_{safe_title}"
                        chunks = chunker.process_telegram_messages(messages)
                        db.add_chunks(collection_name, chunks)
                        print(f"[+] Telegram channel '{channel_title}' indexed into collection '{db.sanitize_collection_name(collection_name)}' successfully!")
                except Exception as e:
                    print(f"[!] Telegram indexing failed: {e}")
                    
            elif sub == "3":
                channel_input = input("Enter Telegram channel username/link/Peer ID (or type 'back'): ").strip()
                if not channel_input or channel_input.lower() in ["back", "b"]:
                    continue

                try:
                    messages, peer_id, channel_title = ingestor.fetch_messages(channel_input, hours=24)
                    
                    if not messages:
                        print(f"[!] No messages found in '{channel_title}' within the last 24 hours.")
                        continue

                    if not chatbot:
                        chatbot = init_llm_provider_wrapper()
                    if not chatbot:
                        print("[!] Cannot generate digest without an active LLM provider.")
                        continue

                    messages_context = "\n".join([
                        f"[{m['date_str']}] {m['sender']}: {m['text']} (Link: {m['link']})"
                        for m in reversed(messages)
                    ])

                    console = Console()
                    with console.status("[bold green]Generating 24-hour digest...", spinner="dots"):
                        fake_chunk = [{
                            "text": messages_context,
                            "metadata": {"source": f"Telegram @{channel_title}", "title": f"24h Digest for {channel_title}"}
                        }]
                        answer = chatbot.generate_answer("Provide an executive 24-hour catch-up digest of this channel activity.", fake_chunk)
                    
                    console.print(f"\n[bold cyan]24-Hour Digest for '{channel_title}':[/bold cyan]")
                    console.print(Markdown(answer))
                    print()
                except Exception as e:
                    print(f"[!] Failed to generate 24h digest: {e}")
        break
    return chatbot

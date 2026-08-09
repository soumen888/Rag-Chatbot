import os
import sys
import getpass
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.markdown import Markdown
from urllib.parse import urlparse

from website import DocCrawler
from telegram import TelegramIngestor
from discord import DiscordIngestor
from core.chunker import DocChunker
from core.chatbot import get_provider, PROVIDER_INFO
from core.config_manager import ConfigManager

def format_col_display(col_name):
    """Formats a ChromaDB collection name for display in menus."""
    if col_name == "telegram_all":
        return "Telegram: All Channels (telegram_all)"
    elif col_name.startswith("tg_"):
        raw_name = col_name[3:].replace("_", " ").title()
        return f"Telegram: {raw_name} ({col_name})"
    elif col_name.startswith("ds_"):
        raw_name = col_name[3:].replace("_", " ").title()
        return f"Discord: {raw_name} ({col_name})"
    else:
        return f"Docs: {col_name}"

def init_llm_provider_wrapper():
    """Wrapper to initialize LLM provider."""
    provider_name = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if not provider_name:
        return None
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "").strip()

    info = PROVIDER_INFO.get(provider_name, {})
    provider_display = info.get("name", provider_name)
    local_providers = {"ollama", "lmstudio"}

    if provider_name not in local_providers and not api_key:
        return None

    if model:
        os.environ["LLM_MODEL"] = model
    if base_url:
        os.environ["LLM_BASE_URL"] = base_url

    try:
        provider = get_provider()
        effective_model = model or info.get("model_default", "")
        print(f"[+] LLM Provider: {provider_display} | Model: {effective_model}")
        return provider
    except Exception:
        return None

def interactive_setup_wizard(cfg):
    """Wizard triggered when no LLM credentials exist in .env."""
    print("\n==================================================")
    print("           First-Time Setup Wizard                ")
    print("==================================================")
    print("To use RAGChat, let's configure your LLM provider.")
    
    print("\nSelect your LLM Provider:")
    providers = list(PROVIDER_INFO.keys())
    for idx, p in enumerate(providers):
        name = PROVIDER_INFO[p]["name"]
        default_model = PROVIDER_INFO[p]["model_default"]
        print(f"{idx + 1}. {name} (Default: {default_model})")
        
    choice = input(f"Select provider (1-{len(providers)}): ").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(providers):
        print("[!] Invalid choice. Defaulting to Google AI Studio.")
        selected = "google"
    else:
        selected = providers[int(choice) - 1]
        
    cfg.write_env_var("LLM_PROVIDER", selected)
    
    local_providers = {"ollama", "lmstudio"}
    if selected not in local_providers:
        key = getpass.getpass(f"Enter your API key for {PROVIDER_INFO[selected]['name']}: ").strip()
        cfg.write_env_var("LLM_API_KEY", key)
        
    print("[+] Configuration completed! Saved to .env.")

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

def handle_website_menu(db):
    while True:
        print("\n--- WEBSITE MENU ---")
        print("1. Crawl & Index a new documentation site")
        print("2. Back to main menu")
        
        sub = input("\nSelect option (1-2): ").strip()
        if sub == "2" or sub.lower() in ["back", "b"]:
            break
        if sub != "1":
            continue

        url = input("Enter documentation base URL (or type 'back' to cancel): ").strip()
        if not url or url.lower() in ["back", "b"]:
            continue
            
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            print("[!] Invalid URL scheme or domain.")
            continue
            
        collection_name = parsed.netloc
        safe_col_name = db.sanitize_collection_name(collection_name)
        
        cache_dir = "./.crawl_cache"
        cache_file = os.path.join(cache_dir, f"{safe_col_name}.json")
        
        resume = False
        if os.path.exists(cache_file):
            print(f"\n[!] Found previous crawl state for '{safe_col_name}'.")
            print("1. Resume crawling (crawl new pages, append to database)")
            print("2. Start fresh (delete existing collection & cache, crawl from scratch)")
            print("3. Back to main menu")
            sub_choice = input("Select option (1-3, default 1): ").strip()
            if sub_choice == "3" or sub_choice.lower() in ["back", "b"]:
                continue
            elif sub_choice == "2":
                print(f"[*] Deleting existing collection and cache for '{safe_col_name}'...")
                db.delete_collection(collection_name)
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except Exception:
                        pass
            else:
                resume = True
        
        max_pages_input = input("Max pages to crawl this session (default 50): ").strip()
        max_pages = int(max_pages_input) if max_pages_input.isdigit() else 50
        
        crawler = DocCrawler(base_url=url, max_pages=max_pages)
        if resume:
            crawler.load_state(cache_file)
            
        pages = crawler.crawl()
        
        if not pages:
            print("[!] No new pages crawled this session.")
            if resume:
                crawler.save_state(cache_file)
            continue
            
        print("[*] Parsing and chunking HTML content...")
        chunker = DocChunker()
        chunks = chunker.process_pages(pages)
        print(f"[+] Created {len(chunks)} chunks from {len(pages)} new pages.")
        
        db.add_chunks(collection_name, chunks)
        crawler.save_state(cache_file)
        print(f"[+] Collection '{safe_col_name}' is ready to chat!")

def handle_telegram_menu(db, chatbot, cfg):
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

def handle_discord_menu(db, chatbot, cfg):
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

def handle_chat_menu(db, chatbot):
    from main import print_system_stats
    collections = db.list_collections()
    if not collections:
        print("[!] No indexed collections found. Please index a website or Telegram/Discord channel first.")
        return chatbot
        
    print("\nAvailable indexed collections:")
    print("0. Back to main menu")
    for idx, col in enumerate(collections):
        print(f"{idx + 1}. {format_col_display(col)}")
        
    sel = input(f"Select a collection to chat (0-{len(collections)}): ").strip()
    if sel == "0" or sel.lower() in ["back", "b"]:
        return chatbot
    if not sel.isdigit() or int(sel) < 1 or int(sel) > len(collections):
        print("[!] Invalid selection.")
        return chatbot
        
    selected_collection = collections[int(sel) - 1]
    print(f"\n[+] Started chat session with '{format_col_display(selected_collection)}'")
    print("Type 'exit' or 'back' to return to the main menu.\n")
    
    if not chatbot:
        chatbot = init_llm_provider_wrapper()
    if not chatbot:
        print("[!] Cannot start chat without a configured LLM provider.")
        return chatbot
            
    console = Console()
    while True:
        user_query = input("You: ").strip()
        if not user_query:
            continue
        if user_query.lower() in ["exit", "back", "b"]:
            break
            
        with console.status("[bold cyan]Searching knowledge base...", spinner="dots"):
            results = db.query(selected_collection, user_query, n_results=10)
        
        if not results:
            console.print("[yellow]Bot: No relevant context found in database.[/yellow]")
            continue
            
        with console.status("[bold green]Formulating answer...", spinner="dots"):
            answer = chatbot.generate_answer(user_query, results)
            
        console.print("\n[bold cyan]Bot:[/bold cyan]")
        console.print(Markdown(answer))
        print()
        console.print(f"[dim][SYSTEM] {print_system_stats()}[/dim]")
        print()

    return chatbot

def handle_collections_menu(db):
    while True:
        print("\n--- COLLECTIONS MENU ---")
        print("1. List all indexed collections")
        print("2. Delete an indexed collection")
        print("3. Back to main menu")
        
        sub = input("\nSelect option (1-3): ").strip()
        if sub == "3" or sub.lower() in ["back", "b"]:
            break
        
        if sub == "1":
            collections = db.list_collections()
            if not collections:
                print("[!] No indexed collections found.")
            else:
                print("\nIndexed collections:")
                for col in collections:
                    print(f"- {format_col_display(col)}")
                    
        elif sub == "2":
            collections = db.list_collections()
            if not collections:
                print("[!] No indexed collections found.")
                continue
                
            print("\nAvailable indexed collections:")
            print("0. Back to main menu")
            for idx, col in enumerate(collections):
                print(f"{idx + 1}. {format_col_display(col)}")
                
            sel = input(f"Select a collection to delete (0-{len(collections)}): ").strip()
            if sel == "0" or sel.lower() in ["back", "b"]:
                continue
            if not sel.isdigit() or int(sel) < 1 or int(sel) > len(collections):
                print("[!] Invalid selection.")
                continue
                
            col_to_delete = collections[int(sel) - 1]
            confirm = input(f"Are you sure you want to delete '{format_col_display(col_to_delete)}'? (y/n): ").strip().lower()
            if confirm == 'y':
                db.delete_collection(col_to_delete)
                cache_file = os.path.join("./.crawl_cache", f"{col_to_delete}.json")
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except Exception:
                        pass

def handle_settings_menu(cfg):
    while True:
        print("\n--- SETTINGS & ACCOUNT CONNECTIONS ---")
        print("1. Add / Link a Telegram account")
        print("2. Add / Link a Discord account")
        print("3. List connected accounts")
        print("4. Remove a connected account")
        print("5. Change LLM Provider or API Key")
        print("6. Back to main menu")

        sub = input("\nSelect option (1-6): ").strip()
        if sub == "6" or sub.lower() in ["back", "b"]:
            break

        if sub == "1":
            profile_name = input("Enter a label for this Telegram profile (e.g. personal, work): ").strip()
            if not profile_name:
                print("[!] Profile name is required.")
                continue
            session_file = f"tg_session_{db_safe_profile_name(profile_name)}"
            
            ingestor = TelegramIngestor(
                api_id=ConfigManager.DEFAULT_TG_API_ID,
                api_hash=ConfigManager.DEFAULT_TG_API_HASH,
                session_name=session_file
            )
            try:
                ingestor.connect()
                cfg.add_tg_profile(profile_name, session_file)
                print(f"[+] Telegram profile '{profile_name}' successfully connected!")
            except Exception as e:
                print(f"[!] Authorization failed: {e}")

        elif sub == "2":
            profile_name = input("Enter a label for this Discord profile (e.g. personal, work): ").strip()
            if not profile_name:
                print("[!] Profile name is required.")
                continue

            print("\nSelect Discord connection mode:")
            print("1. Admin Bot (Requires Bot Token)")
            print("2. Paste Discord User Token directly")
            mode = input("Select (1-2): ").strip()

            if mode == "1":
                token = getpass.getpass("Enter Discord Bot Token: ").strip()
                if token:
                    cfg.add_ds_profile(profile_name, token, is_bot=True)
                    print(f"[+] Discord bot profile '{profile_name}' added!")
            elif mode == "2":
                token = getpass.getpass("Enter Discord User Token: ").strip()
                if token:
                    cfg.add_ds_profile(profile_name, token, is_bot=False)
                    print(f"[+] Discord user profile '{profile_name}' added!")

        elif sub == "3":
            tg = cfg.load_tg_profiles()
            ds = cfg.load_ds_profiles()
            print("\nConnected Telegram Accounts:")
            if not tg:
                print("  - None")
            for name in tg:
                print(f"  - {name}")

            print("\nConnected Discord Accounts:")
            if not ds:
                print("  - None")
            for name in ds:
                is_bot = " (Bot)" if ds[name].get("is_bot") else " (User)"
                print(f"  - {name}{is_bot}")

        elif sub == "4":
            print("\n1. Remove Telegram Profile")
            print("2. Remove Discord Profile")
            ch = input("Select (1-2): ").strip()
            if ch == "1":
                name = input("Enter profile label to delete: ").strip()
                if cfg.delete_tg_profile(name):
                    print(f"[+] Profile '{name}' removed.")
                else:
                    print("[!] Profile not found.")
            elif ch == "2":
                name = input("Enter profile label to delete: ").strip()
                if cfg.delete_ds_profile(name):
                    print(f"[+] Profile '{name}' removed.")
                else:
                    print("[!] Profile not found.")

        elif sub == "5":
            interactive_setup_wizard(cfg)

def db_safe_profile_name(name):
    import re
    return re.sub(r'[^a-zA-Z0-9]', '_', name)

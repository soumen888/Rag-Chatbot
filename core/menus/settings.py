import os
import sys
import getpass
from dotenv import load_dotenv
from core.chatbot import get_provider, PROVIDER_INFO
from core.config_manager import ConfigManager
from services.google.auth import GoogleAuthManager
from services.microsoft.auth import MicrosoftAuthManager
from services.telegram import TelegramIngestor

def db_safe_profile_name(name):
    import re
    return re.sub(r'[^a-zA-Z0-9]', '_', name)

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
    print("               LLM Setup Wizard                   ")
    print("==================================================")
    
    print("\nSelect your LLM Provider:")
    providers = list(PROVIDER_INFO.keys())
    for idx, p in enumerate(providers):
        print(f"{idx + 1}. {PROVIDER_INFO[p]['name']}")
    print("0. Skip setup for now")
        
    choice = input(f"Select provider (0-{len(providers)}) or 'skip': ").strip().lower()
    if choice in ["0", "skip", "s"]:
        print("[*] Setup skipped. You can configure your provider anytime under Settings (Option 6).")
        return

    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(providers):
        print("[!] Invalid choice. Defaulting to Google AI Studio.")
        selected_provider = "google"
    else:
        selected_provider = providers[int(choice) - 1]

    # Pre-indexed LiteLLM model directory mapping (model_name, provider_key)
    import litellm
    common_models = []
    try:
        for provider, models in litellm.models_by_provider.items():
            prov_key = provider.lower()
            if prov_key == "gemini":
                prov_key = "google"
            elif prov_key == "openai":
                prov_key = "openai"
                
            for m in models:
                common_models.append((m, prov_key))
    except Exception:
        # Fallback to standard core models if litellm registry structure changes
        common_models = [
            ("gemini-1.5-flash", "google"), ("gemini-1.5-pro", "google"),
            ("gpt-4o-mini", "openai"), ("gpt-4o", "openai"),
            ("claude-3-5-sonnet-20241022", "anthropic"), ("claude-3-5-haiku-20241022", "anthropic"),
            ("groq/llama-3.3-70b-versatile", "groq"), ("groq/llama-3.1-70b-versatile", "groq")
        ]

    # Filter common models by selected provider
    provider_models = [m for m in common_models if m[1] == selected_provider]
    prov_name_display = PROVIDER_INFO.get(selected_provider, {}).get("name", selected_provider)

    print(f"\nSearch for a model hosted on {prov_name_display} (e.g. flash, gpt4, claude, local):")
    search_query = input("Model Search: ").strip().lower()
    
    # Split search query for flexible partial matching
    query_parts = search_query.split()
    matches = []
    for m in provider_models:
        model_name_lower = m[0].lower()
        if all(part in model_name_lower for part in query_parts):
            matches.append(m)
            
    selected_model = None
    
    if matches:
        print(f"\nMatching models for {prov_name_display}:")
        for idx, match in enumerate(matches):
            # Clean display name (strip provider prefixes if they exist)
            display_name = match[0]
            if display_name.startswith(selected_provider + "/"):
                display_name = display_name[len(selected_provider) + 1:]
            elif selected_provider == "google" and display_name.startswith("gemini/"):
                display_name = display_name[7:]
            print(f"{idx + 1}. {display_name}")
        print(f"{len(matches) + 1}. Enter custom model name string manually")
        
        sel = input(f"Select option (1-{len(matches) + 1}, default 1): ").strip()
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(matches):
                selected_model = matches[idx][0]
            elif idx == len(matches):
                selected_model = input("Enter custom model name: ").strip()
        else:
            selected_model = matches[0][0]
    else:
        print(f"[-] No matching models found under {prov_name_display}.")
        selected_model = input("Enter custom model name manually: ").strip()
        
    # Auto-prefix Google/Gemini models if needed for LiteLLM format
    if selected_provider == "google" and not selected_model.startswith("gemini/") and not "/" in selected_model:
        selected_model = f"gemini/{selected_model}"
            
    # Save provider and model variables
    cfg.write_env_var("LLM_PROVIDER", selected_provider)
    cfg.write_env_var("LLM_MODEL", selected_model)
    os.environ["LLM_PROVIDER"] = selected_provider
    os.environ["LLM_MODEL"] = selected_model
    
    # 3. Prompt for API Key (if not a local provider)
    local_providers = {"ollama", "lmstudio"}
    if selected_provider not in local_providers:
        prov_display = PROVIDER_INFO.get(selected_provider, {}).get("name", selected_provider)
        key = getpass.getpass(f"\nEnter API key for {prov_display}: ").strip()
        cfg.write_env_var("LLM_API_KEY", key)
        os.environ["LLM_API_KEY"] = key
        
    # 4. Handle base URL if LM Studio or Ollama is selected
    if selected_provider in local_providers:
        default_url = "http://localhost:11434" if selected_provider == "ollama" else "http://localhost:1234/v1"
        url = input(f"\nEnter local API endpoint (default {default_url}): ").strip()
        url_val = url if url else default_url
        cfg.write_env_var("LLM_BASE_URL", url_val)
        os.environ["LLM_BASE_URL"] = url_val
        
    print("[+] Configuration completed! Saved and loaded dynamically into environment.")

def handle_settings_menu(cfg):
    g_manager = GoogleAuthManager()
    ms_manager = MicrosoftAuthManager()
    
    while True:
        print("\n--- SETTINGS & ACCOUNT CONNECTIONS ---")
        print("1. Add / Link a Telegram account")
        print("2. Add / Link a Discord account")
        print("3. Add / Link a Google account")
        print("4. Add / Link a Microsoft account")
        print("5. List connected accounts")
        print("6. Remove a connected account")
        print("7. Change LLM Provider or API Key")
        print("8. Back to main menu")

        sub = input("\nSelect option (1-8): ").strip()
        if sub == "8" or sub.lower() in ["back", "b"]:
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

            from core.cli.auth import prompt_discord_linking_flow
            prompt_discord_linking_flow(profile_name, cfg)

        elif sub == "3":
            profile_name = input("Enter a label for this Google profile (e.g. personal, work): ").strip()
            if not profile_name:
                print("[!] Profile name is required.")
                continue
            try:
                g_manager.authenticate_profile(profile_name)
                print(f"[+] Google profile '{profile_name}' successfully linked!")
            except Exception as e:
                print(f"[!] Google authorization failed: {e}")

        elif sub == "4":
            profile_name = input("Enter a label for this Microsoft profile (e.g. personal, work): ").strip()
            if not profile_name:
                print("[!] Profile name is required.")
                continue
            try:
                ms_manager.authenticate_profile(profile_name)
                print(f"[+] Microsoft profile '{profile_name}' successfully linked!")
            except Exception as e:
                print(f"[!] Microsoft authorization failed: {e}")

        elif sub == "5":
            tg = cfg.load_tg_profiles()
            ds = cfg.load_ds_profiles()
            google_accs = g_manager.list_profiles()
            ms_accs = ms_manager.list_profiles()
            
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
                
            print("\nConnected Google Accounts:")
            if not google_accs:
                print("  - None")
            for name in google_accs:
                print(f"  - {name}")

            print("\nConnected Microsoft Accounts:")
            if not ms_accs:
                print("  - None")
            for name in ms_accs:
                print(f"  - {name}")

        elif sub == "6":
            print("\n1. Remove Telegram Profile")
            print("2. Remove Discord Profile")
            print("3. Remove Google Profile")
            print("4. Remove Microsoft Profile")
            ch = input("Select (1-4): ").strip()
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
            elif ch == "3":
                name = input("Enter profile label to delete: ").strip()
                if g_manager.delete_profile(name):
                    print(f"[+] Google profile '{name}' removed.")
                else:
                    print("[!] Profile not found.")
            elif ch == "4":
                name = input("Enter profile label to delete: ").strip()
                if ms_manager.delete_profile(name):
                    print(f"[+] Microsoft profile '{name}' removed.")
                else:
                    print("[!] Profile not found.")

        elif sub == "7":
            interactive_setup_wizard(cfg)
            load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../.env'), override=True)

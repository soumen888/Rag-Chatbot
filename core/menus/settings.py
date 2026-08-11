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
    print("           First-Time Setup Wizard                ")
    print("==================================================")
    print("To use RAGChat, let's configure your LLM provider.")
    
    print("\nSelect your LLM Provider:")
    providers = list(PROVIDER_INFO.keys())
    for idx, p in enumerate(providers):
        name = PROVIDER_INFO[p]["name"]
        default_model = PROVIDER_INFO[p]["model_default"]
        print(f"{idx + 1}. {name} (Default: {default_model})")
    print("0. Skip setup for now")
        
    choice = input(f"Select provider (0-{len(providers)}) or 'skip': ").strip().lower()
    if choice in ["0", "skip", "s"]:
        print("[*] Setup skipped. You can configure your provider anytime under Settings (Option 6).")
        return

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

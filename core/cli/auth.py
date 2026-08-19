import os
import sys
import getpass
try:
    from core.config_manager import ConfigManager
    from core.db import LocalDB
    from services.google.auth import GoogleAuthManager
    from services.microsoft.auth import MicrosoftAuthManager
    from services.telegram.ingestor import TelegramIngestor
except ImportError:
    from ragchat_core.core.config_manager import ConfigManager
    from ragchat_core.core.db import LocalDB
    from ragchat_core.services.google.auth import GoogleAuthManager
    from ragchat_core.services.microsoft.auth import MicrosoftAuthManager
    from ragchat_core.services.telegram.ingestor import TelegramIngestor

def db_safe_profile_name(name):
    import re
    return re.sub(r'[^a-zA-Z0-9]', '_', name)

def handle_rename_profile_cli(args):
    """Handles profile renaming operations."""
    if len(args) < 4:
        print("[!] Usage: ragchat rename-profile <service> <old_name> <new_name>")
        sys.exit(1)
    service = args[1].lower()
    old_name = args[2]
    new_name = args[3]

    if service not in ['google', 'microsoft']:
        print(f"[!] Unsupported service for rename: '{service}'. Only 'google' and 'microsoft' are supported.")
        sys.exit(1)

    try:
        if service == 'google':
            auth = GoogleAuthManager()
        else:
            auth = MicrosoftAuthManager()

        success = auth.rename_profile(old_name, new_name)
        if not success:
            print(f"[!] Failed to rename credential profile. Check if profile '{old_name}' exists.")
            sys.exit(1)

        db = LocalDB()
        db.rename_profile(service, old_name, new_name)
        print(f"[+] Successfully renamed {service} profile '{old_name}' to '{new_name}' across credentials and database!")
    except Exception as e:
        print(f"[!] Error during rename-profile: {e}")
    sys.exit(0)

def handle_list_profiles_cli(args):
    """Lists all linked profiles for a service."""
    service = 'google'
    if len(args) >= 2:
        service = args[1].lower()
    
    try:
        if service == 'google':
            auth = GoogleAuthManager()
        elif service == 'microsoft':
            auth = MicrosoftAuthManager()
        else:
            print(f"[!] Unsupported service: '{service}'")
            sys.exit(1)
            
        profiles = auth.list_profiles()
        print(f"\n[+] Linked {service.capitalize()} Profiles ({len(profiles)}):")
        if profiles:
            for p in profiles:
                print(f"    • {p}")
        else:
            print(f"    (No profiles linked yet. Run 'ragchat link {service} <profile_name>')")
        print()
    except Exception as e:
        print(f"[!] Error listing profiles: {e}")
    sys.exit(0)

def prompt_discord_linking_flow(profile_name, cfg):
    """Walks the user through connecting a Discord account (Bot or User token)."""
    print("\nSelect Discord connection mode:")
    print("1. Admin Bot (Requires Bot Token - Best for Server Admins)")
    print("2. Discord User Token (Best for normal users / VPS deployments)")
    mode = input("Select (1-2): ").strip()
    
    if mode == "2":
        print("\n" + "="*70)
        print("          HOW TO GET YOUR DISCORD USER TOKEN (NO BROWSER NEEDED ON VPS)")
        print("="*70)
        print("1. Open Discord in your desktop web browser (Chrome/Firefox) and log in.")
        print("2. Press F12 (Cmd+Opt+I on Mac) to open Developer Tools.")
        print("3. Go to the 'Network' tab.")
        print("4. Click on any channel or send a message to trigger network activity.")
        print("5. Search the network list for a request named 'science' or 'messages'.")
        print("6. Click on it, look at the 'Request Headers', and copy the 'Authorization' value.")
        print("   (It should look like a long string of random characters).")
        print("="*70)
        print("⚠️  SECURITY WARNING:")
        print("   Your Token gives FULL access to your Discord account.")
        print("   - NEVER share this token with anyone.")
        print("   - If leaked, change your Discord Password immediately to revoke it.")
        print("="*70 + "\n")

    token = getpass.getpass("Enter Discord Token: ").strip()
    if token:
        is_bot = (mode == "1")
        cfg.add_ds_profile(profile_name, token, is_bot=is_bot)
        print(f"[+] Discord profile '{profile_name}' successfully connected!")
    else:
        print("[!] Token cannot be empty.")

def listen_for_vercel_oauth(service, profile_name, port=8080):
    """Spins up a local HTTP listener and opens Vercel Auth Gateway in browser."""
    import webbrowser
    import urllib.parse
    from http.server import HTTPServer, BaseHTTPRequestHandler

    auth_data = {}

    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if 'access_token' in params or 'refresh_token' in params:
                auth_data['access_token'] = params.get('access_token', [''])[0]
                auth_data['refresh_token'] = params.get('refresh_token', [''])[0]
                auth_data['provider'] = params.get('provider', [service])[0]
                auth_data['profile'] = params.get('profile', [profile_name])[0]

                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                html = """
                <html>
                <body style="font-family: system-ui; background: #000; color: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;">
                  <div style="text-align: center; border: 1px solid #27272a; padding: 30px; border-radius: 12px; background: #09090b;">
                    <h2 style="color: #38bdf8; margin-top: 0;">Authentication Successful!</h2>
                    <p style="color: #a1a1aa;">RAGChat account profile has been linked. You can close this browser tab and return to your terminal.</p>
                  </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authentication failed.")

        def log_message(self, format, *args):
            pass

    server = HTTPServer(('127.0.0.1', port), OAuthCallbackHandler)
    gateway_url = f"https://ragchat-beta.vercel.app/api/auth/{service}?port={port}&profile={profile_name}"
    
    print(f"[*] Opening Vercel Auth Gateway in your browser...")
    print(f"[*] Gateway URL: {gateway_url}")
    webbrowser.open(gateway_url)

    server.handle_request()
    return auth_data

MAX_PROFILES_PER_SERVICE = 20

def check_profile_limit(auth_manager, service_name, new_profile_name):
    existing = auth_manager.list_profiles()
    if new_profile_name not in existing and len(existing) >= MAX_PROFILES_PER_SERVICE:
        print(f"[!] Profile limit reached: RAGChat limits to {MAX_PROFILES_PER_SERVICE} profiles per service.")
        print(f"    Current {service_name.capitalize()} profiles ({len(existing)}/{MAX_PROFILES_PER_SERVICE}): {', '.join(existing)}")
        print(f"    To add a new profile, delete an existing profile first using: ragchat delete-profile {service_name} <profile_name>")
        sys.exit(1)

def handle_link_cli(args):
    """Handles authorization link configurations."""
    if len(args) < 3:
        print("[!] Usage: ragchat link <service> <profile_name> (e.g. link google dev)")
        sys.exit(1)
    
    service = args[1].lower()
    profile_name = args[2]
    cfg = ConfigManager()

    if service in ['google', 'microsoft']:
        try:
            if service == 'google':
                g_manager = GoogleAuthManager()
                check_profile_limit(g_manager, service, profile_name)
                g_manager.authenticate_profile(profile_name)
                print(f"[+] Google profile '{profile_name}' successfully linked locally!")
            else:
                ms_manager = MicrosoftAuthManager()
                check_profile_limit(ms_manager, service, profile_name)
                auth_data = listen_for_vercel_oauth(service, profile_name)
                if auth_data.get('access_token') or auth_data.get('refresh_token'):
                    accounts = ms_manager._load_accounts()
                    accounts[profile_name] = {
                        "token": auth_data.get('access_token'),
                        "refresh_token": auth_data.get('refresh_token')
                    }
                    ms_manager._save_accounts(accounts)
                    print(f"[+] Microsoft profile '{profile_name}' successfully linked via Vercel Gateway!")
                else:
                    print(f"[!] Microsoft authorization failed or timed out.")
        except Exception as e:
            print(f"[!] Authorization error: {e}")
        sys.exit(0)

    elif service == 'telegram':
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
        sys.exit(0)

    elif service == 'discord':
        prompt_discord_linking_flow(profile_name, cfg)
        sys.exit(0)

def clean_file_path(path_str):
    """Cleans up dragged-and-dropped or user-entered file paths."""
    if not path_str:
        return ""
    cleaned = path_str.strip().strip("'\"")
    cleaned = cleaned.replace("\\ ", " ")
    return os.path.expanduser(cleaned)

def find_downloads_google_json():
    """Scans ~/Downloads for any Google client_secret JSON files."""
    downloads_dir = os.path.expanduser("~/Downloads")
    if not os.path.exists(downloads_dir):
        return None
    import glob
    candidates = glob.glob(os.path.join(downloads_dir, "client_secret_*.json"))
    if not candidates:
        candidates = glob.glob(os.path.join(downloads_dir, "credentials*.json"))
    if candidates:
        candidates.sort(key=os.path.getmtime, reverse=True)
        return candidates[0]
    return None

def display_gcp_onboarding_guide():
    """Displays step-by-step GCP OAuth setup guide with direct links."""
    print("\n" + "="*75)
    print("                 GOOGLE OAUTH EASY SETUP ASSISTANT")
    print("="*75)
    print("Google requires a 1-time setup for personal OAuth keys (free & instant):\n")
    print("Step 1: Create a Google Cloud Project (10 seconds):")
    print("        👉 https://console.cloud.google.com/projectcreate")
    print("        • Project Name: Type 'Ragchat' -> Click 'CREATE'\n")
    print("Step 2: Configure OAuth Consent Screen:")
    print("        👉 https://console.cloud.google.com/apis/credentials/consent")
    print("        1. App Information  : Type App Name 'Ragchat' & select your email")
    print("        2. Audience         : Select 'External' -> Click 'Next'")
    print("        3. Contact Info     : Type your email address")
    print("        4. Finish           : Click 'CREATE'\n")
    print("Step 3: Create & Download Desktop OAuth Client JSON:")
    print("        👉 https://console.cloud.google.com/apis/credentials")
    print("        • Click '+ CREATE CREDENTIALS' -> 'OAuth client ID'")
    print("        • Application type: Select 'Desktop app'")
    print("        • Name: Type 'Ragchat Desktop'")
    print("        • Click 'CREATE' -> Click 'DOWNLOAD JSON'\n")
    print("Step 4: Add your email to Test Users (Audience):")
    print("        👉 https://console.cloud.google.com/auth/audience")
    print("        • Click '+ ADD USERS' and type your email address.\n")
    print("="*75)

def handle_bind_cli(args):
    """
    Handles binding custom OAuth credentials JSON files.
    Usage:
      ragchat bind google [file_path] [profile_name]
      ragchat bind [file_path]
    """
    import os
    import json
    
    file_path = None
    profile_name = "default"

    rem_args = args[1:]
    if rem_args and rem_args[0].lower() in ['google', 'gcp']:
        rem_args = rem_args[1:]
    
    if len(rem_args) >= 1:
        file_path = clean_file_path(rem_args[0])
    if len(rem_args) >= 2:
        profile_name = rem_args[1]

    if not file_path or not os.path.exists(file_path):
        auto_file = find_downloads_google_json()
        if auto_file:
            print(f"[+] Auto-detected Google credentials in Downloads:\n    {auto_file}")
            confirm = input("[?] Would you like to bind this file? [Y/n]: ").strip().lower()
            if confirm in ['', 'y', 'yes']:
                file_path = auto_file

    if not file_path or not os.path.exists(file_path):
        display_gcp_onboarding_guide()
        while True:
            raw_input = input("\n[?] Drag & drop or type your JSON file location (or 'q' to quit): ").strip()
            if raw_input.lower() in ['q', 'quit', 'exit']:
                print("[!] Binding cancelled.")
                sys.exit(0)
            candidate = clean_file_path(raw_input)
            if candidate and os.path.exists(candidate):
                file_path = candidate
                break
            print(f"[!] File not found: '{candidate}'. Please check the path and try again.")

    try:
        with open(file_path, 'r') as f:
            json_data = json.load(f)

        data = json_data.get("installed") or json_data.get("web")
        if not data or "client_id" not in data or "client_secret" not in data:
            print("[!] Invalid Google OAuth JSON format. Must contain 'installed' or 'web' with 'client_id' and 'client_secret'.")
            sys.exit(1)

        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        project_id = data.get("project_id", "")

        cfg = ConfigManager()
        cfg.write_env_var("GOOGLE_CLIENT_ID", client_id)
        cfg.write_env_var("GOOGLE_CLIENT_SECRET", client_secret)
        if project_id:
            cfg.write_env_var("GOOGLE_PROJECT_ID", project_id)

        if hasattr(cfg, 'save_google_client_secrets'):
            cfg.save_google_client_secrets(json_data)
        else:
            config_dir = os.path.expanduser("~/.config/ragchat")
            os.makedirs(config_dir, exist_ok=True)
            secrets_path = os.path.join(config_dir, "client_secrets.json")
            with open(secrets_path, "w") as f:
                json.dump(json_data, f, indent=2)
            os.chmod(secrets_path, 0o600)

        try:
            with open("client_secrets.json", "w") as f:
                json.dump(json_data, f, indent=2)
        except Exception:
            pass

        print(f"\n[+] Successfully bound Google OAuth credentials!")
        print(f"    • Client ID: {client_id[:25]}...")
        if project_id:
            print(f"    • Project ID: {project_id}")
            print(f"\n[!] GCP Audience Whitelist Link (1-click to authorize test users):")
            print(f"    👉 https://console.cloud.google.com/auth/audience?project={project_id}")

        print("\n" + "─"*75)
        print("💡 GOOGLE OAUTH SECURITY SCREEN NOTICE:")
        print("   Google will display a screen saying: \"Google hasn't verified this app\".")
        print("   • DO NOT WORRY: This is expected since you are using your own personal OAuth keys!")
        print("   • HOW TO PROCEED: Click 'Advanced' -> Click 'Go to Ragchat (unsafe)' -> 'Continue'.")
        print("─"*75)

        print("\n[*] Launching local OAuth authorization page in your browser...")
        g_manager = GoogleAuthManager()
        g_manager.authenticate_profile(profile_name)
        print(f"[+] Google profile '{profile_name}' successfully linked and ready to use!")

    except Exception as e:
        print(f"[!] Error during Google OAuth binding: {e}")
        sys.exit(1)
    
    sys.exit(0)

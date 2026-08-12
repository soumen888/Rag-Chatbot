import sys
import getpass
from core.config_manager import ConfigManager
from core.db import LocalDB
from services.google.auth import GoogleAuthManager
from services.microsoft.auth import MicrosoftAuthManager
from services.telegram.ingestor import TelegramIngestor

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
            auth_data = listen_for_vercel_oauth(service, profile_name)
            if auth_data.get('access_token') or auth_data.get('refresh_token'):
                if service == 'google':
                    auth = GoogleAuthManager()
                    accounts = auth._load_accounts()
                    accounts[profile_name] = {
                        "token": auth_data.get('access_token'),
                        "refresh_token": auth_data.get('refresh_token')
                    }
                    auth._save_accounts(accounts)
                else:
                    auth = MicrosoftAuthManager()
                    accounts = auth._load_accounts()
                    accounts[profile_name] = {
                        "token": auth_data.get('access_token'),
                        "refresh_token": auth_data.get('refresh_token')
                    }
                    auth._save_accounts(accounts)
                print(f"[+] {service.capitalize()} profile '{profile_name}' successfully linked via Vercel Gateway!")
            else:
                print(f"[!] {service.capitalize()} authorization failed or timed out.")
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

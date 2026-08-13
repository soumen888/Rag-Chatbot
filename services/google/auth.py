import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Scopes needed for Gmail, Calendar, Tasks, Drive, Sheets, Docs, Slides, and YouTube
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",       # Read/Write/Delete Mail
    "https://www.googleapis.com/auth/calendar",           # Read/Write Calendar (including Meet generation)
    "https://www.googleapis.com/auth/tasks",              # Read/Write Tasks
    "https://www.googleapis.com/auth/drive",              # Full access to Drive
    "https://www.googleapis.com/auth/spreadsheets",       # Read/Write Sheets
    "https://www.googleapis.com/auth/documents",          # Read/Write Docs
    "https://www.googleapis.com/auth/presentations",      # Read/Write Slides
    "https://www.googleapis.com/auth/youtube.readonly"    # Read YouTube data
]

OAUTH_SUCCESS_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>RAGChat - Google Account Connected</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #09090b; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .card { background: #18181b; border: 1px solid #27272a; border-radius: 16px; padding: 40px; text-align: center; max-width: 480px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); }
    .icon { width: 64px; height: 64px; background: #10b981; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; margin: 0 auto 20px; box-shadow: 0 0 20px rgba(16, 185, 129, 0.4); }
    h1 { margin: 0 0 8px; font-size: 22px; color: #ffffff; font-weight: 700; }
    p { color: #a1a1aa; font-size: 14px; margin-bottom: 24px; line-height: 1.5; }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 24px; text-align: left; }
    .badge { background: #27272a; border: 1px solid #3f3f46; padding: 10px 14px; border-radius: 10px; font-size: 13px; color: #38bdf8; display: flex; align-items: center; gap: 8px; font-weight: 500; }
    .btn { display: inline-block; background: #ffffff; color: #000000; text-decoration: none; padding: 12px 28px; border-radius: 10px; font-weight: 600; font-size: 14px; transition: all 0.2s ease; margin-top: 10px; }
    .btn:hover { background: #e4e4e7; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✓</div>
    <h1>Google Account Connected!</h1>
    <p>Your Google profile has been linked to RAGChat. You can now access your workspace data seamlessly.</p>
    <div class="grid">
      <div class="badge"><span>✉️</span> Gmail</div>
      <div class="badge"><span>📁</span> Google Drive</div>
      <div class="badge"><span>📊</span> Google Sheets</div>
      <div class="badge"><span>📄</span> Google Docs</div>
      <div class="badge"><span>🖼️</span> Google Slides</div>
      <div class="badge"><span>▶️</span> YouTube</div>
    </div>
    <a href="https://ragchat-beta.vercel.app/" class="btn">Open RAGChat Web App →</a>
    <p style="font-size: 12px; color: #71717a; margin-top: 20px; margin-bottom: 0;">Redirecting to RAGChat Vercel Web App...</p>
  </div>
  <script>
    setTimeout(function() {
      window.location.href = "https://ragchat-beta.vercel.app/";
    }, 2500);
  </script>
</body>
</html>"""

class GoogleAuthManager:
    def __init__(self, config_dir=None):
        if not config_dir:
            self.config_dir = os.path.expanduser("~/.config/ragchat")
        else:
            self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        self.accounts_file = os.path.join(self.config_dir, "google_accounts.json")
        self.client_secrets_path = os.path.join(self.config_dir, "client_secrets.json")

    def _load_accounts(self):
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_accounts(self, accounts):
        with open(self.accounts_file, "w") as f:
            json.dump(accounts, f, indent=2)
        # Set file permission to owner read/write only for security
        os.chmod(self.accounts_file, 0o600)

    def list_profiles(self):
        return list(self._load_accounts().keys())

    def delete_profile(self, profile_name):
        accounts = self._load_accounts()
        if profile_name in accounts:
            del accounts[profile_name]
            self._save_accounts(accounts)
            return True
        return False

    def rename_profile(self, old_name, new_name):
        accounts = self._load_accounts()
        if old_name not in accounts:
            return False
        accounts[new_name] = accounts.pop(old_name)
        self._save_accounts(accounts)
        return True

    def get_credentials(self, profile_name):
        """
        Retrieves valid credentials for a profile.
        Automatically refreshes if expired.
        """
        accounts = self._load_accounts()
        if profile_name not in accounts:
            raise ValueError(f"Profile '{profile_name}' not found. Please run authentication first.")

        cred_data = accounts[profile_name]
        
        client_id = os.environ.get("GOOGLE_CLIENT_ID") or cred_data.get("client_id")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET") or cred_data.get("client_secret")

        if not client_id or not client_secret:
            raise Exception(
                "Google OAuth credentials not found.\n"
                "Run: ragchat bind google\n"
                "This binds your own Google OAuth Client JSON (1-time setup)."
            )
        
        creds = Credentials(
            token=cred_data.get("token"),
            refresh_token=cred_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                accounts[profile_name]["token"] = creds.token
                self._save_accounts(accounts)
            except Exception as e:
                raise Exception(f"Failed to refresh Google credentials for profile '{profile_name}': {e}")

        return creds

    def authenticate_profile(self, profile_name):
        """
        Runs the local OAuth loop to authorize a profile.
        Uses environment variables GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET,
        or falls back to reading client_secrets.json in ~/.config/ragchat/client_secrets.json.
        """
        # Enforce profile limit safeguard of 20 profiles
        accounts = self._load_accounts()
        if profile_name not in accounts and len(accounts) >= 20:
            raise Exception("Profile limit reached: RAGChat limits to 20 profiles per service.")

        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

        workspace_secret = None
        import glob
        project_secrets = glob.glob("client_secret_*.json")
        if project_secrets:
            workspace_secret = project_secrets[0]
        elif os.path.exists("client_secrets.json"):
            workspace_secret = "client_secrets.json"

        if os.path.exists(self.client_secrets_path):
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_path, SCOPES)
        elif workspace_secret and os.path.exists(workspace_secret):
            flow = InstalledAppFlow.from_client_secrets_file(workspace_secret, SCOPES)
        elif client_id and client_secret:
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        else:
            raise Exception(
                "\n[!] Google OAuth credentials not found.\n"
                "    You must first bind your own Google OAuth Client JSON:\n"
                "    Run: ragchat bind google\n"
                "    (This is a free 1-time setup using your own GCP project)"
            )

        creds = flow.run_local_server(port=0, success_message=OAUTH_SUCCESS_HTML)

        accounts = self._load_accounts()
        accounts[profile_name] = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        }
        self._save_accounts(accounts)
        return creds

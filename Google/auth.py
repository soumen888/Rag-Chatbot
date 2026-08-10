import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Scopes needed for Gmail, Calendar, Tasks, and Drive (Docs, Sheets, Slides)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",       # Read/Write/Delete Mail
    "https://www.googleapis.com/auth/calendar",           # Read/Write Calendar
    "https://www.googleapis.com/auth/tasks",              # Read/Write Tasks
    "https://www.googleapis.com/auth/drive"               # Full access to Drive/Docs
]

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

    def get_credentials(self, profile_name):
        """
        Retrieves valid credentials for a profile.
        Automatically refreshes if expired.
        """
        accounts = self._load_accounts()
        if profile_name not in accounts:
            raise ValueError(f"Profile '{profile_name}' not found. Please run authentication first.")

        cred_data = accounts[profile_name]
        
        # Check if environment keys are present or we have a client_secrets.json
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        creds = Credentials(
            token=cred_data.get("token"),
            refresh_token=cred_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id or cred_data.get("client_id"),
            client_secret=client_secret or cred_data.get("client_secret")
        )

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update saved token info
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
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

        if client_id and client_secret:
            # Construct client config dynamically
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        elif os.path.exists(self.client_secrets_path):
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_path, SCOPES)
        else:
            raise FileNotFoundError(
                f"Missing Google credentials. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                f"in your .env file, or place a valid client_secrets.json file in '{self.config_dir}'."
            )

        # Start temporary webserver for OAuth redirect
        creds = flow.run_local_server(port=0)

        # Save profile credentials
        accounts = self._load_accounts()
        accounts[profile_name] = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        }
        self._save_accounts(accounts)
        return creds

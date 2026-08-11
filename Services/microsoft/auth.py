import os
import json
import msal

# Microsoft Graph scopes for Outlook, OneDrive, Calendars, Tasks, User
SCOPES = [
    "User.Read",
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.ReadWrite",
    "Tasks.ReadWrite",
    "Files.ReadWrite.All"
]

class MicrosoftAuthManager:
    def __init__(self, config_dir=None):
        if not config_dir:
            self.config_dir = os.path.expanduser("~/.config/ragchat")
        else:
            self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        self.accounts_file = os.path.join(self.config_dir, "microsoft_accounts.json")
        # Standard default client ID for multi-tenant developer apps
        self.client_id = os.environ.get("MICROSOFT_CLIENT_ID", "0918f7e0-071e-499f-aec9-383822849070")
        self.authority = "https://login.microsoftonline.com/consumers"

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

    def get_token(self, profile_name):
        """
        Retrieves a valid access token for the profile.
        Silently refreshes if expired using MSAL's token cache.
        """
        accounts = self._load_accounts()
        if profile_name not in accounts:
            raise ValueError(f"Profile '{profile_name}' not found. Please authenticate first.")

        client_id = os.environ.get("MICROSOFT_CLIENT_ID", accounts[profile_name].get("client_id") or "0918f7e0-071e-499f-aec9-383822849070")

        # Create a serializable token cache
        cache = msal.SerializableTokenCache()
        token_cache_state = accounts[profile_name].get("token_cache")
        if token_cache_state:
            cache.deserialize(token_cache_state)

        # Re-build PublicClientApplication with the serializable cache
        app = msal.PublicClientApplication(client_id, authority=self.authority, token_cache=cache)

        # Get accounts from cache
        msal_accounts = app.get_accounts()
        if not msal_accounts:
            raise Exception("No active session found in MSAL cache. Please log in again.")

        # Attempt silent token acquisition
        result = app.acquire_token_silent(SCOPES, account=msal_accounts[0])
        
        if not result:
            raise Exception("Silent token acquisition failed. User interaction is required.")

        # If cache was updated, save it back
        if cache.has_state_changed:
            accounts[profile_name]["token_cache"] = cache.serialize()
            self._save_accounts(accounts)

        return result.get("access_token")

    def authenticate_profile(self, profile_name):
        """
        Runs an interactive OAuth flow (opening a browser to localhost redirect).
        If localhost flow fails, it falls back to the Device Code flow.
        """
        client_id = os.environ.get("MICROSOFT_CLIENT_ID", "0918f7e0-071e-499f-aec9-383822849070")

        cache = msal.SerializableTokenCache()
        app = msal.PublicClientApplication(client_id, authority=self.authority, token_cache=cache)
        result = None

        try:
            # 1. Try interactive browser authentication first (starts a local web server at localhost)
            result = app.acquire_token_interactive(scopes=SCOPES)
        except Exception as e:
            print(f"[!] Interactive login failed ({e}). Falling back to Device Code flow...")
            # 2. Device Code Flow fallback
            flow = app.initiate_device_flow(scopes=SCOPES)
            if "message" in flow:
                print("\n" + "="*60)
                print(flow["message"])
                print("="*60 + "\n")
            result = app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            accounts = self._load_accounts()
            accounts[profile_name] = {
                "client_id": client_id,
                "email": result.get("id_token_claims", {}).get("preferred_username"),
                "token_cache": cache.serialize()
            }
            self._save_accounts(accounts)
            print(f"[+] Microsoft profile '{profile_name}' successfully authenticated!")
            return result.get("access_token")
        else:
            error_desc = result.get("error_description", result.get("error"))
            raise Exception(f"Microsoft authentication failed: {error_desc}")

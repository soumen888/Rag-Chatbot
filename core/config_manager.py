import os
import json

class ConfigManager:
    # Default official Telegram Desktop API credentials
    DEFAULT_TG_API_ID = "2040"
    DEFAULT_TG_API_HASH = "b18441a1ff607e10a98a053d6a98562d"

    def __init__(self, cache_dir="./.crawl_cache"):
        self.cache_dir = cache_dir
        self.env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        self.tg_profiles_file = os.path.join(self.cache_dir, "tg_profiles.json")
        self.ds_profiles_file = os.path.join(self.cache_dir, "ds_profiles.json")
        os.makedirs(self.cache_dir, exist_ok=True)

    def write_env_var(self, key, value):
        """Programmatic .env writer that preserves existing content."""
        lines = []
        if os.path.exists(self.env_path):
            with open(self.env_path, 'r') as f:
                lines = f.readlines()
        
        found = False
        new_line = f"{key}={value}\n"
        
        for idx, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[idx] = new_line
                found = True
                break
                
        if not found:
            # Ensure line break at end
            if lines and not lines[-1].endswith('\n'):
                lines[-1] += '\n'
            lines.append(new_line)
            
        with open(self.env_path, 'w') as f:
            f.writelines(lines)
        
        # Keep os.environ in sync
        os.environ[key] = str(value)

    def save_google_client_secrets(self, json_data):
        """Saves Google OAuth client secrets data to ~/.config/ragchat/client_secrets.json."""
        config_dir = os.path.expanduser("~/.config/ragchat")
        os.makedirs(config_dir, exist_ok=True)
        secrets_path = os.path.join(config_dir, "client_secrets.json")
        with open(secrets_path, "w") as f:
            if isinstance(json_data, dict):
                json.dump(json_data, f, indent=2)
            else:
                f.write(str(json_data))
        os.chmod(secrets_path, 0o600)
        return secrets_path

    # ──────────────────────────────────────────────────────────────
    # Telegram Multi-Account Profiles
    # ──────────────────────────────────────────────────────────────

    def load_tg_profiles(self):
        profiles = {}
        if os.path.exists(self.tg_profiles_file):
            try:
                with open(self.tg_profiles_file, 'r') as f:
                    profiles = json.load(f)
            except Exception:
                pass
        
        # Auto-import legacy setup if it exists and no profiles are registered yet
        if not profiles:
            legacy_session = os.path.join(self.cache_dir, "personal_agent_session.session")
            if os.path.exists(legacy_session):
                profiles["default"] = {"session_name": "personal_agent_session"}
                self.save_tg_profiles(profiles)
                
        return profiles

    def save_tg_profiles(self, profiles):
        with open(self.tg_profiles_file, 'w') as f:
            json.dump(profiles, f, indent=2)

    def add_tg_profile(self, name, session_file):
        profiles = self.load_tg_profiles()
        profiles[name] = {"session_name": session_file}
        self.save_tg_profiles(profiles)

    def delete_tg_profile(self, name):
        profiles = self.load_tg_profiles()
        if name in profiles:
            del profiles[name]
            self.save_tg_profiles(profiles)
            return True
        return False

    # ──────────────────────────────────────────────────────────────
    # Discord Multi-Account Profiles
    # ──────────────────────────────────────────────────────────────

    def load_ds_profiles(self):
        if os.path.exists(self.ds_profiles_file):
            try:
                with open(self.ds_profiles_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_ds_profiles(self, profiles):
        with open(self.ds_profiles_file, 'w') as f:
            json.dump(profiles, f, indent=2)

    def add_ds_profile(self, name, token, is_bot=False):
        profiles = self.load_ds_profiles()
        profiles[name] = {
            "token": token,
            "is_bot": is_bot
        }
        self.save_ds_profiles(profiles)

    def delete_ds_profile(self, name):
        profiles = self.load_ds_profiles()
        if name in profiles:
            del profiles[name]
            self.save_ds_profiles(profiles)
            return True
        return False

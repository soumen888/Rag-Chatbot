import os
import sys

# Ensure local workspace modules are prioritized
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Secure OS Keychain is used by default; custom backends can still be set via PYTHON_KEYRING_BACKEND

try:
    from ragchat_core.core.config_manager import ConfigManager  # type: ignore
except ImportError:
    from core.config_manager import ConfigManager

# One-time migration of any existing .env file → keyring, then load all
# config keys from keyring into os.environ so downstream code is unaffected.
_cfg = ConfigManager()
_cfg._migrate_legacy_dotenv()
_cfg.load_all_to_env()

from main.menu import run_app

if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)

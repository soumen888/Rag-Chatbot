try:
    from ragchat_core.core.vector_db import VectorDB
    from ragchat_core.core.config_manager import ConfigManager
    from ragchat_core.core.chatbot import BaseLLMProvider, get_provider
    from ragchat_core.core.db import LocalDB
except (ImportError, AttributeError):
    from .vector_db import VectorDB
    from .config_manager import ConfigManager
    from .chatbot import BaseLLMProvider, get_provider
    from .db import LocalDB

# Exposing modular menus directly (these live in Public/core/menus/ - use relative imports)
from .menus.website import handle_website_menu
from .menus.telegram import handle_telegram_menu
from .menus.discord import handle_discord_menu
from .menus.chat import handle_chat_menu
from .menus.collections import handle_collections_menu
from .menus.settings import handle_settings_menu, interactive_setup_wizard, init_llm_provider_wrapper
from .menus.pageindex import handle_pageindex_menu


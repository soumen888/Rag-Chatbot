import os
from abc import ABC, abstractmethod

# ──────────────────────────────────────────────────────────────
# Base Provider
# ──────────────────────────────────────────────────────────────

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate_answer(self, question: str, context_chunks: list) -> str:
        """Generate an answer for the given question using the provided context."""
        raise NotImplementedError

    def _build_prompt(self, question: str, context_chunks: list) -> tuple[str, str]:
        """Shared prompt builder. Returns (system_instruction, user_prompt)."""
        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        context_str = ""
        for idx, chunk in enumerate(context_chunks):
            context_str += f"\n--- DOCUMENT CHUNK {idx+1} ---\n"
            context_str += f"Source: {chunk['metadata'].get('source', 'Unknown')}\n"
            context_str += f"Title: {chunk['metadata'].get('title', 'Unknown')}\n"
            context_str += f"Content:\n{chunk['text']}\n"

        system_instruction = (
            "You are a helpful, expert technical documentation and chat assistant.\n"
            f"The current real-world time is: {now_str}.\n"
            "Answer the user's question as accurately and comprehensively as possible based on the documentation/chat context provided below.\n"
            "You may logically reason and draw direct conclusions from the context, keeping the current real-world time in mind when resolving relative time references (e.g. today, yesterday, last 2 hours).\n"
            "If the answer cannot be determined or inferred from the context, state: "
            "'I could not find the answer to this question in the provided documentation.' and do not invent details.\n"
            "At the end of your answer, list all the unique Source URLs/links you referenced as 'Sources:'.\n"
        )

        user_prompt = (
            f"DOCUMENTATION CONTEXT:\n{context_str}\n\n"
            f"USER QUESTION: {question}\n\n"
            "YOUR DETAILED RESPONSE:"
        )

        return system_instruction, user_prompt


# ──────────────────────────────────────────────────────────────
# Universal LiteLLM Provider
# ──────────────────────────────────────────────────────────────

class LiteLLMProvider(BaseLLMProvider):
    """
    Universal LLM provider powered by LiteLLM.
    Supports Gemini, OpenAI, Anthropic (Claude), Groq, Together AI, Mistral, Ollama, LM Studio, etc.
    """

    def __init__(self, provider_type: str, api_key: str = "", model: str = "", base_url: str = None):
        import litellm
        import logging
        litellm.set_verbose = False
        logging.getLogger("LiteLLM").setLevel(logging.ERROR)
        self.litellm = litellm
        self.provider_type = provider_type
        self.api_key = api_key
        self.base_url = base_url

        # Format model name for LiteLLM schema
        if provider_type == "google":
            os.environ["GEMINI_API_KEY"] = api_key
            self.model_name = f"gemini/{model}" if not model.startswith("gemini/") else model
        elif provider_type == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
            self.model_name = f"anthropic/{model}" if not model.startswith("anthropic/") else model
        elif provider_type == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
            self.model_name = model
        elif provider_type == "groq":
            os.environ["GROQ_API_KEY"] = api_key
            self.model_name = f"groq/{model}" if not model.startswith("groq/") else model
        elif provider_type == "mistral":
            os.environ["MISTRAL_API_KEY"] = api_key
            self.model_name = f"mistral/{model}" if not model.startswith("mistral/") else model
        elif provider_type in ["ollama", "lmstudio"]:
            self.model_name = f"ollama/{model}" if not model.startswith("ollama/") else model
        else:
            self.model_name = model

    def generate_answer(self, question: str, context_chunks: list) -> str:
        system_instruction, user_prompt = self._build_prompt(question, context_chunks)
        try:
            kwargs = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 2048,
                "temperature": 0.3
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["api_base"] = self.base_url

            response = self.litellm.completion(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with LLM Provider ({self.provider_type}): {e}"


# ──────────────────────────────────────────────────────────────
# Provider Factory
# ──────────────────────────────────────────────────────────────

PROVIDER_INFO = {
    "google": {
        "name": "Google AI Studio (Gemini / Gemma)",
        "key_env": "LLM_API_KEY",
        "model_default": "gemini-1.5-flash",
        "url_required": False,
    },
    "openai": {
        "name": "OpenAI",
        "key_env": "LLM_API_KEY",
        "model_default": "gpt-4o-mini",
        "url_required": False,
    },
    "groq": {
        "name": "Groq (Cloud - Fast Inference)",
        "key_env": "LLM_API_KEY",
        "model_default": "llama-3.3-70b-versatile",
        "url_required": False,
    },
    "together": {
        "name": "Together AI",
        "key_env": "LLM_API_KEY",
        "model_default": "together_ai/meta-llama/Llama-3-8b-chat-hf",
        "url_required": False,
    },
    "mistral": {
        "name": "Mistral AI",
        "key_env": "LLM_API_KEY",
        "model_default": "mistral-small-latest",
        "url_required": False,
    },
    "ollama": {
        "name": "Ollama (Local)",
        "key_env": None,
        "model_default": "llama3",
        "url_required": False,
        "base_url": "http://localhost:11434",
    },
    "lmstudio": {
        "name": "LM Studio (Local)",
        "key_env": None,
        "model_default": "local-model",
        "url_required": False,
        "base_url": "http://localhost:1234/v1",
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "key_env": "LLM_API_KEY",
        "model_default": "claude-3-5-sonnet-20241022",
        "url_required": False,
    },
    "custom": {
        "name": "Custom OpenAI-Compatible Endpoint",
        "key_env": "LLM_API_KEY",
        "model_default": "your-model-name",
        "url_required": True,
    },
}


def get_provider() -> BaseLLMProvider:
    """
    Factory function. Reads LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
    from environment variables and returns the LiteLLMProvider instance.
    """
    provider_name = os.environ.get("LLM_PROVIDER", "google").lower().strip()
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")
    base_url = os.environ.get("LLM_BASE_URL", "").strip() or None

    info = PROVIDER_INFO.get(provider_name)
    if not info:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider_name}'. "
            f"Valid options: {', '.join(PROVIDER_INFO.keys())}"
        )

    if not model:
        model = info["model_default"]

    if not base_url:
        base_url = info.get("base_url")

    if info["key_env"] and not api_key and provider_name not in ["ollama", "lmstudio"]:
        raise ValueError(f"LLM_API_KEY is required for the '{provider_name}' provider.")

    return LiteLLMProvider(
        provider_type=provider_name,
        api_key=api_key,
        model=model,
        base_url=base_url
    )


# ──────────────────────────────────────────────────────────────
# Legacy compatibility shim
# ──────────────────────────────────────────────────────────────

class RAGChatbot:
    """Compatibility wrapper. Use get_provider() directly in new code."""

    def __init__(self, api_key=None, model_name=None):
        self._provider = None
        self._api_key = api_key
        self._model = model_name

    def configure_api(self, api_key):
        self._api_key = api_key
        self._init_provider()

    def _init_provider(self):
        if self._api_key:
            os.environ.setdefault("LLM_API_KEY", self._api_key)
        if self._model:
            os.environ.setdefault("LLM_MODEL", self._model)
        self._provider = get_provider()

    def is_configured(self) -> bool:
        return self._provider is not None

    def generate_answer(self, question: str, context_chunks: list) -> str:
        if not self.is_configured():
            raise ValueError("LLM provider is not configured.")
        return self._provider.generate_answer(question, context_chunks)

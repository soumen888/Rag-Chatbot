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
# Google AI Studio / Vertex AI Provider
# ──────────────────────────────────────────────────────────────

class GoogleProvider(BaseLLMProvider):
    """Provider for Google AI Studio and Vertex AI using the google-genai SDK."""

    def __init__(self, api_key: str, model: str = "gemma-4-31b-it"):
        from google import genai
        from google.genai import types as genai_types
        self._genai = genai
        self._types = genai_types
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def generate_answer(self, question: str, context_chunks: list) -> str:
        system_instruction, user_prompt = self._build_prompt(question, context_chunks)
        full_prompt = f"{system_instruction}\n\n{user_prompt}"
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=self._types.GenerateContentConfig(
                    max_output_tokens=2048,
                    temperature=0.3
                )
            )
            return response.text
        except Exception as e:
            return f"Error communicating with Google GenAI API: {e}"


# ──────────────────────────────────────────────────────────────
# OpenAI-Compatible Provider
# Covers: OpenAI, Groq, Together AI, Mistral, LM Studio, Perplexity, etc.
# ──────────────────────────────────────────────────────────────

class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Universal provider for any OpenAI-compatible API.
    Works with: OpenAI, Groq, Together AI, Mistral, Perplexity,
    LM Studio, and any service exposing a /v1/chat/completions endpoint.
    """

    def __init__(self, api_key: str, model: str, base_url: str = None):
        from openai import OpenAI
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model

    def generate_answer(self, question: str, context_chunks: list) -> str:
        system_instruction, user_prompt = self._build_prompt(question, context_chunks)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2048,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with OpenAI-compatible API: {e}"


# ──────────────────────────────────────────────────────────────
# Ollama Local Provider
# ──────────────────────────────────────────────────────────────

class OllamaProvider(OpenAICompatibleProvider):
    """
    Provider for local Ollama models.
    Ollama exposes an OpenAI-compatible API at http://localhost:11434/v1
    Run models locally: ollama pull llama3, ollama pull mistral, etc.
    """

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434/v1"):
        super().__init__(api_key="ollama", model=model, base_url=base_url)


# ──────────────────────────────────────────────────────────────
# Anthropic Provider (Claude)
# ──────────────────────────────────────────────────────────────

class AnthropicProvider(BaseLLMProvider):
    """Provider for Anthropic Claude models."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_answer(self, question: str, context_chunks: list) -> str:
        system_instruction, user_prompt = self._build_prompt(question, context_chunks)
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_instruction,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error communicating with Anthropic API: {e}"


# ──────────────────────────────────────────────────────────────
# Provider Factory
# ──────────────────────────────────────────────────────────────

PROVIDER_INFO = {
    "google": {
        "name": "Google AI Studio (Gemini / Gemma)",
        "key_env": "LLM_API_KEY",
        "model_default": "gemma-4-31b-it",
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
        "base_url": "https://api.groq.com/openai/v1",
    },
    "together": {
        "name": "Together AI",
        "key_env": "LLM_API_KEY",
        "model_default": "meta-llama/Llama-3-8b-chat-hf",
        "url_required": False,
        "base_url": "https://api.together.xyz/v1",
    },
    "mistral": {
        "name": "Mistral AI",
        "key_env": "LLM_API_KEY",
        "model_default": "mistral-small-latest",
        "url_required": False,
        "base_url": "https://api.mistral.ai/v1",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "key_env": None,
        "model_default": "llama3",
        "url_required": False,
        "base_url": "http://localhost:11434/v1",
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
    from environment variables and returns the correct provider instance.
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

    # Use default model if none specified
    if not model:
        model = info["model_default"]

    # Resolve base URL (env overrides hardcoded default)
    if not base_url:
        base_url = info.get("base_url")

    if provider_name == "google":
        if not api_key:
            raise ValueError("LLM_API_KEY is required for the Google provider.")
        return GoogleProvider(api_key=api_key, model=model)

    elif provider_name == "anthropic":
        if not api_key:
            raise ValueError("LLM_API_KEY is required for the Anthropic provider.")
        return AnthropicProvider(api_key=api_key, model=model)

    elif provider_name == "ollama":
        return OllamaProvider(model=model, base_url=base_url)

    elif provider_name == "lmstudio":
        return OllamaProvider(model=model, base_url=base_url)

    else:
        # openai, groq, together, mistral, custom
        if not api_key and provider_name not in ["ollama", "lmstudio"]:
            raise ValueError(f"LLM_API_KEY is required for the '{provider_name}' provider.")
        return OpenAICompatibleProvider(api_key=api_key, model=model, base_url=base_url)


# ──────────────────────────────────────────────────────────────
# Legacy compatibility shim
# ──────────────────────────────────────────────────────────────

class DocChatbot:
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

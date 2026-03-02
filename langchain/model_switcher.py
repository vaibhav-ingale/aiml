"""
Simple Model Configuration for LangChain
Configure your OpenAI-compatible endpoint or Ollama.
"""

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# ============================================================
# MODEL CONFIGURATION - Edit these settings
# ============================================================

# Provider: "openai" or "ollama"
PROVIDER = "openai"
# PROVIDER = "ollama"

# OpenAI-compatible settings (for PROVIDER = "openai") as we are using ChatOpenAI class
# OPENAI_MODEL = "gpt-oss:20b"
# OPENAI_MODEL = "openai/gpt-oss-20b"
OPENAI_MODEL = "ggml-org/gpt-oss-20b-GGUF"
# OPENAI_MODEL = "granite4:latest"
# OPENAI_MODEL = "ministral-3:8b-instruct-2512-q4_K_M"
# OPENAI_MODEL = "mistralai/ministral-3-3b"
OPENAI_BASE_URL = "http://10.0.0.100:8008/v1"
OPENAI_API_KEY = "llmgw-JiCFEeqoGLkuyzF1GAKHgPY4vSadsbMR"

# Ollama settings (for PROVIDER = "ollama") as we are using ChatOllama class
OLLAMA_MODEL = "gpt-oss:20b"
OLLAMA_BASE_URL = "http://10.0.0.100:11434"
OLLAMA_API_KEY = "not-needed"

# Common settings
TEMPERATURE = 0.1
MAX_TOKENS = 5000

# ============================================================
# MODEL GETTER FUNCTIONS
# ============================================================
import uuid

SESSION_ID = f"agent-{str(uuid.uuid4())[-8:]}"


def get_model(provider=None, model_name=None, base_url=None, api_key=None, temperature=None, max_tokens=None, session_id=None, **kwargs):
    """
    Get configured chat model based on provider.

    Args:
        provider: Override default PROVIDER ("openai" or "ollama")
        model_name: Override default model name
        base_url: Override default base URL
        api_key: Override default API key (OpenAI only)
        temperature: Override default TEMPERATURE
        max_tokens: Override default MAX_TOKENS
        session_id: Session ID for tracking related requests (OpenAI provider only)
        **kwargs: Additional parameters for the model

    Returns:
        ChatOpenAI or ChatOllama instance
    """
    selected_provider = provider or PROVIDER

    if selected_provider == "openai":
        # Add session_id to default_headers if provided
        default_headers = kwargs.pop("default_headers", {})
        if session_id or SESSION_ID:
            default_headers["X-Session-ID"] = session_id or SESSION_ID

        return ChatOpenAI(
            model=model_name or OPENAI_MODEL,
            base_url=base_url or OPENAI_BASE_URL,
            api_key=api_key or OPENAI_API_KEY,
            temperature=temperature if temperature is not None else TEMPERATURE,
            max_tokens=max_tokens or MAX_TOKENS,
            default_headers=default_headers if default_headers else None,
            **kwargs,
        )
    elif selected_provider == "ollama":
        # Note: Ollama provider doesn't support custom headers for session tracking
        # Use OpenAI provider with Ollama-compatible gateway for session support
        return ChatOllama(
            model=model_name or OLLAMA_MODEL,
            base_url=base_url or OLLAMA_BASE_URL,
            # api_key=api_key or OLLAMA_API_KEY,
            temperature=temperature if temperature is not None else TEMPERATURE,
            num_predict=max_tokens or MAX_TOKENS,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown provider: {selected_provider}. Use 'openai' or 'ollama'")


if __name__ == "__main__":
    # Demo usage - test the model configuration
    print(f"Provider: {PROVIDER}")
    if PROVIDER == "openai":
        print(f"Model: {OPENAI_MODEL}")
        print(f"Base URL: {OPENAI_BASE_URL}")
    else:
        print(f"Model: {OLLAMA_MODEL}")
        print(f"Base URL: {OLLAMA_BASE_URL}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Max Tokens: {MAX_TOKENS}")
    print("-" * 50)

    # Get the configured model
    model = get_model()
    print(f"Model loaded: {model}")

    # Test with a simple question
    response = model.invoke("What is 2+2?")
    print(f"\nTest Question: What is 2+2?")
    print(f"Response: {response.content}")

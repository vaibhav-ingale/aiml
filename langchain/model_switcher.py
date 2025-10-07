"""
Universal Model Switcher for LangChain
Supports switching between different LLM providers with a single function call.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import ollama
from dotenv import load_dotenv

load_dotenv()
# Import different LangChain model classes

# pip install -qU "langchain[ollama]"
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    OllamaLLM = None

# pip install -qU "langchain[openai]"
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

# pip install -qU "langchain[anthropic]"
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

# pip install -qU "langchain[mistralai]"
try:
    from langchain_mistralai import ChatMistralAI
except ImportError:
    ChatMistralAI = None

# pip install -qU "langchain[huggingface]"
try:
    from langchain_huggingface import HuggingFaceEndpoint
except ImportError:
    HuggingFaceEndpoint = None

# pip install -qU "langchain[google-genai]"
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None


class ModelSwitcher:
    """Universal model switcher for LangChain supporting multiple providers."""

    def __init__(self):
        self.supported_providers = {
            "ollama": self._get_ollama_model,
            "openai": self._get_openai_model,
            "llamacpp": self._get_llamacpp_model,
            "anthropic": self._get_anthropic_model,
            "mistral": self._get_mistral_model,
            "huggingface": self._get_huggingface_model,
            "google": self._get_google_model,
        }

    def get_model(self, provider: str, model_name: str, **kwargs) -> Union[Any, None]:
        """
        Get a model from the specified provider.

        Args:
            provider: Provider name ('ollama', 'openai', 'llamacpp', 'anthropic', 'mistral', 'huggingface', 'google')
            model_name: Model name/ID
            **kwargs: Additional parameters for the model

        Returns:
            Initialized model instance or None if failed
        """
        if provider.lower() not in self.supported_providers:
            raise ValueError(f"Unsupported provider: {provider}. Supported: {list(self.supported_providers.keys())}")

        return self.supported_providers[provider.lower()](model_name, **kwargs)

    def _get_ollama_model(self, model_name: str, **kwargs) -> Optional[OllamaLLM]:
        """Get Ollama model."""
        if OllamaLLM is None:
            print("langchain_ollama not installed. Install: pip install langchain-ollama")
            return None

        defaults = {"temperature": 0.1, "max_tokens": 100}
        defaults.update(kwargs)

        return OllamaLLM(model=model_name, **defaults)

    def _get_openai_model(self, model_name: str, **kwargs) -> Optional[ChatOpenAI]:
        """Get OpenAI model."""
        if ChatOpenAI is None:
            print("langchain_openai not installed. Install: pip install langchain-openai")
            return None

        if not os.getenv("OPENAI_API_KEY"):
            print("OPENAI_API_KEY environment variable not set")
            return None

        defaults = {"temperature": 0.1, "max_tokens": 100}
        defaults.update(kwargs)

        return ChatOpenAI(model=model_name, **defaults)

    def _get_llamacpp_model(self, model_name: str, **kwargs) -> Optional[ChatOpenAI]:
        """Get llama.cpp model using OpenAI-compatible endpoint."""
        if ChatOpenAI is None:
            print("langchain_openai not installed. Install: pip install langchain-openai")
            return None

        # Extract base_url from kwargs, default to llama.cpp default
        base_url = kwargs.pop("base_url", "http://localhost:8080/v1")

        defaults = {
            "temperature": 0.1,
            "max_tokens": 100,
            "openai_api_key": "not-needed",
            "openai_api_base": base_url,
        }
        defaults.update(kwargs)

        return ChatOpenAI(model=model_name, **defaults)

    def _get_anthropic_model(self, model_name: str, **kwargs) -> Optional[ChatAnthropic]:
        """Get Anthropic model."""
        if ChatAnthropic is None:
            print("langchain_anthropic not installed. Install: pip install langchain-anthropic")
            return None

        if not os.getenv("ANTHROPIC_API_KEY"):
            print("ANTHROPIC_API_KEY environment variable not set")
            return None

        defaults = {"temperature": 0.1, "max_tokens": 100}
        defaults.update(kwargs)

        return ChatAnthropic(model=model_name, **defaults)

    def _get_mistral_model(self, model_name: str, **kwargs) -> Optional[ChatMistralAI]:
        """Get Mistral model."""
        if ChatMistralAI is None:
            print("langchain_mistralai not installed. Install: pip install langchain-mistralai")
            return None

        if not os.getenv("MISTRAL_API_KEY"):
            print("MISTRAL_API_KEY environment variable not set")
            return None

        defaults = {"temperature": 0.1, "max_tokens": 100}
        defaults.update(kwargs)

        return ChatMistralAI(model=model_name, **defaults)

    def _get_huggingface_model(self, model_name: str, **kwargs) -> Optional[HuggingFaceEndpoint]:
        """Get HuggingFace model."""
        if HuggingFaceEndpoint is None:
            print("langchain_huggingface not installed. Install: pip install langchain-huggingface")
            return None

        if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
            print("HUGGINGFACEHUB_API_TOKEN environment variable not set")
            return None

        defaults = {"temperature": 0.1, "max_new_tokens": 100}
        defaults.update(kwargs)

        return HuggingFaceEndpoint(repo_id=model_name, **defaults)

    def _get_google_model(self, model_name: str, **kwargs) -> Optional[ChatGoogleGenerativeAI]:
        """Get Google Generative AI model."""
        if ChatGoogleGenerativeAI is None:
            print("langchain_google_genai not installed. Install: pip install langchain-google-genai")
            return None

        if not os.getenv("GOOGLE_API_KEY"):
            print("GOOGLE_API_KEY environment variable not set")
            return None

        defaults = {"temperature": 0.1, "max_output_tokens": 100}
        defaults.update(kwargs)

        return ChatGoogleGenerativeAI(model=model_name, **defaults)

    def list_available_providers(self) -> list:
        """List all supported providers."""
        return list(self.supported_providers.keys())

    def list_ollama_models(self) -> list:
        """List available Ollama models."""
        try:
            models = ollama.list()["models"]
            return [model.model for model in models]
        except Exception as e:
            print(f"Error listing Ollama models: {e}")
            return []


# Convenience function for quick model switching
def get_model(provider: str, model_name: str, **kwargs) -> Union[Any, None]:
    """
    Quick function to get any model with one line.

    Examples:
        # Ollama
        model = get_model('ollama', 'llama2')

        # OpenAI
        model = get_model('openai', 'gpt-3.5-turbo')

        # llama.cpp
        model = get_model('llamacpp', 'local-model', base_url='http://localhost:8080/v1')

        # Anthropic
        model = get_model('anthropic', 'claude-3-sonnet-20240229')

        # Mistral
        model = get_model('mistral', 'mistral-large-latest')

        # HuggingFace
        model = get_model('huggingface', 'microsoft/DialoGPT-medium')

        # Google
        model = get_model('google', 'gemini-pro')
    """
    switcher = ModelSwitcher()
    return switcher.get_model(provider, model_name, **kwargs)


# Popular model presets
POPULAR_MODELS = {
    "ollama": [
        "llama2",
        "llama2:7b",
        "llama2:13b",
        "mistral",
        "codellama",
        "vicuna",
        "orca-mini",
    ],
    "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
    "anthropic": [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    "mistral": [
        "mistral-large-latest",
        "mistral-medium-latest",
        "mistral-small-latest",
    ],
    "google": ["gemini-pro", "gemini-pro-vision"],
    "huggingface": [
        "microsoft/DialoGPT-medium",
        "huggingface/CodeBERTa-small-v1",
        "facebook/blenderbot-400M-distill",
    ],
}


if __name__ == "__main__":
    # Demo usage
    switcher = ModelSwitcher()

    print("Supported providers:", switcher.list_available_providers())
    print("\nAvailable Ollama models:", switcher.list_ollama_models())

    # Example usage
    print("\nExample usage:")
    print("model = get_model('ollama', 'llama2')")
    print("model = get_model('openai', 'gpt-3.5-turbo')")
    print("model = get_model('llamacpp', 'local-model', base_url='http://localhost:8080/v1')")
    print("model = get_model('anthropic', 'claude-3-sonnet-20240229')")

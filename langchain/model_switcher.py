"""
Model Switcher for LangChain
Supports switching between Ollama and llama.cpp models.
"""

from typing import Any, Optional, Union

# Import ollama module
try:
    import ollama
except ImportError:
    ollama = None

# Import LangChain model classes

# pip install -qU "langchain[ollama]"
try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None

# pip install -qU "langchain[openai]"
# Note: Used for llama.cpp OpenAI-compatible endpoint
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None


class ModelSwitcher:
    """Model switcher for LangChain supporting Ollama and llama.cpp."""

    def __init__(self):
        self.supported_providers = {
            "ollama": self._get_ollama_model,
            "llamacpp": self._get_llamacpp_model,
        }

    def get_model(self, provider: str, model_name: str, **kwargs) -> Union[Any, None]:
        """
        Get a model from the specified provider.

        Args:
            provider: Provider name ('ollama', 'llamacpp')
            model_name: Model name/ID
            **kwargs: Additional parameters for the model

        Returns:
            Initialized model instance or None if failed
        """
        if provider.lower() not in self.supported_providers:
            raise ValueError(f"Unsupported provider: {provider}. Supported: {list(self.supported_providers.keys())}")

        return self.supported_providers[provider.lower()](model_name, **kwargs)

    def _get_ollama_model(self, model_name: str, **kwargs) -> Optional[ChatOllama]:
        """Get Ollama chat model."""
        if ChatOllama is None:
            print("langchain_ollama not installed. Install: pip install langchain-ollama")
            return None

        defaults = {"temperature": 0.1}
        defaults.update(kwargs)

        return ChatOllama(model=model_name, **defaults)

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

    def list_available_providers(self) -> list:
        """List all supported providers."""
        return list(self.supported_providers.keys())

    def list_ollama_models(self) -> list:
        """List available Ollama models."""
        if ollama is None:
            print("ollama module not installed. Install: pip install ollama")
            return []
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

        # llama.cpp
        model = get_model('llamacpp', 'local-model', base_url='http://localhost:8080/v1')
    """
    switcher = ModelSwitcher()
    return switcher.get_model(provider, model_name, **kwargs)


# Default configuration (can be customized by users)
PROVIDER = "ollama"
MODEL_NAME = "gpt-oss:20b"
MODEL_PARAMS = {"temperature": 0}


def get_configured_model(**kwargs) -> Union[Any, None]:
    """
    Get the model using the default configuration.

    Args:
        **kwargs: Additional parameters to override defaults

    Returns:
        Initialized model instance using PROVIDER, MODEL_NAME, and MODEL_PARAMS

    Examples:
        # Use default configuration
        model = get_configured_model()

        # Override specific parameters
        model = get_configured_model(temperature=0.7)

        # For llama.cpp, you might need to specify base_url
        model = get_configured_model(base_url='http://localhost:8080/v1')
    """
    params = MODEL_PARAMS.copy()
    params.update(kwargs)
    return get_model(PROVIDER, MODEL_NAME, **params)


if __name__ == "__main__":
    from mlutils import print_model_info, print_response

    # Demo usage
    switcher = ModelSwitcher()

    print("Supported providers:", switcher.list_available_providers())
    print("\nAvailable Ollama models:", switcher.list_ollama_models())
    model = get_configured_model()
    print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

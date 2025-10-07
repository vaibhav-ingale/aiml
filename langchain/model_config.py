"""
Global Model Configuration
Centralized configuration for model selection across all tests and examples.
Change the model settings here, and all code using this config will automatically use the new model.
"""

# PRESET MODEL CONFIGURATIONS
MODEL_CONFIGS = {
    "ollama_gpt_oss": {
        "provider": "ollama",
        "model_name": "gpt-oss:20b",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {},
    },
    "ollama_llama32": {
        "provider": "ollama",
        "model_name": "llama3.2:1b",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {},
    },
    "llamacpp_local": {
        "provider": "llamacpp",
        # "model_name": "gpt-oss:20b",
        "model_name": "mistralai/Magistral-Small-2509-GGUF",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {"base_url": "http://localhost:8080/v1"},
    },
    "openai_gpt4": {
        "provider": "openai",
        "model_name": "gpt-4",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {},
    },
    "openai_gpt35": {
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {},
    },
    "anthropic_claude_sonnet": {
        "provider": "anthropic",
        "model_name": "claude-3-sonnet-20240229",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {},
    },
    "anthropic_claude_opus": {
        "provider": "anthropic",
        "model_name": "claude-3-opus-20240229",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {},
    },
    "mistral_small": {
        "provider": "mistral",
        "model_name": "mistral-small-latest",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {},
    },
    "mistral_large": {
        "provider": "mistral",
        "model_name": "mistral-large-latest",
        "params": {"temperature": 0.1, "max_tokens": 100},
        "additional_params": {},
    },
    "google_gemini_pro": {
        "provider": "google",
        "model_name": "gemini-pro",
        "params": {"temperature": 0.1, "max_output_tokens": 100},
        "additional_params": {},
    },
    "google_gemini_flash": {
        "provider": "google",
        "model_name": "gemini-2.5-flash-lite",
        "params": {"temperature": 0.1, "max_output_tokens": 100},
        "additional_params": {},
    },
}


# ACTIVE CONFIGURATION
# ACTIVE_CONFIG = "ollama_gpt_oss"
ACTIVE_CONFIG = "llamacpp_local"

# Load the active configuration
_config = MODEL_CONFIGS[ACTIVE_CONFIG]
PROVIDER = _config["provider"]
MODEL_NAME = _config["model_name"]
MODEL_PARAMS = _config["params"]
ADDITIONAL_PARAMS = _config["additional_params"]


# HELPER FUNCTION
def get_configured_model():
    """
    Get the globally configured model.

    Returns:
        Initialized model instance based on global configuration
    """
    from model_switcher import get_model

    # Merge model parameters with additional parameters
    all_params = {**MODEL_PARAMS, **ADDITIONAL_PARAMS}

    return get_model(PROVIDER, MODEL_NAME, **all_params)


def list_available_configs():
    """List all available model configurations."""
    print("\nAvailable Model Configurations:")
    print("=" * 60)
    for key, config in MODEL_CONFIGS.items():
        active = "→ ACTIVE" if key == ACTIVE_CONFIG else ""
        print(f"{key:25} {config['provider']:12} {config['model_name']:30} {active}")
    print("=" * 60)


if __name__ == "__main__":
    # Display current configuration
    print("=" * 60)
    print("CURRENT MODEL CONFIGURATION")
    print("=" * 60)
    print(f"Active Config: {ACTIVE_CONFIG}")
    print(f"Provider: {PROVIDER}")
    print(f"Model: {MODEL_NAME}")
    print(f"Parameters: {MODEL_PARAMS}")
    print(f"Additional Parameters: {ADDITIONAL_PARAMS}")
    print("=" * 60)

    # List all available configurations
    list_available_configs()

    # Test the configuration
    print("\nTesting model initialization...")
    model = get_configured_model()
    if model:
        print(f"✓ Model initialized successfully: {type(model).__name__}")
    else:
        print("✗ Failed to initialize model")

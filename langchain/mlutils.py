"""
Utility functions for LangChain examples.
"""

from typing import Any


def print_response(response: Any, use_markdown: bool = True):
    """
    Print model response with optional markdown formatting.

    Args:
        response: Model response object or string
        use_markdown: Whether to use rich markdown formatting (default: True)
    """
    # Extract content from response object or use as string
    if hasattr(response, "content"):
        content = response.content
    else:
        content = str(response)

    # Print with markdown formatting if available
    if use_markdown:
        try:
            from rich.console import Console
            from rich.markdown import Markdown

            console = Console()
            markdown = Markdown(content)
            console.print(markdown)
        except ImportError:
            # Fallback to plain text if rich is not installed
            print(content)
    else:
        print(content)


def print_model_info(model: Any):
    """
    Print model configuration information.

    Args:
        model: Model object (ChatOpenAI, ChatOllama, etc.)
    """
    print("=" * 60)
    print("MODEL CONFIGURATION")
    print("=" * 60)

    # Extract model information based on type
    model_type = type(model).__name__
    print(f"Model API Type: {model_type}")

    # Try to get common attributes
    if hasattr(model, "model_name"):
        print(f"Model Name: {model.model_name}")
    elif hasattr(model, "model"):
        print(f"Model Name: {model.model}")

    if hasattr(model, "base_url"):
        print(f"Base URL: {model.base_url}")
    elif hasattr(model, "openai_api_base"):
        print(f"Base URL: {model.openai_api_base}")

    if hasattr(model, "temperature"):
        print(f"Temperature: {model.temperature}")

    if hasattr(model, "max_tokens"):
        print(f"Max Tokens: {model.max_tokens}")

    print("=" * 60)

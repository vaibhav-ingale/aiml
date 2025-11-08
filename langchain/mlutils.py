"""
Utility functions for LangChain examples.
"""

import re
from typing import Any


def print_response(response: Any, provider: str = None, use_markdown: bool = True, convert_latex: bool = True):
    """
    Print model response with optional markdown formatting and LaTeX conversion.

    Args:
        response: Model response object
        provider: Optional provider name to determine response format
        use_markdown: Whether to use rich markdown formatting (default: True)
        convert_latex: Whether to convert LaTeX to Unicode (default: True)
    """
    # Determine if response has content attribute (ChatModels) or is a string
    if hasattr(response, "content"):
        content = response.content
    else:
        content = str(response)

    # Apply markdown formatting if requested
    if use_markdown:
        try:
            from rich.console import Console
            from rich.markdown import Markdown

            console = Console()
            markdown = Markdown(content)
            console.print(markdown)
        except ImportError:
            # If rich is not installed, just print plain text
            print(content)
    else:
        print(content)


def print_model_info(provider: str, model_name: str, params: dict = None):
    """
    Print model configuration information.

    Args:
        provider: Provider name
        model_name: Model name
        params: Optional model parameters
    """
    print("=" * 60)
    print("MODEL CONFIGURATION")
    print("=" * 60)
    print(f"Provider: {provider}")
    print(f"Model: {model_name}")
    if params:
        print(f"Parameters: {params}")
    print("=" * 60)

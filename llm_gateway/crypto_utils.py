"""
Encryption utilities for securing sensitive data like API keys.
Uses Fernet (symmetric encryption) from cryptography library.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Get encryption key from environment or generate one
ENCRYPTION_KEY_ENV = os.getenv("LLM_GATEWAY_ENCRYPTION_KEY")

def get_encryption_key() -> bytes:
    """
    Get or generate encryption key.
    In production, this should be stored securely (e.g., environment variable, secrets manager).
    """
    if ENCRYPTION_KEY_ENV:
        return ENCRYPTION_KEY_ENV.encode()

    # For development, use a deterministic key based on a salt
    # In production, you should use a proper secret management system
    salt = b'llm_gateway_salt_v1'  # This should be unique and stored securely
    password = os.getenv("LLM_GATEWAY_SECRET", "default_dev_secret_change_in_prod")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for storage.

    Args:
        api_key: Plain text API key

    Returns:
        Encrypted API key as base64 string
    """
    if not api_key:
        return ""

    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(api_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    Decrypt an API key from storage.

    Handles both encrypted and plain text API keys for backwards compatibility.
    If the key starts with 'llmgw-', it's assumed to be plain text and returned as-is.

    Args:
        encrypted_api_key: Encrypted API key as base64 string or plain text

    Returns:
        Plain text API key
    """
    if not encrypted_api_key:
        return ""

    # Check if it's a plain text API key (starts with 'llmgw-')
    if encrypted_api_key.startswith('llmgw-'):
        return encrypted_api_key

    # Otherwise, try to decrypt it
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_api_key.encode())
        return decrypted.decode()
    except Exception as e:
        # If decryption fails, log the error and return the key as-is
        # This handles cases where the key might be stored in plain text
        print(f"Warning: Failed to decrypt API key, returning as plain text: {e}")
        return encrypted_api_key


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """
    Mask an API key for display purposes.

    Args:
        api_key: Plain text API key
        visible_chars: Number of characters to show at the end

    Returns:
        Masked API key (e.g., "****xyz123")
    """
    if not api_key or len(api_key) <= visible_chars:
        return "****"

    return "*" * 8 + api_key[-visible_chars:]

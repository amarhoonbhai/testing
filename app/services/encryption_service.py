"""
Fernet encryption service for Telethon session strings.

Uses a symmetric key stored in ENCRYPTION_KEY environment variable.
Never logs or exposes raw session data.
"""

import logging
from cryptography.fernet import Fernet, InvalidToken

from app.config import ENCRYPTION_KEY

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Get or create the Fernet cipher instance."""
    global _fernet
    if _fernet is None:
        if not ENCRYPTION_KEY:
            raise RuntimeError("ENCRYPTION_KEY not set in environment")
        _fernet = Fernet(ENCRYPTION_KEY.encode())
    return _fernet


def encrypt_session(session_string: str) -> str:
    """
    Encrypt a Telethon session string.

    Returns the encrypted data as a UTF-8 string (base64-encoded).
    """
    try:
        f = _get_fernet()
        encrypted = f.encrypt(session_string.encode("utf-8"))
        return encrypted.decode("utf-8")
    except Exception:
        logger.error("Failed to encrypt session data")
        raise


def decrypt_session(encrypted_data: str) -> str:
    """
    Decrypt an encrypted Telethon session string.

    Returns the original session string.
    """
    try:
        f = _get_fernet()
        decrypted = f.decrypt(encrypted_data.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt session — invalid token or key mismatch")
        raise
    except Exception:
        logger.error("Failed to decrypt session data")
        raise


def generate_new_key() -> str:
    """Generate a new Fernet key. Use this to create ENCRYPTION_KEY."""
    return Fernet.generate_key().decode("utf-8")

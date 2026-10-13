"""Hill cipher stub.

Weaknesses: linear structure makes it vulnerable to known-plaintext attacks, and the key matrix must be invertible mod 26.
Owner: <name>
"""

from __future__ import annotations


def encrypt(text: str, key) -> str:
    """Encrypt text using the Hill cipher.

    This function is intentionally not implemented yet.
    """

    raise NotImplementedError("Hill encryption is not implemented yet.")


def decrypt(text: str, key) -> str:
    """Decrypt text using the Hill cipher.

    This function is intentionally not implemented yet.
    """

    raise NotImplementedError("Hill decryption is not implemented yet.")


def validate_key(key) -> bool:
    """Validate a Hill cipher key.

    This function is intentionally not implemented yet.
    """

    raise NotImplementedError("Hill key validation is not implemented yet.")
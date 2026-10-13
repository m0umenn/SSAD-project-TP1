"""Password protection stub.

This module will later hold password storage, hashing, and protection helpers.
Owner: <name>
"""

from __future__ import annotations


def hash_password(password: str) -> str:
    """Hash a password for storage.

    This function is intentionally not implemented yet.
    """

    raise NotImplementedError("Password hashing is not implemented yet.")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its stored representation.

    This function is intentionally not implemented yet.
    """

    raise NotImplementedError("Password verification is not implemented yet.")
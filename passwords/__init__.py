"""Password protection, candidate generation, and validation for SSAD Toolkit."""

from __future__ import annotations

from passwords.protection import (
    LOCK_SECONDS,
    MAX_FAILURES,
    Lockout,
    make_checker,
    protect,
    validate_password,
)

__all__ = [
    "LOCK_SECONDS",
    "MAX_FAILURES",
    "Lockout",
    "make_checker",
    "protect",
    "validate_password",
]
"""Password validation, PBKDF2-HMAC-SHA256 storage, verification, and lockout."""

from __future__ import annotations

import hashlib
import hmac
import math
import os
import time
from collections.abc import Callable
from typing import Any

from passwords.generators import USE_CASES, hash_fast

ITERATIONS = 100_000
SALT_BYTES = 16
MAX_FAILURES = 5
LOCK_SECONDS = 30


def validate_password(password: str, use_case: int) -> None:
    """Validate `password` against the alphabet and length rules of `use_case`.

    Raises:
        ValueError: If the use case is unknown, the password is empty, the
            length does not match, or any character is outside the alphabet.
    """
    if isinstance(use_case, bool) or use_case not in USE_CASES:
        raise ValueError("Unknown use case.")
    if not isinstance(password, str) or password == "":
        raise ValueError("Password is empty.")

    spec = USE_CASES[use_case]
    length = int(spec["length"])
    alphabet = str(spec["alphabet"])

    if len(password) != length:
        raise ValueError(f"Password must have exactly {length} characters.")
    if any(char not in alphabet for char in password):
        raise ValueError(f"Only these characters are allowed: {alphabet}")


def hash_protected(
    password: str, iterations: int = ITERATIONS
) -> dict[str, str | int]:
    """Hash `password` with a random salt using PBKDF2-HMAC-SHA256.

    Returns:
        dict[str, str | int]: {"salt": hex str, "iterations": int, "hash": hex str}
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string.")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("Iterations must be a positive integer.")

    salt = os.urandom(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return {
        "salt": salt.hex(),
        "iterations": iterations,
        "hash": derived.hex(),
    }


def _parse_record(record: Any) -> tuple[bytes, int, str]:
    """Validate a protected record dictionary and return (salt_bytes, iterations, hash_hex)."""
    if not isinstance(record, dict):
        raise ValueError("Malformed record.")
    if set(record.keys()) != {"salt", "iterations", "hash"}:
        raise ValueError("Malformed record.")

    salt_hex = record.get("salt")
    iterations = record.get("iterations")
    hash_hex = record.get("hash")

    if not isinstance(salt_hex, str) or not salt_hex:
        raise ValueError("Malformed record.")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("Malformed record.")
    if not isinstance(hash_hex, str) or len(hash_hex) != 64:
        raise ValueError("Malformed record.")

    try:
        salt_bytes = bytes.fromhex(salt_hex)
        bytes.fromhex(hash_hex)
    except ValueError as exc:
        raise ValueError("Malformed record.") from exc

    if not salt_bytes:
        raise ValueError("Malformed record.")

    return salt_bytes, iterations, hash_hex.lower()


def verify_protected(password: str, record: dict[str, Any]) -> bool:
    """Verify `password` against a protected `record` using constant-time comparison."""
    if not isinstance(password, str):
        raise ValueError("Password must be a string.")
    salt_bytes, iterations, expected_hash = _parse_record(record)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        iterations,
    ).hex()
    return hmac.compare_digest(derived, expected_hash)


def make_checker(target: str | dict[str, Any]) -> Callable[[str], bool]:
    """Build a `check(candidate) -> bool` callable for a fast hash or protected record."""
    if isinstance(target, str):
        stripped = target.strip()
        if not stripped:
            raise ValueError("Target hash string is empty.")
        try:
            bytes.fromhex(stripped)
        except ValueError as exc:
            raise ValueError("Target string must be valid hexadecimal.") from exc
        normalized_target = stripped.lower()
        return lambda candidate: hmac.compare_digest(hash_fast(candidate), normalized_target)

    if isinstance(target, dict):
        _parse_record(target)
        snapshot = dict(target)
        return lambda candidate: verify_protected(candidate, snapshot)

    raise ValueError("Target must be a hex string or a protected record dict.")


class Lockout:
    """Track failed login attempts and enforce a temporary lockout window."""

    def __init__(
        self,
        max_failures: int = MAX_FAILURES,
        lock_seconds: float = LOCK_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if isinstance(max_failures, bool) or not isinstance(max_failures, int) or max_failures <= 0:
            raise ValueError("max_failures must be a positive integer.")
        if isinstance(lock_seconds, bool) or not isinstance(lock_seconds, (int, float)) or lock_seconds <= 0:
            raise ValueError("lock_seconds must be positive.")
        self.max_failures = max_failures
        self.lock_seconds = float(lock_seconds)
        self._clock = clock
        self._failures = 0
        self._locked_until: float | None = None

    def remaining(self) -> float:
        """Return seconds remaining in the current lock window, or 0.0 if unlocked."""
        if self._locked_until is None:
            return 0.0
        left = self._locked_until - float(self._clock())
        if left <= 0.0:
            self._locked_until = None
            return 0.0
        return float(left)

    def attempts_left(self) -> int:
        """Return the number of attempts remaining before lockout."""
        if self.remaining() > 0.0:
            return 0
        return self.max_failures - self._failures

    def record(self, success: bool) -> bool:
        """Record a login attempt outcome.

        Raises:
            ValueError: If currently locked, even when `success` is True.
        """
        rem = self.remaining()
        if rem > 0.0:
            n = max(1, int(math.ceil(rem)))
            raise ValueError(f"Locked. Try again in {n} s.")

        if success:
            self._failures = 0
            return True

        self._failures += 1
        if self._failures >= self.max_failures:
            self._locked_until = float(self._clock()) + self.lock_seconds
            self._failures = 0
        return False

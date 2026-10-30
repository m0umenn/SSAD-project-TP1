"""Password validation, encryption-based protection, verification, and lockout.

Part 3 protects passwords by encrypting them with ciphers instead of hashing.
The secret key is never stored in the record or logged.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import Any

from passwords import cipher_adapter
from passwords.cipher_adapter import USE_CASE_CIPHER, block_size, get_alphabet
from passwords.generators import USE_CASES

MAX_FAILURES: int = 5
LOCK_SECONDS: float = 30.0


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


def protect(
    password: str,
    use_case: int,
    cipher: str | None = None,
    key: Any = None,
) -> dict[str, Any]:
    """Validate password for the use case, encrypt it, and return the protected record.

    The secret key is never included in the record.

    Returns:
        dict[str, Any]: {
            "use_case": int,
            "cipher": str,
            "ciphertext": str,
            "params": {"modulus": m, "block": n}
        }
    """
    validate_password(password, use_case)

    # Resolve cipher name
    if cipher is None or cipher == "":
        cipher_name = USE_CASE_CIPHER.get(use_case, "hill")
    else:
        cipher_name = str(cipher).lower().strip()

    # Parse key strictly
    parsed_key = cipher_adapter.parse_key(key, use_case, cipher_name)

    ciphertext = cipher_adapter.encrypt(password, parsed_key, use_case, cipher_name)

    alphabet = get_alphabet(use_case)
    m = len(alphabet)
    n = block_size(use_case) if cipher_name == "hill" else 1

    params: dict[str, Any] = {"modulus": m, "block": n}

    return {
        "use_case": use_case,
        "cipher": cipher_name,
        "ciphertext": ciphertext,
        "params": params,
    }


def make_checker(record: dict[str, Any], key: Any) -> Callable[[str], bool]:
    """Build a `check(candidate) -> bool` callable using the record and secret key.

    Encrypts the candidate with `key` and compares it with `record['ciphertext']`.
    The key stays strictly inside the closure.
    """
    if not isinstance(record, dict):
        raise ValueError("Malformed record.")
    if "use_case" not in record or "ciphertext" not in record:
        raise ValueError("Malformed record.")

    use_case = int(record["use_case"])
    cipher_name = str(record.get("cipher", USE_CASE_CIPHER.get(use_case, "hill")))
    expected_ciphertext = str(record["ciphertext"])

    # Parse and close over the key — it never leaves this scope
    parsed_key = cipher_adapter.parse_key(key, use_case, cipher_name)

    def check(candidate: str) -> bool:
        if not isinstance(candidate, str):
            return False
        try:
            cand_ct = cipher_adapter.encrypt(candidate, parsed_key, use_case, cipher_name)
            return cand_ct == expected_ciphertext
        except Exception:
            return False

    return check


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

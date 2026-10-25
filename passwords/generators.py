"""Password use case definitions, fast hashing, and candidate generation."""

from __future__ import annotations

import hashlib
import itertools
from collections.abc import Iterator

CASE_3_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "+*"
)

USE_CASES: dict[int, dict[str, str | int]] = {
    1: {"alphabet": "01", "length": 3},
    2: {"alphabet": "1234", "length": 4},
    3: {"alphabet": CASE_3_ALPHABET, "length": 4},
    4: {"alphabet": CASE_3_ALPHABET, "length": 6},
    5: {"alphabet": CASE_3_ALPHABET, "length": 8},
}



def hash_fast(password: str) -> str:
    """Return the SHA-256 hexadecimal digest of `password` (unprotected fast hash)."""
    if not isinstance(password, str):
        raise ValueError("Password must be a string.")
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def candidates(alphabet: str, length: int) -> Iterator[str]:
    """Yield all passwords of `length` over `alphabet` in lexicographic product order.

    Uses `itertools.product(alphabet, repeat=length)` so that the leftmost
    character changes slowest and the rightmost character changes fastest.
    """
    if not isinstance(alphabet, str) or not alphabet:
        raise ValueError("Alphabet must be a non-empty string.")
    if isinstance(length, bool) or not isinstance(length, int) or length <= 0:
        raise ValueError("Length must be a positive integer.")
    for combo in itertools.product(alphabet, repeat=length):
        yield "".join(combo)

"""Caesar cipher over a 52-letter alphabet (a-z then A-Z), modulo 52.

Specification (the_Caesar_algorithm_2.pdf):
  - index: a..z -> 0..25, A..Z -> 26..51
  - encryption: C = (M + n) mod 52      decryption: M = (C - n) mod 52
  - key n: integer with 1 <= |n| <= 51
      n > 0 : shift right by n        n < 0 : shift left by |n|
      (a left shift by n equals a right shift by 52 - n)
  - only the letters a-z / A-Z are encrypted; spaces, digits, punctuation and
    accented characters are left unchanged.

Weaknesses: only 51 meaningful keys (brute force), and the letter frequencies
of the plaintext are preserved (frequency analysis). Both attacks are
implemented below.
Owner: <name>

Key format accepted: int, or str such as "4", "-4", "+4", "R4" (right),
"L4" (left), case-insensitive.
"""

from __future__ import annotations

import string

ALPHABET = string.ascii_lowercase + string.ascii_uppercase
SIZE = len(ALPHABET)
_INDEX = {char: index for index, char in enumerate(ALPHABET)}

FREQ_FR = {
    "a": 7.64, "b": 0.90, "c": 3.26, "d": 3.67, "e": 14.72, "f": 1.07,
    "g": 0.87, "h": 0.74, "i": 7.53, "j": 0.55, "k": 0.05, "l": 5.46,
    "m": 2.97, "n": 7.10, "o": 5.80, "p": 2.52, "q": 1.36, "r": 6.69,
    "s": 7.95, "t": 7.24, "u": 6.31, "v": 1.84, "w": 0.05, "x": 0.43,
    "y": 0.13, "z": 0.33,
}


def _parse_key(key) -> int:
    """Convert a key to a signed integer; raise ValueError if invalid."""
    if isinstance(key, bool):
        raise ValueError("Key must be an integer.")
    if isinstance(key, int):
        n = key
    elif isinstance(key, str):
        candidate = key.strip().upper().replace(" ", "")
        if not candidate:
            raise ValueError("Key is empty.")
        sign = 1
        if candidate.startswith("L"):
            sign = -1
            candidate = candidate[1:]
        elif candidate.startswith("R"):
            candidate = candidate[1:]
        try:
            n = sign * int(candidate)
        except ValueError as exc:
            raise ValueError(f"Invalid key: {key!r}") from exc
    else:
        raise ValueError("Key must be an integer.")

    if not 1 <= abs(n) <= SIZE - 1:
        raise ValueError(f"Key must satisfy 1 <= |n| <= {SIZE - 1}.")
    return n


def validate_key(key) -> bool:
    """Return True if `key` is a valid Caesar key (1 <= |n| <= 51)."""
    try:
        _parse_key(key)
    except ValueError:
        return False
    return True


def _shift(text: str, n: int) -> str:
    """Apply a Caesar shift over the 52-letter alphabet while leaving other characters unchanged."""
    out: list[str] = []
    for char in text:
        index = _INDEX.get(char)
        if index is not None:
            out.append(ALPHABET[(index + n) % SIZE])
        else:
            out.append(char)
    return "".join(out)


def encrypt(text: str, key) -> str:
    """Encrypt text: C = (M + n) mod 52."""
    return _shift(text, _parse_key(key))


def decrypt(text: str, key) -> str:
    """Decrypt text: M = (C - n) mod 52."""
    return _shift(text, -_parse_key(key))


def brute_force(cipher: str) -> list[tuple[int, str]]:
    """Try all 51 meaningful keys. Returns [(key, candidate_plaintext), ...]."""
    return [(n, decrypt(cipher, n)) for n in range(1, SIZE)]


def _score(text: str) -> float:
    """Lower is better: distance to French frequencies + capitalisation penalty."""
    letters = [char for char in text if char in _INDEX]
    if not letters:
        return float("inf")
    total = len(letters)
    lowered = [char.lower() for char in letters]
    distance = sum(
        (lowered.count(letter) / total * 100 - FREQ_FR[letter]) ** 2
        for letter in string.ascii_lowercase
    )
    inner_caps = sum(
        1
        for index, char in enumerate(text)
        if char.isupper() and char in _INDEX and index > 0 and text[index - 1] in _INDEX
    )
    return distance + 300 * inner_caps / total


def frequency_attack(cipher: str, top: int = 3) -> list[tuple[int, str]]:
    """Rank the 51 keys by how much the result looks like French text."""
    ranked = sorted(brute_force(cipher), key=lambda item: _score(item[1]))
    return ranked[:top]
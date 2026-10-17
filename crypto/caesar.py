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

ALPHABET = string.ascii_lowercase + string.ascii_uppercase  # 52 symbols
SIZE = len(ALPHABET)  # 52
_INDEX = {c: i for i, c in enumerate(ALPHABET)}

# Approximate letter frequencies in French (%), case-insensitive.
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
        k = key.strip().upper().replace(" ", "")
        if not k:
            raise ValueError("Key is empty.")
        sign = 1
        if k[0] == "L":
            sign, k = -1, k[1:]
        elif k[0] == "R":
            k = k[1:]
        try:
            n = sign * int(k)
        except ValueError:
            raise ValueError(f"Invalid key: {key!r}") from None
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
    out = []
    for c in text:
        i = _INDEX.get(c)
        out.append(ALPHABET[(i + n) % SIZE] if i is not None else c)
    return "".join(out)


def encrypt(text: str, key) -> str:
    """Encrypt text: C = (M + n) mod 52."""
    return _shift(text, _parse_key(key))


def decrypt(text: str, key) -> str:
    """Decrypt text: M = (C - n) mod 52."""
    return _shift(text, -_parse_key(key))


# ------------------------- Attacks (security flaws) -------------------------

def brute_force(cipher: str) -> list[tuple[int, str]]:
    """Try all 51 meaningful keys. Returns [(key, candidate_plaintext), ...]."""
    return [(n, decrypt(cipher, n)) for n in range(1, SIZE)]


def _score(text: str) -> float:
    """Lower is better: distance to French frequencies + capitalisation penalty."""
    letters = [c for c in text if c in _INDEX]
    if not letters:
        return float("inf")
    total = len(letters)
    low = [c.lower() for c in letters]
    dist = sum(
        (low.count(a) / total * 100 - FREQ_FR[a]) ** 2 for a in string.ascii_lowercase
    )
    # A real text rarely has capitals inside words: penalise them.
    inner_caps = sum(
        1 for i, c in enumerate(text)
        if c.isupper() and c in _INDEX and i > 0 and text[i - 1] in _INDEX
    )
    return dist + 300 * inner_caps / total


def frequency_attack(cipher: str, top: int = 3) -> list[tuple[int, str]]:
    """Rank the 51 keys by how much the result looks like French text.

    Returns the `top` most likely [(key, candidate_plaintext), ...].
    """
    ranked = sorted(brute_force(cipher), key=lambda kt: _score(kt[1]))
    return ranked[:top]


if __name__ == "__main__":
    # Test cases from the specification (the_Caesar_algorithm_2.pdf)
    cases = [
        ("Meriem", 4, "Qivmiq"),
        ("Zoe", 3, "crh"),
        ("xyz", 3, "ABC"),
        ("XYZ", 3, "abc"),
        ("abc", -3, "XYZ"),
        ("Hello World 2026!", 5, "Mjqqt btwqi 2026!"),
    ]
    ok = True
    for msg, key, expected in cases:
        got = encrypt(msg, key)
        back = decrypt(got, key)
        status = "OK " if got == expected and back == msg else "FAIL"
        ok &= status == "OK "
        print(f"{status} {msg!r:22} n={key:3} -> {got!r}  (expected {expected!r})")
    print("validate_key:", validate_key(4), validate_key(-3), validate_key("L2"),
          validate_key(0), validate_key(52), validate_key("abc"))
    print("ALL SPEC TESTS PASSED" if ok else "SOME TESTS FAILED")

    text = "Rendez vous demain devant la bibliotheque de l'universite"
    c = encrypt(text, 17)
    print("\nattack on:", c)
    for k, t in frequency_attack(c):
        print(f"  key {k:2d} -> {t}")

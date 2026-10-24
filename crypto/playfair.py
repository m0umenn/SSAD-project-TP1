"""Playfair cipher.

Weaknesses: vulnerable to digraph frequency analysis, uses I/J merge, and needs padding rules.
Owner: <name>
"""

from __future__ import annotations

_ALPHABET = "ABCDEFGHIKLMNOPQRSTUVWXYZ"  # 25 letters, J merged into I


def _clean(text: str) -> str:
    """Uppercase, keep only A-Z, replace J with I."""
    text = "".join(c for c in text.upper() if "A" <= c <= "Z")
    return text.replace("J", "I")


def _filler(letter: str) -> str:
    """Padding letter: X, or Q if the letter to pair with is already X."""
    return "Q" if letter == "X" else "X"


def _build_matrix(key: str) -> list[list[str]]:
    """Build the 5x5 key matrix from the keyword."""
    seen: list[str] = []
    for c in _clean(key) + _ALPHABET:
        if c not in seen:
            seen.append(c)
    return [seen[i:i + 5] for i in range(0, 25, 5)]


def _positions(matrix: list[list[str]]) -> dict[str, tuple[int, int]]:
    return {c: (r, col) for r, row in enumerate(matrix) for col, c in enumerate(row)}


def _prepare(text: str) -> list[str]:
    """Clean the message and split it into digraphs, adding padding where needed."""
    text = _clean(text)
    pairs = []
    i = 0
    while i < len(text):
        a = text[i]
        if i + 1 < len(text) and text[i + 1] != a:
            pairs.append(a + text[i + 1])
            i += 2
        else:  # identical letters, or a single letter left at the end
            pairs.append(a + _filler(a))
            i += 1
    return pairs


def _transform_pair(pair: str, matrix, pos, shift: int) -> str:
    """shift = +1 to encrypt, -1 to decrypt."""
    (r1, c1), (r2, c2) = pos[pair[0]], pos[pair[1]]
    if r1 == r2:  # same row
        return matrix[r1][(c1 + shift) % 5] + matrix[r2][(c2 + shift) % 5]
    if c1 == c2:  # same column
        return matrix[(r1 + shift) % 5][c1] + matrix[(r2 + shift) % 5][c2]
    return matrix[r1][c2] + matrix[r2][c1]  # rectangle


def _remove_padding(text: str) -> str:
    """Remove padding added during preparation (best effort).

    A genuine X can be indistinguishable from padding (e.g. "AXA" or a final X),
    so this is ambiguous by nature.
    """
    n = len(text)
    out = []
    for i, c in enumerate(text):
        if 0 < i < n - 1 and text[i - 1] == text[i + 1] and c == _filler(text[i - 1]):
            continue
        out.append(c)
    if len(out) >= 2 and out[-1] == _filler(out[-2]):
        out.pop()
    return "".join(out)


def validate_key(key) -> bool:
    """Validate a Playfair cipher key.

    A valid key is a non-empty string made of letters (spaces are ignored).
    J is treated as I, and repeated letters are dropped when the matrix is built.
    """

    if not isinstance(key, str):
        return False
    stripped = key.replace(" ", "")
    return bool(stripped) and stripped.isascii() and stripped.isalpha()


def encrypt(text: str, key) -> str:
    """Encrypt text using the Playfair cipher.

    The text is uppercased, stripped of non-letters, J becomes I, and padding
    (X, or Q after an X) is inserted between identical letters and at the end
    if the length is odd.
    """

    if not validate_key(key):
        raise ValueError("Invalid Playfair key: use a non-empty string of letters.")
    matrix = _build_matrix(key)
    pos = _positions(matrix)
    return "".join(_transform_pair(p, matrix, pos, 1) for p in _prepare(text))


def decrypt(text: str, key) -> str:
    """Decrypt text using the Playfair cipher.

    Padding added during encryption is removed (best effort). The original J
    cannot be recovered because it was merged into I.
    """

    if not validate_key(key):
        raise ValueError("Invalid Playfair key: use a non-empty string of letters.")
    cipher = _clean(text)
    if len(cipher) % 2:
        raise ValueError("Ciphertext must contain an even number of letters.")
    matrix = _build_matrix(key)
    pos = _positions(matrix)
    pairs = [cipher[i:i + 2] for i in range(0, len(cipher), 2)]
    plain = "".join(_transform_pair(p, matrix, pos, -1) for p in pairs)
    return _remove_padding(plain)
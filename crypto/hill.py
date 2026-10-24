

from __future__ import annotations

import math
from collections.abc import Sequence


def normalize(text: str) -> str:
    """Return the uppercase text with all non-letter characters removed."""
    if not isinstance(text, str):
        text = str(text)
    return "".join(char for char in text.upper() if "A" <= char <= "Z")


def _coerce_key(key) -> list[list[int]] | None:
    """Normalize a candidate key and reject malformed inputs."""
    if not isinstance(key, Sequence) or isinstance(key, (str, bytes)):
        return None

    rows = [list(row) for row in key]
    if not rows or len(rows) not in (2, 3):
        return None

    size = len(rows)
    if any(not isinstance(row, Sequence) or isinstance(row, (str, bytes)) for row in rows):
        return None
    if any(len(row) != size for row in rows):
        return None

    normalized: list[list[int]] = []
    for row in rows:
        cleaned: list[int] = []
        for entry in row:
            if isinstance(entry, bool) or not isinstance(entry, int):
                return None
            cleaned.append(entry % 26)
        normalized.append(cleaned)
    return normalized


def determinant(key) -> int:
    """Return the determinant of a 2x2 or 3x3 integer key matrix."""
    normalized = _coerce_key(key)
    if normalized is None:
        raise ValueError("Key must be a 2x2 or 3x3 square matrix of integers.")

    size = len(normalized)
    if size == 2:
        return normalized[0][0] * normalized[1][1] - normalized[0][1] * normalized[1][0]

    if size == 3:
        a, b, c = normalized[0]
        d, e, f = normalized[1]
        g, h, i = normalized[2]
        return (
            a * (e * i - f * h)
            - b * (d * i - f * g)
            + c * (d * h - e * g)
        )

    raise ValueError("Key must be a 2x2 or 3x3 square matrix of integers.")


def inverse_key(key) -> list[list[int]]:
    """Return the modular inverse of a valid Hill key matrix modulo 26."""
    normalized = _coerce_key(key)
    if normalized is None:
        raise ValueError("Key must be a 2x2 or 3x3 square matrix of integers.")

    det_mod = determinant(normalized) % 26
    gcd_value = math.gcd(det_mod, 26)
    if gcd_value != 1:
        raise ValueError(f"Key is not invertible mod 26: gcd(det, 26) = {gcd_value}")

    inverse_det = pow(det_mod, -1, 26)
    size = len(normalized)

    if size == 2:
        a, b = normalized[0]
        c, d = normalized[1]
        adjugate = [[d, -b], [-c, a]]
    else:
        a, b, c = normalized[0]
        d, e, f = normalized[1]
        g, h, i = normalized[2]
        cofactor = [
            [
                (e * i - f * h),
                -(d * i - f * g),
                (d * h - e * g),
            ],
            [
                -(b * i - c * h),
                (a * i - c * g),
                -(a * h - b * g),
            ],
            [
                (b * f - c * e),
                -(a * f - c * d),
                (a * e - b * d),
            ],
        ]
        adjugate = [
            [cofactor[r][c] for r in range(size)]
            for c in range(size)
        ]

    inverse = [
        [((entry * inverse_det) % 26) for entry in row]
        for row in adjugate
    ]
    return inverse


def validate_key(key) -> bool:
    """Return True only for invertible 2x2 or 3x3 integer matrices mod 26."""
    normalized = _coerce_key(key)
    if normalized is None:
        return False

    try:
        det_mod = determinant(normalized) % 26
    except ValueError:
        return False

    return math.gcd(det_mod, 26) == 1


def padding_length(text: str, n: int) -> int:
    """Return the number of trailing 'X' letters needed to complete the block."""
    normalized = normalize(text)
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("Block size must be a positive integer.")
    remainder = len(normalized) % n
    return 0 if remainder == 0 else n - remainder


def _matrix_multiply(matrix: list[list[int]], vector: list[int]) -> list[int]:
    """Multiply a key matrix by a column vector modulo 26."""
    return [
        sum(matrix[row_index][col_index] * vector[col_index] for col_index in range(len(vector))) % 26
        for row_index in range(len(matrix))
    ]


def encrypt(text: str, key) -> str:
    """Encrypt a message with the Hill cipher using a valid invertible key.

    Known weaknesses: the cipher is linear and vulnerable to known-plaintext
    attacks, and the key matrix must be invertible modulo 26.
    """
    normalized = normalize(text)
    if not normalized:
        raise ValueError("Message has no letters A-Z.")

    normalized_key = _coerce_key(key)
    if normalized_key is None:
        raise ValueError("Key must be a 2x2 or 3x3 square matrix of integers.")

    det_mod = determinant(normalized_key) % 26
    gcd_value = math.gcd(det_mod, 26)
    if gcd_value != 1:
        raise ValueError(f"Key is not invertible mod 26: gcd(det, 26) = {gcd_value}")

    block_size = len(normalized_key)
    padded = normalized + ("X" * padding_length(normalized, block_size))
    ciphertext_letters: list[str] = []

    for start in range(0, len(padded), block_size):
        block = padded[start : start + block_size]
        vector = [ord(letter) - 65 for letter in block]
        encrypted_vector = _matrix_multiply(normalized_key, vector)
        ciphertext_letters.extend(chr(value + 65) for value in encrypted_vector)

    return "".join(ciphertext_letters)


def decrypt(text: str, key, pad_len: int | None = None) -> str:
    """Decrypt a Hill-cipher message and optionally strip trailing padding.

    If pad_len is None, the padded text is returned unchanged. Otherwise the
    final pad_len letters are removed after decryption.
    """
    normalized_key = _coerce_key(key)
    if normalized_key is None:
        raise ValueError("Key must be a 2x2 or 3x3 square matrix of integers.")

    det_mod = determinant(normalized_key) % 26
    gcd_value = math.gcd(det_mod, 26)
    if gcd_value != 1:
        raise ValueError(f"Key is not invertible mod 26: gcd(det, 26) = {gcd_value}")

    block_size = len(normalized_key)
    normalized_cipher = normalize(text)
    if len(normalized_cipher) % block_size != 0:
        raise ValueError(
            f"Ciphertext length {len(normalized_cipher)} is not a multiple of the key size {block_size}."
        )

    inverse_matrix = inverse_key(normalized_key)
    plaintext_letters: list[str] = []
    for start in range(0, len(normalized_cipher), block_size):
        block = normalized_cipher[start : start + block_size]
        vector = [ord(letter) - 65 for letter in block]
        decoded_vector = _matrix_multiply(inverse_matrix, vector)
        plaintext_letters.extend(chr(value + 65) for value in decoded_vector)

    decoded = "".join(plaintext_letters)

    if pad_len is None:
        return decoded

    if not isinstance(pad_len, int) or isinstance(pad_len, bool) or pad_len < 0 or pad_len >= block_size:
        raise ValueError(f"Padding length must be between 0 and {block_size - 1}.")
    if pad_len > len(decoded):
        raise ValueError("Padding length is larger than the decrypted text length.")

    return decoded[:-pad_len] if pad_len else decoded

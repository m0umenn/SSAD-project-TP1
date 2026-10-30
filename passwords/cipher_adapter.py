"""Password cipher adapter: the only place that knows the ciphers used for passwords.

Maps use cases to alphabets and ciphers, and provides encrypt / decrypt / parse_key
for Caesar and Hill over the use-case-specific alphabets.

Playfair is intentionally not offered for passwords:
  - Use cases 1 ("01") and 2 ("1234") have only 2 or 4 symbols, which are too
    small to build a 5x5 or any valid Playfair grid.
  - Use cases 3–5 use the 64-symbol alphabet; Playfair needs filler characters when
    a bigram contains the same letter twice, which changes the ciphertext length and
    makes reliable round-trips impossible for fixed-length password slots.

Does NOT import from crypto/.
"""

from __future__ import annotations

import math
from typing import Any

from passwords.generators import CASE_3_ALPHABET, USE_CASES

# ---------------------------------------------------------------------------
# Alphabets
# ---------------------------------------------------------------------------

USE_CASE_ALPHABETS: dict[int, str] = {
    1: "01",          # m=2,  length 3
    2: "1234",        # m=4,  length 4
    3: CASE_3_ALPHABET,  # m=64, length 4
    4: CASE_3_ALPHABET,  # m=64, length 6
    5: CASE_3_ALPHABET,  # m=64, length 8
}

# ---------------------------------------------------------------------------
# Default ciphers and block sizes: (cipher_name, block_n)
# The password length is always a multiple of block_n so no padding is needed.
# ---------------------------------------------------------------------------

USE_CASE_CIPHER: dict[int, str] = {
    1: "hill",
    2: "hill",
    3: "hill",
    4: "hill",
    5: "hill",
}

_USE_CASE_BLOCK: dict[int, int] = {
    1: 3,  # length 3, n=3 → one block
    2: 2,  # length 4, n=2 → two blocks
    3: 2,  # length 4, n=2 → two blocks
    4: 3,  # length 6, n=3 → two blocks
    5: 2,  # length 8, n=2 → four blocks
}


def block_size(use_case: int) -> int:
    """Return the default Hill block size n for *use_case*.

    Parameters:
        use_case (int): Use-case identifier (1-5).

    Returns:
        int: Default block size n for Hill cipher.

    Raises:
        ValueError: If *use_case* is unknown.
    """
    if isinstance(use_case, bool) or use_case not in _USE_CASE_BLOCK:
        raise ValueError("Unknown use case.")
    return _USE_CASE_BLOCK[use_case]


def get_alphabet(use_case: int) -> str:
    """Return the allowed alphabet string for *use_case*.

    Parameters:
        use_case (int): Use-case identifier (1-5).

    Returns:
        str: The alphabet string for that use case.

    Raises:
        ValueError: If *use_case* is unknown.
    """
    if isinstance(use_case, bool) or use_case not in USE_CASE_ALPHABETS:
        raise ValueError("Unknown use case.")
    return USE_CASE_ALPHABETS[use_case]


# ---------------------------------------------------------------------------
# Internal math helpers (no crypto/ imports)
# ---------------------------------------------------------------------------

def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def _det2(m: list[list[int]]) -> int:
    """Determinant of a 2×2 integer matrix."""
    return m[0][0] * m[1][1] - m[0][1] * m[1][0]


def _det3(m: list[list[int]]) -> int:
    """Determinant of a 3×3 integer matrix (Sarrus)."""
    a = m[0]
    b = m[1]
    c = m[2]
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def _adjugate2(m: list[list[int]]) -> list[list[int]]:
    """Adjugate (classical adjoint) of a 2×2 matrix: adj([[a,b],[c,d]])=[[d,-b],[-c,a]]."""
    return [
        [m[1][1], -m[0][1]],
        [-m[1][0], m[0][0]],
    ]


def _adjugate3(m: list[list[int]]) -> list[list[int]]:
    """Adjugate of a 3×3 matrix via cofactors (transposed cofactor matrix)."""
    n = 3
    adj: list[list[int]] = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            # cofactor C_{r,c} = (-1)^{r+c} * minor(r, c)
            minor_rows = [m[i] for i in range(n) if i != r]
            minor = [[minor_rows[i][j] for j in range(n) if j != c] for i in range(2)]
            cofactor = ((-1) ** (r + c)) * _det2(minor)
            adj[c][r] = cofactor  # transpose
    return adj


def _mat_vec_mod(mat: list[list[int]], vec: list[int], mod: int) -> list[int]:
    """Matrix-vector product mod *mod*."""
    n = len(mat)
    return [sum(mat[r][c] * vec[c] for c in range(n)) % mod for r in range(n)]


def _mat_mod(mat: list[list[int]], mod: int) -> list[list[int]]:
    return [[x % mod for x in row] for row in mat]


def _scale_mat_mod(scalar: int, mat: list[list[int]], mod: int) -> list[list[int]]:
    return [[(scalar * x) % mod for x in row] for row in mat]


def _is_identity(mat: list[list[int]]) -> bool:
    n = len(mat)
    for r in range(n):
        for c in range(n):
            expected = 1 if r == c else 0
            if mat[r][c] != expected:
                return False
    return True


# ---------------------------------------------------------------------------
# Key parsing
# ---------------------------------------------------------------------------

def _parse_caesar_key(raw: Any, modulus: int) -> int:
    """Parse and validate a Caesar shift key.

    Parameters:
        raw: The raw key value (int or str).
        modulus (int): Alphabet size m; key must be in [1, m-1].

    Returns:
        int: Validated shift value.

    Raises:
        ValueError: If key is empty, non-integer, or out of range.
    """
    if isinstance(raw, bool):
        raise ValueError("Key must be an integer, not a boolean.")
    if isinstance(raw, int):
        k = raw
    elif isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            raise ValueError("Key cannot be empty.")
        try:
            k = int(stripped)
        except ValueError as exc:
            raise ValueError(f"Key must be an integer, got: {raw!r}") from exc
    else:
        raise ValueError(f"Key must be an integer, got: {type(raw).__name__}")

    if not (1 <= k <= modulus - 1):
        raise ValueError(
            f"Caesar key must be between 1 and {modulus - 1} (got {k})."
        )
    return k


def _parse_hill_key(raw: Any, n: int, modulus: int) -> list[list[int]]:
    """Parse and validate a Hill n×n key matrix.

    *raw* may be a list of lists (already parsed), a flat list of n² ints, or a
    string of n² space-/comma-separated integers.

    Parameters:
        raw: Raw key — list[list[int]], list[int], or str.
        n (int): Block size (2 or 3).
        modulus (int): Alphabet size m.

    Returns:
        list[list[int]]: n×n matrix with each entry in [0, m-1].

    Raises:
        ValueError: Friendly message for every validation failure.
    """
    expected = n * n

    # --- normalise to flat list of ints ---
    if isinstance(raw, bool):
        raise ValueError("Key must be a matrix, not a boolean.")

    if isinstance(raw, list):
        # already list[list[int]] ?
        if raw and isinstance(raw[0], list):
            flat = [raw[r][c] for r in range(len(raw)) for c in range(len(raw[r]))]
        else:
            flat = list(raw)
    elif isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            raise ValueError("Key cannot be empty.")
        import re
        tokens = re.split(r"[\s,]+", stripped)
        tokens = [t for t in tokens if t]
        flat = []
        for tok in tokens:
            try:
                flat.append(int(tok))
            except ValueError:
                raise ValueError(
                    f"Key entry {tok!r} is not an integer. "
                    f"Provide {expected} integers separated by spaces or commas."
                )
    else:
        raise ValueError(
            f"Hill key must be a list or string, got: {type(raw).__name__}"
        )

    if len(flat) != expected:
        raise ValueError(
            f"Hill {n}×{n} key needs {expected} integers, got {len(flat)}."
        )

    # range check
    for i, val in enumerate(flat):
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(f"Key entry at position {i} must be an integer.")
        if not (0 <= val <= modulus - 1):
            raise ValueError(
                f"Key entry {val} out of range. Each entry must be 0..{modulus - 1}."
            )

    mat = [[flat[r * n + c] for c in range(n)] for r in range(n)]

    # identity check
    if _is_identity(mat):
        raise ValueError(
            "Identity matrix is not allowed as a Hill key (it would not change the password)."
        )

    # invertibility: gcd(det, m) = 1
    det = _det2(mat) if n == 2 else _det3(mat)
    if _gcd(det % modulus, modulus) != 1:
        raise ValueError(
            f"determinant shares a factor with the alphabet size "
            f"({det % modulus} and {modulus} are not coprime). "
            f"Choose a different key matrix."
        )

    return mat


def parse_key(raw: Any, use_case: int = 3, cipher: str = "hill") -> Any:
    """Parse and validate a key for the given *use_case* and *cipher*.

    Parameters:
        raw: Raw key string / list / int typed by the user.
        use_case (int): Use-case identifier (1-5).
        cipher (str): ``"caesar"`` or ``"hill"``.

    Returns:
        For Caesar: int shift k (1 ≤ k ≤ m-1).
        For Hill:   list[list[int]] n×n matrix.

    Raises:
        ValueError: Friendly error for any validation failure.
    """
    alphabet = get_alphabet(use_case)
    m = len(alphabet)
    cipher = cipher.lower().strip()
    if cipher == "caesar":
        return _parse_caesar_key(raw, m)
    elif cipher == "hill":
        n = block_size(use_case)
        return _parse_hill_key(raw, n, m)
    else:
        raise ValueError(f"Unknown cipher: {cipher!r}. Choose 'caesar' or 'hill'.")


# ---------------------------------------------------------------------------
# Hill encrypt / decrypt helpers
# ---------------------------------------------------------------------------

def _hill_encrypt_blocks(
    indices: list[int], mat: list[list[int]], n: int, m: int
) -> list[int]:
    """Encrypt a flat list of indices using Hill cipher in blocks of n."""
    result: list[int] = []
    for i in range(0, len(indices), n):
        block = indices[i: i + n]
        enc = _mat_vec_mod(mat, block, m)
        result.extend(enc)
    return result


def _hill_inverse(mat: list[list[int]], modulus: int) -> list[list[int]]:
    """Compute the modular inverse of a Hill key matrix."""
    n = len(mat)
    det = _det2(mat) if n == 2 else _det3(mat)
    det_mod = det % modulus
    det_inv = pow(det_mod, -1, modulus)  # Python 3.8+
    adj = _adjugate2(mat) if n == 2 else _adjugate3(mat)
    return _scale_mat_mod(det_inv, adj, modulus)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encrypt(
    text: str,
    key: Any,
    use_case: int,
    cipher: str | None = None,
) -> str:
    """Encrypt *text* using the given *cipher* over the *use_case* alphabet.

    Parameters:
        text (str): Plaintext password string.
        key: Shift int (Caesar) or n×n list (Hill), already parsed or raw.
        use_case (int): Use-case identifier (1-5).
        cipher (str | None): ``"caesar"`` or ``"hill"`` (default per use case).

    Returns:
        str: Ciphertext string of the same length as *text*.

    Raises:
        ValueError: On unknown use case, unknown cipher, or key/text issues.
    """
    if not isinstance(text, str):
        raise ValueError("Text must be a string.")
    if isinstance(use_case, bool) or use_case not in USE_CASE_ALPHABETS:
        raise ValueError("Unknown use case.")

    cipher_name = (cipher or USE_CASE_CIPHER[use_case]).lower().strip()
    alphabet = get_alphabet(use_case)
    m = len(alphabet)
    index_map = {ch: i for i, ch in enumerate(alphabet)}

    # Validate all characters
    for ch in text:
        if ch not in index_map:
            raise ValueError(
                f"Character {ch!r} is not in the alphabet for use case {use_case}."
            )
    indices = [index_map[ch] for ch in text]

    if cipher_name == "caesar":
        parsed_key = (
            key if isinstance(key, int) and not isinstance(key, bool)
            else _parse_caesar_key(key, m)
        )
        enc_indices = [(idx + parsed_key) % m for idx in indices]

    elif cipher_name == "hill":
        n = block_size(use_case)
        parsed_key = (
            key if (isinstance(key, list) and key and isinstance(key[0], list))
            else _parse_hill_key(key, n, m)
        )
        if len(indices) % n != 0:
            raise ValueError(
                f"Text length {len(text)} is not divisible by block size {n}."
            )
        enc_indices = _hill_encrypt_blocks(indices, parsed_key, n, m)

    else:
        raise ValueError(f"Unknown cipher: {cipher_name!r}.")

    return "".join(alphabet[i] for i in enc_indices)


def decrypt(
    text: str,
    key: Any,
    use_case: int,
    cipher: str | None = None,
) -> str:
    """Decrypt *text* using the given *cipher* over the *use_case* alphabet.

    Parameters:
        text (str): Ciphertext password string.
        key: Shift int (Caesar) or n×n list (Hill), already parsed or raw.
        use_case (int): Use-case identifier (1-5).
        cipher (str | None): ``"caesar"`` or ``"hill"`` (default per use case).

    Returns:
        str: Plaintext string of the same length as *text*.

    Raises:
        ValueError: On unknown use case, unknown cipher, or key/text issues.
    """
    if not isinstance(text, str):
        raise ValueError("Text must be a string.")
    if isinstance(use_case, bool) or use_case not in USE_CASE_ALPHABETS:
        raise ValueError("Unknown use case.")

    cipher_name = (cipher or USE_CASE_CIPHER[use_case]).lower().strip()
    alphabet = get_alphabet(use_case)
    m = len(alphabet)
    index_map = {ch: i for i, ch in enumerate(alphabet)}

    for ch in text:
        if ch not in index_map:
            raise ValueError(
                f"Character {ch!r} is not in the alphabet for use case {use_case}."
            )
    indices = [index_map[ch] for ch in text]

    if cipher_name == "caesar":
        parsed_key = (
            key if isinstance(key, int) and not isinstance(key, bool)
            else _parse_caesar_key(key, m)
        )
        dec_indices = [(idx - parsed_key) % m for idx in indices]

    elif cipher_name == "hill":
        n = block_size(use_case)
        parsed_key = (
            key if (isinstance(key, list) and key and isinstance(key[0], list))
            else _parse_hill_key(key, n, m)
        )
        if len(indices) % n != 0:
            raise ValueError(
                f"Text length {len(text)} is not divisible by block size {n}."
            )
        inv_key = _hill_inverse(parsed_key, m)
        dec_indices = _hill_encrypt_blocks(indices, inv_key, n, m)

    else:
        raise ValueError(f"Unknown cipher: {cipher_name!r}.")

    return "".join(alphabet[i] for i in dec_indices)

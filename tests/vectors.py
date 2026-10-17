"""Test vectors for the cipher unit tests."""

# The math team fills these in.
CAESAR_VECTORS: list[dict[str, object]] = []
PLAYFAIR_VECTORS: list[dict[str, object]] = []
HILL_VECTORS: list[dict[str, object]] = [
    {"plaintext": "BONJOUR", "key": [[3, 2], [5, 7]], "ciphertext": "FZFYECTM"},
    {
        "plaintext": "BONJOUR",
        "key": [[6, 24, 1], [13, 16, 10], [20, 17, 15]],
        "ciphertext": "RDLUVQBNK",
    },
    {"plaintext": "HELP", "key": [[3, 3], [2, 5]], "ciphertext": "HIAT"},
    {"plaintext": "ALGORITHM", "key": [[6, 24, 1], [13, 16, 10], [20, 17, 15]], "ciphertext": "KCRGONILD"},
]
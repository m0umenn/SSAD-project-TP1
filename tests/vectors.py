"""Test vectors for the cipher unit tests."""

CAESAR_VECTORS: list[dict[str, object]] = [
    {"plaintext": "Meriem", "key": 4, "ciphertext": "Qivmiq"},
    {"plaintext": "Zoe", "key": 3, "ciphertext": "crh"},
    {"plaintext": "xyz", "key": 3, "ciphertext": "ABC"},
    {"plaintext": "XYZ", "key": 3, "ciphertext": "abc"},
    {"plaintext": "abc", "key": -3, "ciphertext": "XYZ"},
    {"plaintext": "Hello World 2026!", "key": 5, "ciphertext": "Mjqqt btwqi 2026!"},
]
PLAYFAIR_VECTORS: list[dict[str, object]] = [
    {"plaintext": "HELLO", "key": "MONARCHY", "ciphertext": "CFSUPM"},
    {"plaintext": "MEETME", "key": "MONARCHY", "ciphertext": "CLKLCL"},
    {"plaintext": "INSTRUMENTS", "key": "MONARCHY", "ciphertext": "GATLMZCLRQXA"},
    {"plaintext": "INFORMATION", "key": "MONARCHY", "ciphertext": "GAPHMORSFAAW"},
    {"plaintext": "EXAMPLE", "key": "KEYWORD", "ciphertext": "WURPSHWU"},
]
HILL_VECTORS: list[dict[str, object]] = [    {"plaintext": "BONJOUR", "key": [[3, 2], [5, 7]], "ciphertext": "FZFYECTM"},
    {
        "plaintext": "BONJOUR",
        "key": [[6, 24, 1], [13, 16, 10], [20, 17, 15]],
        "ciphertext": "RDLUVQBNK",
    },
    {"plaintext": "HELP", "key": [[3, 3], [2, 5]], "ciphertext": "HIAT"},
    {"plaintext": "ALGORITHM", "key": [[6, 24, 1], [13, 16, 10], [20, 17, 15]], "ciphertext": "KCRGONILD"},
]
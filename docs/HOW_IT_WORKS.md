# SSAD Toolkit — How It Works

This technical guide explains the architectural and algorithmic design of the SSAD Toolkit (Python 3.10+, Tkinter, standard library only, Windows).

---

## 1. Project Overview & Architecture

The application is structured around four distinct parts:
1. **Part 1: Classical Ciphers** (`crypto/`): Symmetric encryption algorithms (Caesar, Playfair, Hill).
2. **Part 2: Cryptanalysis & Attacks** (`attacks/`): Brute-force attacks, frequency analysis, known-plaintext cryptanalysis, and dictionary attacks.
3. **Part 3: Password Defence & Storage** (`passwords/`): Password validation, encryption-based protection with secret keys, verification closures, and lockout enforcement.
4. **Part 4: Data Authenticity & Integrity** (`integrity/`): Cryptographic hashing (SHA-256), PBKDF2 stretching, constant-time verification, and slowdown modeling.

```text
SSAD/
├── main.py                     # Entry point (launches gui.app.run_app())
├── benchmarks.py               # Runtime benchmarks
├── crypto/                     # Part 1: Ciphers
│   ├── caesar.py               # Caesar cipher
│   ├── hill.py                 # Hill cipher (matrix math modulo 26)
│   └── playfair.py             # Playfair cipher (5x5 key matrix)
├── attacks/                    # Part 2: Attacks
│   ├── caesar_attack.py        # Caesar brute-force & frequency analysis
│   ├── hill_attack.py          # Known-plaintext attack on Hill
│   └── playfair_attack.py      # Digraph frequency analysis
├── passwords/                  # Part 3: Password Protection via Encryption
│   ├── cipher_adapter.py       # Cipher mapping and dispatch per use case
│   ├── protection.py           # protect(), make_checker(), Lockout, validate_password()
│   ├── generators.py           # USE_CASES and candidate generator
│   ├── brute_force.py          # Brute-force search across candidates
│   └── dictionary.py           # Dictionary attack against candidate words
├── integrity/                  # Part 4: Integrity & Hashing
│   ├── __init__.py             # Exports public hashing functions & constants
│   ├── hashing.py              # SHA-256, PBKDF2-HMAC, compare_hashes, slowdown
│   └── README.md               # API reference for teammates
├── gui/                        # Desktop Interface (Tkinter)
│   ├── app.py                  # Main window shell & navigation sidebar
│   └── pages/                  # Page modules
│       ├── encryption_page.py  # Entity A (Sender) encryption interface
│       ├── decryption_page.py  # Entity B (Receiver) decryption & identity verification interface
│       ├── passwords_page.py   # Password protection & login verification
│       ├── attacks_page.py     # Attack comparison workbench
│       └── integrity_page.py   # Integrity verification page
└── tests/                      # Full test suite
    ├── test_ciphers.py
    ├── test_hill.py
    ├── test_smoke.py
    ├── test_cipher_adapter.py  # Part 3 cipher adapter (Hill+Caesar) vectors & validation
    ├── test_protection.py      # Part 3 protection & lockout tests
    └── test_integrity.py       # Part 4 hashing & integrity tests
```

---

## 2. Part 1: Classical Ciphers (`crypto/`)

The classical ciphers are implemented in dedicated modules under `crypto/`:
- **Caesar Cipher** (`crypto/caesar.py`):
  Shifts characters across the alphabet modulo alphabet length.
- **Playfair Cipher** (`crypto/playfair.py`):
  Digraph substitution cipher using a 5×5 key square (merging I/J). Handles duplicate letters by inserting filler characters (e.g. `X`), and applies standard Playfair row, column, and rectangle rules for encryption and decryption.
- **Hill Cipher** (`crypto/hill.py`):
  Polygraphic substitution cipher using linear algebra modulo 26. Validates key invertibility ($\gcd(\det(K), 26) = 1$), uses modular matrix inversion for decryption, and handles trailing padding.

---

## 3. Part 3: Password Defence via Encryption (`passwords/`)

### Teacher Feedback Requirement
Passwords in Part 3 are protected by **ENCRYPTING them with ciphers**, rather than hashing. All hashing routines are separated into `integrity/` (Part 4).

### Why Not Playfair?
Playfair is deliberately excluded from the password section:
- **Use cases 1 and 2** (`"01"`, `"1234"`) use alphabets of only 2 or 4 symbols — too small to construct any valid Playfair grid (which requires at least 25 unique characters).
- **Use cases 3–5** use the 64-symbol alphabet. Playfair requires inserting filler characters (e.g. `X`) when both letters of a bigram are identical, which **changes the ciphertext length**. Since passwords have a fixed length per use case, a variable-length ciphertext makes reliable round-trips impossible.

### Available Ciphers

| Cipher  | Use cases | Role |
|---------|-----------|------|
| **Hill** | 1–5 | Default: cryptographically stronger matrix cipher |
| **Caesar** | 1–5 | Comparison only: trivial single-character shift |

### Alphabets and Default Block Sizes

| Use case | Alphabet | m | Length | Default block n |
|----------|----------|---|--------|----------------|
| 1 | `"01"` | 2 | 3 | 3 |
| 2 | `"1234"` | 4 | 4 | 2 |
| 3 | 64-char (`a-z A-Z 0-9 + *`) | 64 | 4 | 2 |
| 4 | 64-char | 64 | 6 | 3 |
| 5 | 64-char | 64 | 8 | 2 |

The password length is always a multiple of the block size, so **no padding is ever needed or added**.

### Cipher Mathematics

**Caesar** — shift modulo m:
```
Encrypt: C = (P + k) mod m
Decrypt: P = (C - k) mod m
Key k: integer in [1, m-1]
```

**Hill** — matrix multiplication modulo m (block size n):
```
Encrypt: C = K · P  mod m   (per block of n indices)
Decrypt: P = K⁻¹ · C  mod m
Key K: n×n matrix with gcd(det K, m) = 1  (for m=2,4,64: det K must be odd)
K must not be the identity matrix.
```
For n=2: `adj([[a,b],[c,d]]) = [[d,-b],[-c,a]]`.
For n=3: adjugate computed via cofactors.
K⁻¹ = pow(det, -1, m) * adj(K)  mod m.

### Protection Record Format
The protected record is a dictionary that **strictly never contains the key**:
```python
{
    "use_case": int,           # 1 to 5
    "cipher": str,             # "hill" or "caesar"
    "ciphertext": str,         # Encrypted password string (same length as plaintext)
    "params": {
        "modulus": int,        # Alphabet size m (non-secret)
        "block": int           # Hill block size n, or 1 for Caesar (non-secret)
    }
}
```

### Encryption & Verification Flow
1. **Protection (`protect(password, use_case, cipher, key) -> record`)**:
   - Validates `password` against the use-case length and alphabet.
   - Parses the key strictly via `cipher_adapter.parse_key(key, use_case, cipher)`.
   - Encrypts the password using `cipher_adapter.encrypt(text, parsed_key, use_case, cipher)`.
   - Returns the record dictionary without the key.
2. **Verification (`make_checker(record, key) -> check(candidate) -> bool`)**:
   - Parses and closes over the key — the key never leaves the closure.
   - `check(candidate)` encrypts the candidate and compares the ciphertext with `record["ciphertext"]`.
   - Wrong key → wrong ciphertext → `False`.
3. **Lockout Mechanism (`Lockout`)**:
   - Parameters: `MAX_FAILURES = 5`, `LOCK_SECONDS = 30`.
   - Injectable clock for deterministic testing.
   - After 5 consecutive failures, raises `ValueError("Locked. Try again in N s.")` until the window expires.
   - A successful login resets the failure counter to 0.

### Cipher Adapter (`passwords/cipher_adapter.py`)
The **only** file that knows the password-section ciphers. Public API:
- `encrypt(text, key, use_case, cipher)` → ciphertext string
- `decrypt(text, key, use_case, cipher)` → plaintext string
- `parse_key(raw, use_case, cipher)` → validated int (Caesar) or list[list[int]] (Hill)
- `block_size(use_case)` → default Hill block size n
- `get_alphabet(use_case)` → alphabet string
- `USE_CASE_CIPHER` — default cipher per use case (Hill for all)
- Does **not** import from `crypto/`; implements Hill and Caesar from scratch over use-case alphabets.

---

## 4. Part 4: Data Authenticity & Integrity (`integrity/`)

All hashing and integrity mechanisms are isolated in `integrity/` to be managed independently:
- **`integrity.hashing.hash_fast(password) -> str`**:
  Calculates raw SHA-256 hexadecimal digests.
- **`integrity.hashing.generate_salt(num_bytes=16) -> bytes`**:
  Generates cryptographically random salt bytes via `os.urandom`.
- **`integrity.hashing.hash_protected(password, iterations=100_000, salt=None) -> dict`**:
  Derives a stretched hash using PBKDF2-HMAC-SHA256, returning salt, iteration count, and digest.
- **`integrity.hashing.compare_hashes(a, b) -> bool`**:
  Performs constant-time digest comparison using `hmac.compare_digest`.
- **`integrity.hashing.verify_protected(password, record) -> bool`**:
  Verifies candidate input against a stored PBKDF2 record in constant time.
- **`integrity.hashing.estimate_slowdown(attempts, rate, factor=1.0) -> float`**:
  Models cracking duration using the slowdown formula $t = k \cdot \text{attempts} / v$.

`integrity/` relies solely on Python standard library modules (`hashlib`, `hmac`, `os`) and **never imports from `passwords/` or `gui/`**.

---

## 5. Graphical User Interface (GUI)

### Separate Windows for Encryption and Decryption (Security Layer)
To ensure authenticity and security between communicating parties:
1. **Entity A — Encryption Window (`gui/pages/encryption_page.py`)**:
   - Sender selects algorithm (`Caesar`, `Playfair`, `Hill`), configures the key, enters plaintext, and clicks **Encrypt**.
   - Clicking **"Send to Decryption Window (Entity B)"** transmits **ONLY the ciphertext** (and optional non-secret padding length for Hill).
   - **Crucially, neither the algorithm choice nor the secret key is transmitted or revealed.**
   - Includes a button to pop open the Decryption window into an independent OS window.

2. **Entity B — Decryption Window (`gui/pages/decryption_page.py`)**:
   - Functions as an independent sidebar tab **and** can be popped out into a standalone floating window (`DecryptionToplevel`).
   - Receives incoming ciphertext from Entity A without knowing which algorithm or key was used.
   - **Recipient Authentication Mechanism**: The person operating the Decryption window **must independently select the algorithm from a dropdown menu and type the secret key by hand**.
   - If the operator selects the wrong algorithm or enters an incorrect key, decryption fails or outputs garbled text, proving that unauthorized operators cannot read the message.
   - Successful decryption confirms the recipient's identity and shared knowledge.

3. **Other GUI Pages**:
   - **`gui/pages/passwords_page.py`**: Password protection via cipher encryption with hand-typed keys and lockout enforcement.
   - **`gui/pages/attacks_page.py`**: Cryptanalysis workbench for evaluating brute-force and dictionary attacks.

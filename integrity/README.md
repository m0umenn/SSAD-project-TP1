# Integrity Package (`integrity/`)

Part 4 of the SSAD Toolkit implements data integrity, hashing, and verification.
This package is self-contained: it uses **Python standard library only** (`hashlib`, `hmac`, `os`) and **never imports from `passwords/` or `gui/`**.

---

## Constants

- `ITERATIONS: int = 100_000`  
  Default iteration count for PBKDF2-HMAC-SHA256 stretching.
- `SALT_BYTES: int = 16`  
  Default number of cryptographically secure random bytes generated for salt (128 bits).

---

## Public Functions (`integrity.hashing`)

### 1. `hash_fast(password: str) -> str`
- **Inputs**:
  - `password` (`str`): The plaintext string to hash.
- **Output**:
  - `str`: 64-character lowercase hexadecimal SHA-256 digest.
- **Exceptions**:
  - Raises `ValueError` if `password` is not a `str`.
- **Description**: Fast, un-salted SHA-256 hash. Useful for baseline speed measurements and integrity checks.
- **Example**:
  ```python
  from integrity.hashing import hash_fast
  digest = hash_fast("abc")
  # "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
  ```

---

### 2. `generate_salt(num_bytes: int = SALT_BYTES) -> bytes`
- **Inputs**:
  - `num_bytes` (`int`, optional): Number of bytes (defaults to 16).
- **Output**:
  - `bytes`: Cryptographically random bytes generated via `os.urandom`.
- **Exceptions**:
  - Raises `ValueError` if `num_bytes` is not a positive integer.
- **Example**:
  ```python
  from integrity.hashing import generate_salt
  salt = generate_salt(16)
  ```

---

### 3. `hash_protected(password: str, iterations: int = 100_000, salt: bytes | None = None) -> dict[str, str | int]`
- **Inputs**:
  - `password` (`str`): The plaintext string to hash.
  - `iterations` (`int`, optional): Number of PBKDF2 iterations (default: 100,000).
  - `salt` (`bytes | None`, optional): Explicit salt bytes; if `None`, a random 16-byte salt is generated.
- **Output**:
  - `dict[str, str | int]`: A dictionary with:
    - `"salt"` (`str`): Hex-encoded salt.
    - `"iterations"` (`int`): Iteration count used.
    - `"hash"` (`str`): 64-character lowercase hex digest derived with PBKDF2-HMAC-SHA256.
- **Exceptions**:
  - Raises `ValueError` if `password` is not a string, `iterations` is non-positive or boolean, or `salt` is invalid.
- **Example**:
  ```python
  from integrity.hashing import hash_protected
  record = hash_protected("secret", iterations=1000)
  # {"salt": "...", "iterations": 1000, "hash": "..."}
  ```

---

### 4. `parse_record(record: Any) -> tuple[bytes, int, str]`
- **Inputs**:
  - `record` (`Any`): Expected `dict` containing `"salt"`, `"iterations"`, and `"hash"`.
- **Output**:
  - `tuple[bytes, int, str]`: Validated `(salt_bytes, iterations, hash_hex)`.
- **Exceptions**:
  - Raises `ValueError` ("Malformed record.") if structure, types, lengths, or hex encoding are invalid.
- **Example**:
  ```python
  from integrity.hashing import parse_record
  salt_bytes, iters, digest = parse_record(record)
  ```

---

### 5. `compare_hashes(a: str, b: str) -> bool`
- **Inputs**:
  - `a` (`str`): First hash string.
  - `b` (`str`): Second hash string.
- **Output**:
  - `bool`: `True` if strings are identical, `False` otherwise.
- **Description**: Uses `hmac.compare_digest` to perform constant-time comparison, mitigating timing attacks.
- **Example**:
  ```python
  from integrity.hashing import compare_hashes
  match = compare_hashes(derived_hash, stored_hash)
  ```

---

### 6. `verify_protected(password: str, record: dict[str, Any]) -> bool`
- **Inputs**:
  - `password` (`str`): The candidate plaintext to verify.
  - `record` (`dict[str, Any]`): The record produced by `hash_protected`.
- **Output**:
  - `bool`: `True` if `password` matches the hash in `record`, `False` otherwise.
- **Exceptions**:
  - Raises `ValueError` if `password` is not a string or `record` is malformed.
- **Example**:
  ```python
  from integrity.hashing import verify_protected
  if verify_protected("secret", record):
      print("Authentication succeeded")
  ```

---

### 7. `estimate_slowdown(attempts: int, rate: float, factor: float = 1.0) -> float`
- **Inputs**:
  - `attempts` (`int`): Total number of attempts / search space size.
  - `rate` (`float`): Rate $v$ (hash computations per second).
  - `factor` (`float`, optional): Slowdown constant $k$ (defaults to 1.0).
- **Output**:
  - `float`: Estimated duration $t = k \cdot \text{attempts} / v$ in seconds (`float("inf")` if `rate <= 0`).
- **Example**:
  ```python
  from integrity.hashing import estimate_slowdown
  est_seconds = estimate_slowdown(1_000_000, rate=50_000)
  ```

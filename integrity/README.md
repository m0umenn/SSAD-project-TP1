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

---

## Message, file and HMAC helpers (`integrity.integrity`)

These functions are exported by the package: `from integrity import hash_data, ...`.
All of them raise `ValueError` on invalid input (they never return `None`).
A digest or tag is always **64 lowercase hexadecimal characters**; uppercase hex
is accepted when *verifying*.

### 8. `hash_data(data: str) -> str`
- **Output**: SHA-256 digest of the text (UTF-8).
- **Exceptions**: `ValueError` if `data` is not a `str`.
- **Example**:
  ```python
  hash_data("abc")  # "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
  ```

### 9. `verify_data(data: str, digest: str) -> bool`
- **Output**: `True` if the text still matches the digest (message intact), `False` if it was modified.
- **Exceptions**: `ValueError` if `data` is not a `str` or `digest` is not 64 hex characters.
- **Description**: constant-time comparison (`compare_hashes`).

### 10. `hash_file(path, chunk_size: int = 65536) -> str`
- **Inputs**: `path` (`str` or `pathlib.Path`), `chunk_size` (positive `int`, bytes read at a time).
- **Output**: SHA-256 digest of the file. The file is read in chunks, so large files are fine.
- **Exceptions**: `ValueError` if `path` is not a path, `chunk_size` is invalid, or the file cannot be read (missing, a folder, no permission).
- **Example**:
  ```python
  from pathlib import Path
  hash_file(Path("report.pdf"))
  ```

### 11. `verify_digest(data_or_path, expected_hex: str, is_path: bool | None = None) -> bool`
- **Inputs**:
  - `data_or_path`: a `pathlib.Path` (file), a `str` (text) or `bytes`.
  - `expected_hex`: the expected SHA-256 digest (64 hex characters).
  - `is_path`: set to `True` to treat a `str` as a **file path** (for example a path chosen in a file dialog). By default a `str` is text, so a message is never mistaken for a file name.
- **Output**: `True` if the digest matches, `False` otherwise (constant-time comparison).
- **Exceptions**: `ValueError` for a malformed digest, an unsupported input type, or an unreadable file.
- **Examples**:
  ```python
  verify_digest("abc", digest)                      # text
  verify_digest(b"abc", digest)                     # bytes
  verify_digest(Path("report.pdf"), digest)         # file
  verify_digest("C:/docs/report.pdf", digest, is_path=True)  # file path given as str
  ```

### 12. `hmac_sha256(key: str | bytes, message: str | bytes) -> str`
- **Output**: HMAC-SHA-256 tag (64 hex characters). `str` inputs are encoded as UTF-8.
- **Exceptions**: `ValueError` if `key` or `message` is not `str`/`bytes`, or if `key` is empty.
- **Description**: authenticity. Only someone who knows the shared key can produce a valid tag, so an attacker who edits the message cannot fix the tag (unlike a plain SHA-256 digest, which anyone can recompute).
- **Example**:
  ```python
  hmac_sha256("Jefe", "what do ya want for nothing?")
  # "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"  (RFC 4231)
  ```

### 13. `verify_hmac(key: str | bytes, message: str | bytes, tag: str) -> bool`
- **Output**: `True` if the tag is valid for this key and message; `False` if the message was modified or the key is wrong.
- **Exceptions**: `ValueError` if `tag` is not 64 hex characters or `key`/`message` is invalid.
- **Description**: constant-time comparison (`compare_hashes`).

### Which function for which job (GUI)
| Job | Function |
| --- | --- |
| Hash a text | `hash_data(text)` |
| Hash a file | `hash_file(path)` |
| Check a text / file against a digest | `verify_digest(text_or_path, digest)` (or `verify_data` for text only) |
| Compute an HMAC tag | `hmac_sha256(key, message)` |
| Check an HMAC tag | `verify_hmac(key, message, tag)` |
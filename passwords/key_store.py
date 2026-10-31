"""Secure persistent key storage for password protection ciphers.

Keys are generated once per (cipher, use_case) pair using cryptographically
secure randomness (the `secrets` module) and kept in a local JSON file.
The keys are never exposed in user records, logs, or error messages.
"""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from typing import Any

from passwords import cipher_adapter

_DEFAULT_FILE_NAME = os.path.join("data", "secret_keys.json")
_custom_key_file: str | None = None


def set_key_file(path: str | None) -> None:
    """Override the key file path for the current process (e.g. for testing)."""
    global _custom_key_file
    _custom_key_file = path


def get_key_file() -> str:
    """Return the active key file path."""
    if _custom_key_file is not None:
        return _custom_key_file
    env_path = os.environ.get("SSAD_KEY_FILE")
    if env_path:
        return env_path
    return _DEFAULT_FILE_NAME


def _normalize_cipher(cipher: str | None) -> str:
    if cipher is None or str(cipher).strip() == "":
        return "hill"
    c = str(cipher).lower().strip()
    if c not in ("caesar", "hill"):
        raise ValueError(f"Unsupported cipher for key store: {cipher!r}")
    return c


def _validate_all_entries(data: dict[str, Any]) -> None:
    """Ensure all entries in the parsed JSON conform to expected key structures."""
    for key_id, raw_key in data.items():
        if not isinstance(key_id, str) or ":" not in key_id:
            raise ValueError("Key file is corrupted")
        cipher_name, uc_str = key_id.split(":", 1)
        cipher_name = cipher_name.lower().strip()
        if cipher_name not in ("caesar", "hill"):
            raise ValueError("Key file is corrupted")
        try:
            uc = int(uc_str)
            # Validate through existing cipher_adapter validation
            cipher_adapter.parse_key(raw_key, uc, cipher_name)
        except Exception:
            raise ValueError("Key file is corrupted")


def _generate_key(use_case: int, cipher: str) -> Any:
    """Generate a valid secret key using secrets module and cipher_adapter validation."""
    alphabet = cipher_adapter.get_alphabet(use_case)
    m = len(alphabet)

    if cipher == "caesar":
        if m < 2:
            raise ValueError("Alphabet size must be at least 2 for Caesar.")
        # Key must be an integer in [1, m-1]
        k = secrets.randbelow(m - 1) + 1
        return cipher_adapter.parse_key(k, use_case, "caesar")

    if cipher == "hill":
        n = cipher_adapter.block_size(use_case)
        while True:
            candidate = [[secrets.randbelow(m) for _ in range(n)] for _ in range(n)]
            try:
                # Validates dimensions, entry bounds, non-identity, and invertibility mod m
                valid_mat = cipher_adapter.parse_key(candidate, use_case, "hill")
                return valid_mat
            except ValueError:
                continue

    raise ValueError(f"Unknown cipher: {cipher}")


def _atomic_save(path: str, data: dict[str, Any]) -> None:
    """Save dictionary to path atomically with best-effort restricted permissions."""
    abs_path = os.path.abspath(path)
    parent_dir = os.path.dirname(abs_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=parent_dir, prefix="keys_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        try:
            os.chmod(tmp_path, 0o600)
        except Exception:
            pass
        os.replace(tmp_path, abs_path)
        try:
            os.chmod(abs_path, 0o600)
        except Exception:
            pass
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def get_key(use_case: int, cipher: str | None = None) -> Any:
    """Retrieve or generate the secret key for (cipher, use_case).

    If the key store file is missing, it is created.
    If the requested key entry is missing, a new valid key is generated and saved.
    If the file exists but is corrupted, a ValueError is raised and the file is untouched.
    """
    if isinstance(use_case, bool) or not isinstance(use_case, int):
        raise ValueError("Unknown use case.")
    cipher_name = _normalize_cipher(cipher)
    key_id = f"{cipher_name}:{use_case}"
    path = get_key_file()

    data: dict[str, Any] = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            loaded = json.loads(content)
            if not isinstance(loaded, dict):
                raise ValueError("Key file is corrupted")
            _validate_all_entries(loaded)
            data = loaded
        except json.JSONDecodeError as exc:
            raise ValueError("Key file is corrupted") from exc
        except ValueError:
            raise

    if key_id in data:
        return data[key_id]

    new_key = _generate_key(use_case, cipher_name)
    data[key_id] = new_key
    _atomic_save(path, data)
    return new_key


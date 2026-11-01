"""Data integrity and authenticity helpers (Part 4).

Integrity: the receiver B can check that what it received is exactly what the
sender A produced. A sends a SHA-256 digest together with the message (or file);
B recomputes the digest and compares both values in constant time. Any change,
even of one character or one byte, gives a completely different digest.

Authenticity: HMAC-SHA-256 mixes a secret key shared by A and B into the hash.
Without the key, an attacker who modifies a message cannot compute the matching
tag, so B detects the change and knows the message comes from someone who holds
the key. A plain digest cannot do that: the attacker can recompute it.

Standard library only (hashlib, hmac, os); builds on integrity.hashing.
Owner: <name>
"""

from __future__ import annotations

import hashlib
import hmac
import os

from integrity.hashing import compare_hashes, hash_fast

DIGEST_HEX_LENGTH = 64  # SHA-256 = 256 bits = 64 hexadecimal characters
CHUNK_SIZE = 64 * 1024  # bytes read at a time when hashing a file
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


# ------------------------------------------------------------------ helpers

def _check_hex(value: object, name: str) -> str:
    """Return `value` in lower case if it is a 64-character hex string."""
    if not isinstance(value, str) or len(value) != DIGEST_HEX_LENGTH:
        raise ValueError(f"{name} must be {DIGEST_HEX_LENGTH} hexadecimal characters.")
    if not set(value) <= _HEX_DIGITS:
        raise ValueError(f"{name} must be hexadecimal.")
    return value.lower()


def _to_bytes(value: object, name: str) -> bytes:
    """Encode a str as UTF-8 or accept bytes; reject anything else."""
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    raise ValueError(f"{name} must be a string or bytes.")


# ------------------------------------------------------- digest of a message

def hash_data(data: str) -> str:
    """Create the SHA-256 digest (64 hex characters) of the text `data`.

    Raises:
        ValueError: If `data` is not a string.
    """
    if not isinstance(data, str):
        raise ValueError("Data must be a string.")
    return hash_fast(data)


def verify_data(data: str, digest: str) -> bool:
    """Check that the text `data` still matches the digest computed by the sender.

    Returns:
        bool: True if the message is intact, False if it was modified.

    Raises:
        ValueError: If `data` is not a string or `digest` is not a valid
            64-character hexadecimal string.
    """
    if not isinstance(data, str):
        raise ValueError("Data must be a string.")
    expected = _check_hex(digest, "Digest")
    return compare_hashes(hash_data(data), expected)


# --------------------------------------------------------- digest of a file

def hash_file(path: str | os.PathLike, chunk_size: int = CHUNK_SIZE) -> str:
    """Return the SHA-256 digest (64 hex characters) of a file.

    The file is read in chunks of `chunk_size` bytes, so a large file never has
    to fit in memory.

    Raises:
        ValueError: If `path` is not a path, `chunk_size` is not a positive
            integer, or the file cannot be read (missing, a folder, no access).
    """
    if not isinstance(path, (str, os.PathLike)):
        raise ValueError("Path must be a string or a path object.")
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise ValueError(f"Cannot read file: {exc.strerror or exc}") from None
    return digest.hexdigest()


def verify_digest(data_or_path, expected_hex: str, is_path: bool | None = None) -> bool:
    """Check text, bytes or a file against an expected SHA-256 digest.

    How `data_or_path` is interpreted:
        - a path object (pathlib.Path, os.PathLike)  -> the file is hashed;
        - a str or bytes                             -> the content itself is hashed;
        - a str with is_path=True                    -> the str is a file path.
    A str is treated as text by default so that a message is never mistaken for
    a file name.

    Returns:
        bool: True if the digest matches, False otherwise.

    Raises:
        ValueError: If `expected_hex` is not 64 hexadecimal characters, the
            input has an unsupported type, or the file cannot be read.
    """
    expected = _check_hex(expected_hex, "Digest")
    if is_path is not None and not isinstance(is_path, bool):
        raise ValueError("is_path must be True, False or None.")
    if is_path is None:
        is_path = isinstance(data_or_path, os.PathLike)

    if is_path:
        actual = hash_file(data_or_path)
    elif isinstance(data_or_path, str):
        actual = hash_data(data_or_path)
    elif isinstance(data_or_path, (bytes, bytearray)):
        actual = hashlib.sha256(bytes(data_or_path)).hexdigest()
    else:
        raise ValueError("Data must be a string or bytes (or a path object for a file).")
    return compare_hashes(actual, expected)


# ------------------------------------------------------------- authenticity

def hmac_sha256(key: str | bytes, message: str | bytes) -> str:
    """Return the HMAC-SHA-256 tag (64 hex characters) of `message` under `key`.

    `str` inputs are encoded as UTF-8.

    Raises:
        ValueError: If `key` or `message` is not a str/bytes, or `key` is empty.
    """
    key_bytes = _to_bytes(key, "Key")
    if not key_bytes:
        raise ValueError("Key must not be empty.")
    message_bytes = _to_bytes(message, "Message")
    return hmac.new(key_bytes, message_bytes, hashlib.sha256).hexdigest()


def verify_hmac(key: str | bytes, message: str | bytes, tag: str) -> bool:
    """Check an HMAC-SHA-256 tag in constant time.

    Returns:
        bool: True if the tag is valid for this key and message, False if the
            message was modified or the key is wrong.

    Raises:
        ValueError: If `tag` is not 64 hexadecimal characters, or `key` /
            `message` is invalid (see hmac_sha256).
    """
    expected = _check_hex(tag, "Tag")
    return compare_hashes(hmac_sha256(key, message), expected)
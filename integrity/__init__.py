"""Authenticity, hashing, and integrity verification package for SSAD Toolkit (Part 4)."""

from __future__ import annotations

from integrity.hashing import (
    ITERATIONS,
    SALT_BYTES,
    compare_hashes,
    estimate_slowdown,
    generate_salt,
    hash_fast,
    hash_protected,
    parse_record,
    verify_protected,
)

__all__ = [
    "ITERATIONS",
    "SALT_BYTES",
    "compare_hashes",
    "estimate_slowdown",
    "generate_salt",
    "hash_fast",
    "hash_protected",
    "parse_record",
    "verify_protected",
]
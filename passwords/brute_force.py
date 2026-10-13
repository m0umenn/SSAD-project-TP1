"""Brute-force password attack stub.

This module will later simulate a brute-force search for a target password.
Owner: <name>
"""

from __future__ import annotations


def brute_force(target: str, charset: str, max_len: int) -> tuple[bool, int, float]:
    """Try all combinations up to a given length.

    Returns:
        tuple[bool, int, float]: (found, attempts, seconds)
    """

    raise NotImplementedError("Brute-force attack is not implemented yet.")
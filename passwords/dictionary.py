"""Dictionary attack stub.

This module will later try a list of candidate words against a target password.
Owner: <name>
"""

from __future__ import annotations


def dictionary_attack(target: str, wordlist) -> tuple[bool, int, float]:
    """Try candidate words from a word list.

    Returns:
        tuple[bool, int, float]: (found, attempts, seconds)
    """

    raise NotImplementedError("Dictionary attack is not implemented yet.")
"""Brute-force attack: try every candidate password until the target matches.

The target can be either:
  - a fast hash (str)      : quick to check, e.g. generators.hash_fast(password)
  - a protected record (dict) : slow to check on purpose, from protection.hash_protected

protection.make_checker(target) builds a check(candidate) -> bool callable for
either kind, so this module does not need to know which one it is attacking.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from passwords.generators import USE_CASES, candidates
from passwords.protection import make_checker


def force_brute(
    use_case: int, check: Callable[[str], bool]
) -> tuple[str | None, int]:
    """Try every password of `use_case` against `check` until it returns True.

    Returns (password_found, number_of_attempts). password_found is None only
    if no candidate in the search space satisfies `check` (should not happen
    if the target was produced from a password that is valid for this use case).
    """
    if use_case not in USE_CASES:
        raise ValueError("Unknown use case.")

    spec = USE_CASES[use_case]
    attempts = 0
    for candidate in candidates(str(spec["alphabet"]), int(spec["length"])):
        attempts += 1
        if check(candidate):
            return candidate, attempts
    return None, attempts


def force_brute_target(
    use_case: int, target: str | dict[str, str | int]
) -> tuple[str | None, int, float]:
    """Convenience wrapper: build the checker from `target`, run the attack, and time it.

    `target` is either a fast hash string or a protected record dict.
    Returns (password_found, attempts, elapsed_seconds).
    """
    check = make_checker(target)
    start = time.perf_counter()
    found, attempts = force_brute(use_case, check)
    elapsed = time.perf_counter() - start
    return found, attempts, elapsed


def _demo(use_case: int, password: str) -> None:
    """Small command-line demo: hash a password then brute-force it back."""
    from passwords.generators import hash_fast

    target = hash_fast(password)
    spec = USE_CASES[use_case]
    total = len(str(spec["alphabet"])) ** int(spec["length"])

    print(f"\n--- Use case {use_case} ({total} possible passwords) ---")
    print(f"Real password: {password}")
    print(f"Stolen fast hash: {target}")

    found, attempts, elapsed = force_brute_target(use_case, target)

    print(f"Password recovered: {found}")
    print(f"Attempts: {attempts}")
    print(f"Elapsed: {elapsed * 1000:.3f} ms")


if __name__ == "__main__":
    print("Brute-force demo - use cases 1 and 2")
    _demo(1, "101")
    _demo(2, "4321")
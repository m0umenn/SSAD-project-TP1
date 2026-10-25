"""Dictionary attack: try only a short list of likely passwords, not the full space.

Unlike brute_force.py, which tries every possible password, this only tries
words a human might realistically pick. It is much faster, but only succeeds
if the real password happens to be in the list.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from passwords.generators import USE_CASES
from passwords.protection import make_checker

# A short list of common/predictable passwords per use case, matching each
# use case's alphabet and length so every word is actually a valid candidate.
COMMON_PASSWORDS: dict[int, list[str]] = {
    1: ["000", "111", "010", "101", "001", "100", "011", "110"],
    2: ["1234", "4321", "1111", "2222", "3333", "4444", "1212", "2121", "1122", "4411"],
    3: ["pass", "4321","Pass", "1234", "0000", "abcd", "P4ss", "A1b2", "qwer"],
    4: ["123456", "qwerty", "abcdef", "Passw0", "P4ssw0", "000000", "111111", "aaaaaa"],
    5: [
        "password", "12345678", "qwertyui", "Passw0rd", "P4ssw0rd",
        "letmein1", "iloveyou", "Pass+123",
    ],
}


def dictionary_attack(use_case: int, check: Callable[[str], bool]) -> tuple[str | None, int]:
    """Try each word of the built-in list for `use_case` against `check`.

    Words that do not match the use case's alphabet/length are skipped
    (they are not valid candidates, so they would never match anyway).

    Returns (password_found, number_of_attempts). password_found is None if
    no word in the list matched.
    """
    if use_case not in USE_CASES:
        raise ValueError("Unknown use case.")

    spec = USE_CASES[use_case]
    alphabet = str(spec["alphabet"])
    length = int(spec["length"])
    words = COMMON_PASSWORDS.get(use_case, [])

    attempts = 0
    for word in words:
        if len(word) != length or any(char not in alphabet for char in word):
            continue
        attempts += 1
        if check(word):
            return word, attempts
    return None, attempts


def dictionary_attack_target(
    use_case: int, target: str | dict[str, str | int]
) -> tuple[str | None, int, float]:
    """Convenience wrapper: build the checker from `target`, run the attack, and time it.

    Returns (password_found, attempts, elapsed_seconds).
    """
    check = make_checker(target)
    start = time.perf_counter()
    found, attempts = dictionary_attack(use_case, check)
    elapsed = time.perf_counter() - start
    return found, attempts, elapsed


def _demo(use_case: int, password: str) -> None:
    """Small command-line demo: hash a password then attack it with the dictionary."""
    from passwords.generators import hash_fast

    target = hash_fast(password)
    print(f"\n--- Use case {use_case} ---")
    print(f"Real password: {password}")
    print(f"Stolen fast hash: {target}")

    found, attempts, elapsed = dictionary_attack_target(use_case, target)

    result = found if found else "FAILED (password not in the dictionary)"
    print(f"Result: {result}")
    print(f"Attempts: {attempts}")
    print(f"Elapsed: {elapsed * 1000:.3f} ms")


if __name__ == "__main__":
    print("Dictionary attack demo")
    _demo(1, "101")    # in the dictionary
    _demo(2, "1234")   # in the dictionary
    _demo(2, "3142")   # NOT in the dictionary -> fails
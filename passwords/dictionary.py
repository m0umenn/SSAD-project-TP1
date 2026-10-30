"""Dictionary attack: try only a short list of likely passwords, not the full space.

Unlike brute_force.py, which tries every possible password, this only tries
words a human might realistically pick. It is much faster, but only succeeds
if the real password happens to be in the list.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from passwords.generators import USE_CASES
from passwords.protection import make_checker

# A list of common/predictable passwords per use case, matching each use
# case's alphabet and length so every word is actually a valid candidate.
COMMON_PASSWORDS: dict[int, list[str]] = {
    # Use case 1: 3 characters from "01" -> only 8 possible passwords exist,
    # so this list is the entire search space.
    1: ["000", "001", "010", "011", "100", "101", "110", "111"],

    # Use case 2: 4 characters from "1234" (256 possible passwords).
    2: [
        # repeated digits
        "1111", "2222", "3333", "4444",
        # ascending / descending runs
        "1234", "4321", "1231", "1324", "2143", "4123", "3412", "2341",
        # simple pairs
        "1212", "2121", "1313", "3131", "1414", "4141",
        "2323", "3232", "2424", "4242", "3434", "4343",
        # palindromes
        "1221", "2112", "1331", "3113", "1441", "4114",
        "2332", "3223", "2442", "4224", "3443", "4334",
        # doubled digits
        "1122", "2211", "1133", "3311", "1144", "4411",
        "2233", "3322", "2244", "4422", "3344", "4433",
    ],

    # Use case 3: 4 characters from the full alphabet (letters, digits, +, *).
    3: [
        "pass", "Pass", "PASS", "abcd", "ABCD", "Abcd",
        "1234", "4321", "0000", "1111", "2222",
        "qwer", "Qwer", "asdf", "Asdf", "zxcv", "Zxcv",
        "Aa11", "Bb22", "P4ss", "A1b2", "Ab12", "1Ab2",
        "root", "user", "test", "Test", "demo", "Demo",
        "Xx11", "+123", "12*4",
    ],

    # Use case 4: 6 characters from the full alphabet.
    4: [
        "123456", "654321", "111111", "121212", "000000",
        "qwerty", "QWERTY", "asdfgh", "zxcvbn", "qazwsx",
        "abc123", "123abc", "abcdef", "ABCDEF",
        "monkey", "dragon", "shadow", "master", "letmei",
        "iloveu", "freedo", "superm", "ninja1", "admin1",
        "passwd", "Passw0", "P4ssw0", "root12", "test12",
    ],

    # Use case 5: 8 characters from the full alphabet.
    5: [
        "password", "PASSWORD", "Password", "12345678", "87654321",
        "qwertyui", "QWERTYUI", "asdfghjk", "zxcvbnm1", "1qaz2wsx",
        "iloveyou", "princess", "football", "baseball", "sunshine",
        "superman", "trustno1", "letmein1", "welcome1", "starwars",
        "whatever", "computer", "dragon12", "monkey12", "master12",
        "shadow12", "batman12", "ginger12", "summer12", "winter12",
        "Passw0rd", "P4ssw0rd", "Pass+123", "Pass*123", "admin123",
        "root1234", "test1234", "11111111", "00000000", "12121212",
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
    use_case: int, target: dict[str, Any], key: Any = 0
) -> tuple[str | None, int, float]:
    """Convenience wrapper: build the checker from `target`, run the attack, and time it.

    `target` is an encrypted record dict.
    Returns (password_found, attempts, elapsed_seconds).
    """
    check = make_checker(target, key)
    start = time.perf_counter()
    found, attempts = dictionary_attack(use_case, check)
    elapsed = time.perf_counter() - start
    return found, attempts, elapsed


def _demo(use_case: int, password: str, key: int = 3) -> None:
    """Small command-line demo: encrypt a password then attack it with the dictionary."""
    from passwords.protection import protect

    record = protect(password, use_case, key=key)
    print(f"\n--- Use case {use_case} ---")
    print(f"Real password: {password}")
    print(f"Protected record: {record}")

    found, attempts, elapsed = dictionary_attack_target(use_case, record, key=key)

    result = found if found else "FAILED (password not in the dictionary)"
    print(f"Result: {result}")
    print(f"Attempts: {attempts}")
    print(f"Elapsed: {elapsed * 1000:.3f} ms")


if __name__ == "__main__":
    print("Dictionary attack demo")
    _demo(1, "101")    # in the dictionary
    _demo(2, "1234")   # in the dictionary
    _demo(2, "3142")   # NOT in the dictionary -> fails
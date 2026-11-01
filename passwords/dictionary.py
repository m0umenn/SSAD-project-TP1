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
    # Use case 1:
    1: ["000", "001", "010", "011", "100", "101", "110", "111"],

    # Use case 2: 4 characters from "1234" (256 possible passwords).
    2: [
        "1111", "2222", "3333", "4444", "1112", "1113", "1114", "1121",
        "1122", "1131", "1133", "1141", "1144", "1211", "1212", "1221",
        "1222", "1311", "1313", "1331", "1333", "1411", "1414", "1441",
        "1444", "2111", "2112", "2121", "2122", "2211", "2212", "2221",
        "2223", "2224", "2232", "2233", "2242", "2244", "2322", "2323",
        "2332", "2333", "2422", "2424", "2442", "2444", "3111", "3113",
        "3131", "3133", "3222", "3223", "3232", "3233", "3311", "3313",
        "3322", "3323", "3331", "3332", "3334", "3343", "3344", "3433",
        "3434", "3443", "3444", "4111", "4114", "4141", "4144", "4222",
        "4224", "4242", "4244", "4333", "4334", "4343", "4344", "4411",
        "4414", "4422", "4424", "4433", "4434", "4441", "4442", "4443",
        "1123", "1124", "1132", "1134", "1142", "1143", "1213", "1214",
        "1223", "1224", "1231", "1232", "1233", "1241", "1242", "1244",
        "1312", "1314", "1321", "1322", "1323", "1332", "1334", "1341",
        "1343", "1344", "1412", "1413", "1421", "1422", "1424", "1431",
    ],

    # Use case 3: 4 characters from the full alphabet (letters, digits, +, *).
     3: [
        "0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777",
        "8888", "9999", "1234", "4321", "1212", "2121", "1122", "1004",
        "2000", "1999", "2024", "2025", "pass", "Pass", "PASS", "qwer",
        "Qwer", "QWER", "asdf", "Asdf", "zxcv", "Zxcv", "abcd", "ABCD",
        "Abcd", "root", "user", "test", "Test", "demo", "Demo", "User",
        "Love", "love", "Life", "life", "Cool", "cool", "Evil", "evil",
        "Ace1", "best", "Ryan", "Jake", "Alex", "Kyle", "Mike", "John",
        "Jack", "Sean", "Adam", "Noah", "toto", "dodo", "nana", "titi",
        "zaza", "lolo", "fifi", "gaga", "mama", "papa", "coco", "bebe",
        "chat", "miam", "doux", "nono", "zozo", "rere", "mumu", "aime",
        "roii", "amis", "bise", "fete", "noel", "sudd", "tata", "yoyo",
        "momo", "jojo", "Aa11", "Bb22", "Cc33", "P4ss", "A1b2", "Ab12",
        "1Ab2", "Xx11", "+123", "12*4", "a1+*", "*123", "Az1*", "1a2b",
    ],

    # Use case 4: 6 characters from the full alphabet.
    4: [
        "123456", "654321", "111111", "121212", "000000", "222222", "333333", "666666",
        "qwerty", "QWERTY", "asdfgh", "zxcvbn", "qazwsx", "azerty", "AZERTY", "1qaz2w",
        "abc123", "123abc", "abcdef", "ABCDEF", "a1b2c3", "1a2b3c", "monkey", "dragon",
        "shadow", "master", "letme1", "iloveu", "freedo", "superm", "ninja1", "admin1",
        "passwd", "Passw0", "P4ssw0", "root12", "test12", "soccer", "hockey", "batman",
        "ginger", "orange", "purple", "yellow", "silver", "golfer", "hunter", "killer",
        "buster", "cookie", "jordan", "daniel", "amanda", "maggie", "sophie", "robert",
        "thomas", "andrea", "iphone", "forest", "flower", "summer", "winter", "autumn",
        "spring", "forev1", "qwert1", "soleil", "amour1", "bisous", "chaton", "copain",
        "copine", "maison", "doudou", "coucou", "secret", "voitur", "jardin", "cuisin",
        "ecolie", "poulet", "lapin1", "tigre1", "canard", "poisso", "famill", "potato",
        "banana",
    ],

    # Use case 5: 8 characters from the full alphabet.
    5: [
        "password", "PASSWORD", "Password", "12345678", "87654321", "qwertyui", "QWERTYUI", "asdfghjk",
        "zxcvbnm1", "1qaz2wsx", "iloveyou", "princess", "football", "baseball", "sunshine", "superman",
        "trustno1", "letmein1", "welcome1", "starwars", "whatever", "computer", "dragon12", "monkey12",
        "master12", "shadow12", "batman12", "ginger12", "summer12", "winter12", "Passw0rd", "P4ssw0rd",
        "Pass+123", "Pass*123", "admin123", "root1234", "test1234", "11111111", "00000000", "12121212",
        "qwerty12", "abcd1234", "qwer1234", "zaq1zaq1", "michael1", "jennifer", "jonathan", "patricia",
        "nicholas", "samantha", "mercedes", "corvette", "fireball", "bonjour1", "chocolat", "vacances",
        "fromage1", "famille1", "musique1", "bisous12", "doudou12", "amour123", "footbal1", "biloute1",
        "azerty12", "azertyui", "champion", "toulouse", "bordeaux", "marseil1", "maison12", "copain12",
        "voiture1", "lesecret", "soleil12", "printemp",
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
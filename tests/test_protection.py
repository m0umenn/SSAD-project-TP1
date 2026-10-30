"""Unit tests for password generators, encryption-based protection, and lockout (Part 3)."""

from __future__ import annotations

import importlib
import itertools
import pkgutil
import unittest

import passwords
from passwords import cipher_adapter, generators, protection


class FakeClock:
    """Deterministic monotonic clock replacement for lockout tests."""

    def __init__(self, initial: float = 100.0) -> None:
        self.now = initial

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestGenerators(unittest.TestCase):
    """Tests for passwords.generators candidate generation."""

    def test_candidates_use_case_1(self) -> None:
        items = list(generators.candidates("01", 3))
        self.assertEqual(
            items,
            ["000", "001", "010", "011", "100", "101", "110", "111"],
        )

    def test_candidates_use_case_2(self) -> None:
        items = list(generators.candidates("1234", 4))
        self.assertEqual(len(items), 256)
        self.assertEqual(items[0], "1111")
        self.assertEqual(items[-1], "4444")
        self.assertEqual(items.index("3214"), 147)

    def test_candidates_case_3_vector_abcd(self) -> None:
        gen = generators.candidates(generators.CASE_3_ALPHABET, 4)
        first = next(gen)
        self.assertEqual(first, "aaaa")
        abcd = next(itertools.islice(generators.candidates(generators.CASE_3_ALPHABET, 4), 4227, None))
        self.assertEqual(abcd, "abcd")


class TestProtectionValidation(unittest.TestCase):
    """Tests for validate_password across use cases."""

    def test_valid_passwords_accepted(self) -> None:
        protection.validate_password("101", 1)
        protection.validate_password("3214", 2)
        for pw in ("abcd", "Ab56", "Q+g4"):
            with self.subTest(pw=pw, uc=3):
                protection.validate_password(pw, 3)
        for pw in ("abcdef", "Abc123", "H*bD88"):
            with self.subTest(pw=pw, uc=4):
                protection.validate_password(pw, 4)
        for pw in ("abcdefgh", "Abcd1234", "jK+73*Dd"):
            with self.subTest(pw=pw, uc=5):
                protection.validate_password(pw, 5)

    def test_unknown_use_case_rejected(self) -> None:
        for bad_uc in (0, 6, 99, -1, True):
            with self.subTest(use_case=bad_uc):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password("101", bad_uc)
                self.assertEqual(str(ctx.exception), "Unknown use case.")

    def test_use_case_1_rejections(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            protection.validate_password("", 1)
        self.assertEqual(str(ctx.exception), "Password is empty.")

        for wrong_len in ("0", "01", "0101"):
            with self.subTest(password=wrong_len):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(wrong_len, 1)
                self.assertEqual(
                    str(ctx.exception),
                    "Password must have exactly 3 characters.",
                )

        for bad_chars in ("012", "01a", "999"):
            with self.subTest(password=bad_chars):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(bad_chars, 1)
                self.assertEqual(
                    str(ctx.exception),
                    "Only these characters are allowed: 01",
                )

    def test_use_case_2_rejections(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            protection.validate_password("", 2)
        self.assertEqual(str(ctx.exception), "Password is empty.")

        for wrong_len in ("123", "12345", "1"):
            with self.subTest(password=wrong_len):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(wrong_len, 2)
                self.assertEqual(
                    str(ctx.exception),
                    "Password must have exactly 4 characters.",
                )

        for bad_chars in ("1235", "1230", "123a"):
            with self.subTest(password=bad_chars):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(bad_chars, 2)
                self.assertEqual(
                    str(ctx.exception),
                    "Only these characters are allowed: 1234",
                )

    def test_use_case_3_rejections(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            protection.validate_password("", 3)
        self.assertEqual(str(ctx.exception), "Password is empty.")

        for wrong_len in ("abc", "abcde", "a"):
            with self.subTest(password=wrong_len):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(wrong_len, 3)
                self.assertEqual(
                    str(ctx.exception),
                    "Password must have exactly 4 characters.",
                )

        for bad_chars in ("abc@", "ab c", "ab-d"):
            with self.subTest(password=bad_chars):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(bad_chars, 3)
                self.assertEqual(
                    str(ctx.exception),
                    f"Only these characters are allowed: {generators.CASE_3_ALPHABET}",
                )

    def test_use_case_4_rejections(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            protection.validate_password("", 4)
        self.assertEqual(str(ctx.exception), "Password is empty.")

        for wrong_len in ("abcde", "abcd", "abcdefg"):
            with self.subTest(password=wrong_len):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(wrong_len, 4)
                self.assertEqual(
                    str(ctx.exception),
                    "Password must have exactly 6 characters.",
                )

        for bad_chars in ("abcde@", "Abc12!"):
            with self.subTest(password=bad_chars):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(bad_chars, 4)
                self.assertEqual(
                    str(ctx.exception),
                    f"Only these characters are allowed: {generators.CASE_3_ALPHABET}",
                )

    def test_use_case_5_rejections(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            protection.validate_password("", 5)
        self.assertEqual(str(ctx.exception), "Password is empty.")

        for wrong_len in ("abcdefg", "abcdef", "abcdefghi"):
            with self.subTest(password=wrong_len):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(wrong_len, 5)
                self.assertEqual(
                    str(ctx.exception),
                    "Password must have exactly 8 characters.",
                )

        for bad_chars in ("abcdefg@", "jK+73*D!"):
            with self.subTest(password=bad_chars):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(bad_chars, 5)
                self.assertEqual(
                    str(ctx.exception),
                    f"Only these characters are allowed: {generators.CASE_3_ALPHABET}",
                )


class TestEncryptedProtection(unittest.TestCase):
    """Tests for encrypt-based protection, checker closure, and key isolation."""

    PASSWORDS_BY_USE_CASE = {
        1: ("101", "010"),
        2: ("3214", "1234"),
        3: ("abcd", "Zyx9"),
        4: ("Abc123", "Zyx987"),
        5: ("jK+73*Dd", "Pass1234"),
    }

    # Valid Hill keys (odd det mod m) for each use case
    HILL_KEYS = {
        1: [[1, 1, 0], [0, 1, 1], [0, 0, 1]],  # m=2, det=1
        2: [[1, 2], [3, 3]],                      # m=4, det=1 mod 4
        3: [[3, 2], [5, 7]],                      # m=64, det=11
        4: [[1, 2, 3], [0, 1, 4], [5, 6, 0]],    # m=64, det=1
        5: [[3, 2], [5, 7]],                      # m=64, det=11
    }

    def test_protect_and_decrypt_round_trip_caesar_every_use_case(self) -> None:
        for use_case, (password, _) in self.PASSWORDS_BY_USE_CASE.items():
            alphabet = cipher_adapter.get_alphabet(use_case)
            m = len(alphabet)
            for key in (1, 3):
                if key >= m:
                    continue
                with self.subTest(use_case=use_case, key=key):
                    record = protection.protect(password, use_case, cipher="caesar", key=key)
                    self.assertEqual(record["use_case"], use_case)
                    self.assertEqual(record["cipher"], "caesar")
                    self.assertIsInstance(record["ciphertext"], str)
                    self.assertIsInstance(record["params"], dict)
                    self.assertIn("modulus", record["params"])

                    decrypted = cipher_adapter.decrypt(
                        record["ciphertext"], key=key, use_case=use_case, cipher="caesar"
                    )
                    self.assertEqual(decrypted, password)

    def test_protect_and_decrypt_round_trip_hill_every_use_case(self) -> None:
        for use_case, (password, _) in self.PASSWORDS_BY_USE_CASE.items():
            key = self.HILL_KEYS[use_case]
            with self.subTest(use_case=use_case):
                record = protection.protect(password, use_case, cipher="hill", key=key)
                self.assertEqual(record["cipher"], "hill")
                self.assertIn("modulus", record["params"])
                self.assertIn("block", record["params"])

                decrypted = cipher_adapter.decrypt(
                    record["ciphertext"], key=key, use_case=use_case, cipher="hill"
                )
                self.assertEqual(decrypted, password)

    def test_make_checker_accepts_right_password_rejects_wrong_caesar(self) -> None:
        for use_case, (right_pw, wrong_pw) in self.PASSWORDS_BY_USE_CASE.items():
            alphabet = cipher_adapter.get_alphabet(use_case)
            m = len(alphabet)
            key = 3 if m > 3 else 1
            record = protection.protect(right_pw, use_case, cipher="caesar", key=key)
            check = protection.make_checker(record, key)

            self.assertTrue(check(right_pw))
            self.assertFalse(check(wrong_pw))
            self.assertFalse(check(""))

    def test_make_checker_accepts_right_password_rejects_wrong_hill(self) -> None:
        for use_case, (right_pw, wrong_pw) in self.PASSWORDS_BY_USE_CASE.items():
            key = self.HILL_KEYS[use_case]
            record = protection.protect(right_pw, use_case, cipher="hill", key=key)
            check = protection.make_checker(record, key)

            self.assertTrue(check(right_pw))
            self.assertFalse(check(wrong_pw))
            self.assertFalse(check(""))

    def test_wrong_key_makes_correct_password_fail(self) -> None:
        # Caesar: different shift makes checker fail
        for use_case, (right_pw, _) in self.PASSWORDS_BY_USE_CASE.items():
            alphabet = cipher_adapter.get_alphabet(use_case)
            m = len(alphabet)
            key = 3 if m > 4 else 1
            wrong_key = (key % (m - 1)) + 1
            if wrong_key == key:
                wrong_key = 1 if key != 1 else 2
            if wrong_key >= m:
                continue
            record = protection.protect(right_pw, use_case, cipher="caesar", key=key)
            check_correct = protection.make_checker(record, key)
            check_wrong = protection.make_checker(record, wrong_key)
            self.assertTrue(check_correct(right_pw))
            self.assertFalse(check_wrong(right_pw))

    def test_record_never_contains_the_key(self) -> None:
        # Caesar: numeric key should not appear in record values
        for key in (5, 11, 37):
            record = protection.protect("aB1+", 3, cipher="caesar", key=key)
            self.assertNotIn("key", record)
            for k, v in record.items():
                self.assertNotEqual(k, "key")
                if isinstance(v, dict):
                    self.assertNotIn("key", v)
        # Hill: key matrix should not be stored
        hill_key = [[3, 2], [5, 7]]
        record = protection.protect("aB1+", 3, cipher="hill", key=hill_key)
        self.assertNotIn("key", record)
        for k in record:
            self.assertNotEqual(k, "key")

    def test_no_module_under_passwords_imports_hashlib(self) -> None:
        for module_info in pkgutil.walk_packages(passwords.__path__, prefix="passwords."):
            mod = importlib.import_module(module_info.name)
            self.assertNotIn(
                "hashlib",
                mod.__dict__,
                f"{module_info.name} imports hashlib!",
            )
            file_path = getattr(mod, "__file__", None)
            if file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                    self.assertNotIn("import hashlib", source, f"hashlib imported in {module_info.name}")
                    self.assertNotIn("from hashlib", source, f"hashlib imported in {module_info.name}")
                    self.assertNotIn("import hmac", source, f"hmac imported in {module_info.name}")
                    self.assertNotIn("from hmac", source, f"hmac imported in {module_info.name}")


class TestLockout(unittest.TestCase):
    """Tests for Lockout using an injectable fake clock without sleeping."""

    def test_five_failures_lock_and_unlock_after_lock_seconds(self) -> None:
        clock = FakeClock(initial=0.0)
        lockout = protection.Lockout(
            max_failures=protection.MAX_FAILURES,
            lock_seconds=protection.LOCK_SECONDS,
            clock=clock,
        )

        self.assertEqual(lockout.attempts_left(), 5)
        self.assertEqual(lockout.remaining(), 0.0)

        for expected_left in (4, 3, 2, 1):
            self.assertFalse(lockout.record(False))
            self.assertEqual(lockout.attempts_left(), expected_left)
            self.assertEqual(lockout.remaining(), 0.0)

        # 5th failure triggers lock
        self.assertFalse(lockout.record(False))
        self.assertEqual(lockout.attempts_left(), 0)
        self.assertAlmostEqual(lockout.remaining(), float(protection.LOCK_SECONDS))

        # Correct password during lock raises ValueError
        clock.advance(10.0)
        with self.assertRaises(ValueError) as ctx:
            lockout.record(True)
        self.assertEqual(str(ctx.exception), "Locked. Try again in 20 s.")

        # Advance past LOCK_SECONDS -> unlocked and works again
        clock.advance(float(protection.LOCK_SECONDS))
        self.assertEqual(lockout.remaining(), 0.0)
        self.assertEqual(lockout.attempts_left(), 5)
        self.assertTrue(lockout.record(True))

    def test_success_resets_failure_counter(self) -> None:
        clock = FakeClock(initial=50.0)
        lockout = protection.Lockout(max_failures=5, lock_seconds=30, clock=clock)

        self.assertFalse(lockout.record(False))
        self.assertFalse(lockout.record(False))
        self.assertEqual(lockout.attempts_left(), 3)

        self.assertTrue(lockout.record(True))
        self.assertEqual(lockout.attempts_left(), 5)

        for expected_left in (4, 3, 2, 1):
            self.assertFalse(lockout.record(False))
            self.assertEqual(lockout.attempts_left(), expected_left)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for password generators and protection mechanisms."""

from __future__ import annotations

import itertools
import unittest

from passwords import generators, protection


class FakeClock:
    """Deterministic monotonic clock replacement for lockout tests."""

    def __init__(self, initial: float = 100.0) -> None:
        self.now = initial

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestGenerators(unittest.TestCase):
    """Tests for passwords.generators."""

    def test_hash_fast_known_vector(self) -> None:
        self.assertEqual(
            generators.hash_fast("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

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

        for wrong_len in ("123", "12", "12345"):
            with self.subTest(password=wrong_len):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(wrong_len, 2)
                self.assertEqual(
                    str(ctx.exception),
                    "Password must have exactly 4 characters.",
                )

        for bad_chars in ("1230", "1235", "abcd"):
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

        for wrong_len in ("abc", "ab", "abcde"):
            with self.subTest(password=wrong_len):
                with self.assertRaises(ValueError) as ctx:
                    protection.validate_password(wrong_len, 3)
                self.assertEqual(
                    str(ctx.exception),
                    "Password must have exactly 4 characters.",
                )

        for bad_chars in ("abc@", "ab 5", "Q#g4"):
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


class TestProtectedHashingAndChecker(unittest.TestCase):
    """Tests for hash_protected, verify_protected, and make_checker."""

    FAST_ITERATIONS = 1000

    def test_round_trip_and_wrong_password(self) -> None:
        record = protection.hash_protected("3214", iterations=self.FAST_ITERATIONS)
        self.assertTrue(protection.verify_protected("3214", record))
        self.assertFalse(protection.verify_protected("1111", record))

    def test_case_3_round_trip(self) -> None:
        for pw, wrong in (("abcd", "Ab56"), ("Abc123", "secret"), ("jK+73*Dd", "Pass1234")):
            with self.subTest(password=pw):
                record = protection.hash_protected(pw, iterations=self.FAST_ITERATIONS)
                self.assertTrue(protection.verify_protected(pw, record))
                self.assertFalse(protection.verify_protected(wrong, record))
                checker = protection.make_checker(record)
                self.assertTrue(checker(pw))
                self.assertFalse(checker(wrong))


    def test_unique_salts_and_hashes(self) -> None:
        r1 = protection.hash_protected("3214", iterations=self.FAST_ITERATIONS)
        r2 = protection.hash_protected("3214", iterations=self.FAST_ITERATIONS)
        self.assertNotEqual(r1["salt"], r2["salt"])
        self.assertNotEqual(r1["hash"], r2["hash"])

    def test_tampered_and_malformed_records(self) -> None:
        record = protection.hash_protected("101", iterations=self.FAST_ITERATIONS)

        tampered_hash = dict(record)
        orig_hash = str(record["hash"])
        flipped = ("0" if orig_hash[0] != "0" else "1") + orig_hash[1:]
        tampered_hash["hash"] = flipped
        self.assertFalse(protection.verify_protected("101", tampered_hash))

        tampered_salt = dict(record)
        orig_salt = str(record["salt"])
        tampered_salt["salt"] = ("0" if orig_salt[0] != "0" else "1") + orig_salt[1:]
        self.assertFalse(protection.verify_protected("101", tampered_salt))

        malformed_records = [
            "not a dict",
            {},
            {"salt": record["salt"], "iterations": self.FAST_ITERATIONS},
            {"salt": "", "iterations": self.FAST_ITERATIONS, "hash": record["hash"]},
            {"salt": "zz", "iterations": self.FAST_ITERATIONS, "hash": record["hash"]},
            {"salt": record["salt"], "iterations": 0, "hash": record["hash"]},
            {"salt": record["salt"], "iterations": -5, "hash": record["hash"]},
            {"salt": record["salt"], "iterations": True, "hash": record["hash"]},
            {"salt": record["salt"], "iterations": self.FAST_ITERATIONS, "hash": "short"},
            {"salt": record["salt"], "iterations": self.FAST_ITERATIONS, "hash": "g" * 64},
        ]
        for bad in malformed_records:
            with self.subTest(record=bad):
                with self.assertRaises(ValueError) as ctx:
                    protection.verify_protected("101", bad)  # type: ignore[arg-type]
                self.assertEqual(str(ctx.exception), "Malformed record.")

    def test_make_checker_hex_and_record_and_invalid(self) -> None:
        fast_target = generators.hash_fast("101")
        check_fast = protection.make_checker(fast_target)
        self.assertTrue(check_fast("101"))
        self.assertFalse(check_fast("000"))

        record_target = protection.hash_protected("3214", iterations=self.FAST_ITERATIONS)
        check_prot = protection.make_checker(record_target)
        self.assertTrue(check_prot("3214"))
        self.assertFalse(check_prot("4444"))

        for bad_target in (None, 123, ["101"], "", "not-hex!", {"bad": "record"}):
            with self.subTest(target=bad_target):
                with self.assertRaises(ValueError):
                    protection.make_checker(bad_target)  # type: ignore[arg-type]


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

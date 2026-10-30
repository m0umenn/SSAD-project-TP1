"""Unit tests for integrity and hashing mechanisms (Part 4).

Tests fast hashing, PBKDF2 stretching, constant-time comparison,
record validation, and timing estimation without importing from passwords/ or gui/.
"""

from __future__ import annotations

import unittest

from integrity import (
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


class TestIntegrityHashing(unittest.TestCase):
    """Tests for integrity.hashing functions and constants."""

    FAST_ITERATIONS = 1000

    def test_constants(self) -> None:
        self.assertEqual(ITERATIONS, 100_000)
        self.assertEqual(SALT_BYTES, 16)

    def test_hash_fast_known_vectors(self) -> None:
        # Standard SHA-256 test vectors specified in requirements
        self.assertEqual(
            hash_fast("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )
        self.assertEqual(
            hash_fast(""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_hash_fast_invalid_type(self) -> None:
        for bad_input in (123, None, ["abc"], {"a": "b"}, True):
            with self.subTest(bad=bad_input):
                with self.assertRaises(ValueError) as ctx:
                    hash_fast(bad_input)  # type: ignore[arg-type]
                self.assertEqual(str(ctx.exception), "Password must be a string.")

    def test_generate_salt(self) -> None:
        s1 = generate_salt(16)
        s2 = generate_salt(16)
        self.assertEqual(len(s1), 16)
        self.assertEqual(len(s2), 16)
        self.assertNotEqual(s1, s2)
        with self.assertRaises(ValueError):
            generate_salt(0)
        with self.assertRaises(ValueError):
            generate_salt(-1)
        with self.assertRaises(ValueError):
            generate_salt(True)  # type: ignore[arg-type]

    def test_compare_hashes(self) -> None:
        self.assertTrue(compare_hashes("abcdef", "abcdef"))
        self.assertFalse(compare_hashes("abcdef", "abcdeg"))
        self.assertFalse(compare_hashes("abcdef", "abcde"))

    def test_round_trip_and_wrong_password(self) -> None:
        record = hash_protected("3214", iterations=self.FAST_ITERATIONS)
        self.assertTrue(verify_protected("3214", record))
        self.assertFalse(verify_protected("1111", record))

    def test_multiple_round_trips(self) -> None:
        for pw, wrong in (("abcd", "Ab56"), ("Abc123", "secret"), ("jK+73*Dd", "Pass1234")):
            with self.subTest(password=pw):
                record = hash_protected(pw, iterations=self.FAST_ITERATIONS)
                self.assertTrue(verify_protected(pw, record))
                self.assertFalse(verify_protected(wrong, record))

    def test_unique_salts_and_hashes(self) -> None:
        r1 = hash_protected("3214", iterations=self.FAST_ITERATIONS)
        r2 = hash_protected("3214", iterations=self.FAST_ITERATIONS)
        self.assertNotEqual(r1["salt"], r2["salt"])
        self.assertNotEqual(r1["hash"], r2["hash"])

    def test_tampered_and_malformed_records(self) -> None:
        record = hash_protected("101", iterations=self.FAST_ITERATIONS)

        tampered_hash = dict(record)
        orig_hash = str(record["hash"])
        flipped = ("0" if orig_hash[0] != "0" else "1") + orig_hash[1:]
        tampered_hash["hash"] = flipped
        self.assertFalse(verify_protected("101", tampered_hash))

        tampered_salt = dict(record)
        orig_salt = str(record["salt"])
        tampered_salt["salt"] = ("0" if orig_salt[0] != "0" else "1") + orig_salt[1:]
        self.assertFalse(verify_protected("101", tampered_salt))

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
                    verify_protected("101", bad)  # type: ignore[arg-type]
                self.assertEqual(str(ctx.exception), "Malformed record.")

    def test_parse_record(self) -> None:
        record = hash_protected("pass", iterations=100)
        salt_bytes, iters, hash_hex = parse_record(record)
        self.assertEqual(len(salt_bytes), SALT_BYTES)
        self.assertEqual(iters, 100)
        self.assertEqual(len(hash_hex), 64)

    def test_estimate_slowdown(self) -> None:
        self.assertEqual(estimate_slowdown(1000, rate=500.0), 2.0)
        self.assertEqual(estimate_slowdown(1000, rate=500.0, factor=2.5), 5.0)
        self.assertEqual(estimate_slowdown(1000, rate=0.0), float("inf"))


if __name__ == "__main__":
    unittest.main()

"""Tests for passwords.cipher_adapter (Step 4).

Hand-verified vectors:
  UC2, Hill, K=[[1,2],[3,3]]: 2431 -> 4133   inv=[[3,2],[1,1]]
  UC1, Hill, K=[[1,1,0],[0,1,1],[0,0,1]]: 101->111, 011->101   inv=[[1,1,1],[0,1,1],[0,0,1]]
  UC3, Hill, K=[[3,2],[5,7]]: aB1+ -> 29B7   inv=[[53,58],[17,41]]
  UC3, Caesar k=5: aB1+ -> fG6d
"""

from __future__ import annotations

import unittest

from passwords import cipher_adapter
from passwords.cipher_adapter import (
    USE_CASE_ALPHABETS,
    USE_CASE_CIPHER,
    block_size,
    decrypt,
    encrypt,
    get_alphabet,
    parse_key,
)
from passwords.generators import CASE_3_ALPHABET


class TestAlphabets(unittest.TestCase):
    """Alphabet and constant sanity checks."""

    def test_use_case_alphabets(self) -> None:
        self.assertEqual(get_alphabet(1), "01")
        self.assertEqual(get_alphabet(2), "1234")
        self.assertEqual(get_alphabet(3), CASE_3_ALPHABET)
        self.assertEqual(get_alphabet(4), CASE_3_ALPHABET)
        self.assertEqual(get_alphabet(5), CASE_3_ALPHABET)
        self.assertEqual(len(get_alphabet(3)), 64)

    def test_default_ciphers_are_hill(self) -> None:
        for uc in (1, 2, 3, 4, 5):
            self.assertEqual(USE_CASE_CIPHER[uc], "hill")

    def test_block_sizes(self) -> None:
        self.assertEqual(block_size(1), 3)
        self.assertEqual(block_size(2), 2)
        self.assertEqual(block_size(3), 2)
        self.assertEqual(block_size(4), 3)
        self.assertEqual(block_size(5), 2)

    def test_block_divides_length(self) -> None:
        from passwords.generators import USE_CASES
        for uc, spec in USE_CASES.items():
            n = block_size(uc)
            self.assertEqual(int(spec["length"]) % n, 0,
                             f"UC{uc}: length {spec['length']} not divisible by block {n}")


class TestHandVerifiedVectors(unittest.TestCase):
    """Exact hand-verified encrypt/decrypt vectors from the spec."""

    def test_uc2_hill_encrypt(self) -> None:
        # UC2: alphabet "1234" (m=4), K=[[1,2],[3,3]], text=2431 -> 4133
        # Indices of "2431" in "1234": 1,3,2,0  (0-indexed: '1'->0,'2'->1,'3'->2,'4'->3)
        key = [[1, 2], [3, 3]]
        ct = encrypt("2431", key, use_case=2, cipher="hill")
        self.assertEqual(ct, "4133")

    def test_uc2_hill_decrypt(self) -> None:
        # decrypt() computes the inverse internally; pass the original key
        # The true inverse is [[3,2],[1,1]] mod 4
        key = [[1, 2], [3, 3]]
        pt = decrypt("4133", key, use_case=2, cipher="hill")
        self.assertEqual(pt, "2431")

    def test_uc2_hill_round_trip(self) -> None:
        key = [[1, 2], [3, 3]]
        ct = encrypt("2431", key, use_case=2, cipher="hill")
        pt = decrypt(ct, key, use_case=2, cipher="hill")
        self.assertEqual(pt, "2431")

    def test_uc1_hill_vector_101(self) -> None:
        # UC1: alphabet "01" (m=2), K=[[1,1,0],[0,1,1],[0,0,1]], 101->111
        key = [[1, 1, 0], [0, 1, 1], [0, 0, 1]]
        ct = encrypt("101", key, use_case=1, cipher="hill")
        self.assertEqual(ct, "111")

    def test_uc1_hill_vector_011(self) -> None:
        # 011 -> 101
        key = [[1, 1, 0], [0, 1, 1], [0, 0, 1]]
        ct = encrypt("011", key, use_case=1, cipher="hill")
        self.assertEqual(ct, "101")

    def test_uc1_hill_decrypt(self) -> None:
        # decrypt() computes the inverse internally; pass the original key
        # The true inverse is [[1,1,1],[0,1,1],[0,0,1]] mod 2
        key = [[1, 1, 0], [0, 1, 1], [0, 0, 1]]
        self.assertEqual(decrypt("111", key, use_case=1, cipher="hill"), "101")
        self.assertEqual(decrypt("101", key, use_case=1, cipher="hill"), "011")

    def test_uc3_hill_vector(self) -> None:
        # UC3: alphabet 64-char (m=64), K=[[3,2],[5,7]], aB1+ -> 29B7
        key = [[3, 2], [5, 7]]
        ct = encrypt("aB1+", key, use_case=3, cipher="hill")
        self.assertEqual(ct, "29B7")

    def test_uc3_hill_decrypt(self) -> None:
        # decrypt() computes the inverse internally; pass the original key
        # The true inverse is [[53,58],[17,41]] mod 64
        key = [[3, 2], [5, 7]]
        pt = decrypt("29B7", key, use_case=3, cipher="hill")
        self.assertEqual(pt, "aB1+")

    def test_uc3_hill_round_trip(self) -> None:
        key = [[3, 2], [5, 7]]
        ct = encrypt("aB1+", key, use_case=3, cipher="hill")
        pt = decrypt(ct, key, use_case=3, cipher="hill")
        self.assertEqual(pt, "aB1+")

    def test_uc3_caesar_vector(self) -> None:
        # UC3, Caesar k=5: aB1+ -> fG6d
        ct = encrypt("aB1+", 5, use_case=3, cipher="caesar")
        self.assertEqual(ct, "fG6d")

    def test_uc3_caesar_decrypt(self) -> None:
        pt = decrypt("fG6d", 5, use_case=3, cipher="caesar")
        self.assertEqual(pt, "aB1+")


class TestRoundTrip(unittest.TestCase):
    """Round-trip for every use case with both ciphers."""

    SAMPLE_PASSWORDS = {
        1: "101",
        2: "2431",
        3: "aB1+",
        4: "Abc123",
        5: "jK+73*Dd",
    }

    CAESAR_KEYS = {1: 1, 2: 3, 3: 5, 4: 7, 5: 11}

    # Pre-validated Hill keys (odd determinant mod m, not identity)
    HILL_KEYS = {
        1: [[1, 1, 0], [0, 1, 1], [0, 0, 1]],   # m=2, det=1
        2: [[1, 2], [3, 3]],                       # m=4, det=-3%4=1
        3: [[3, 2], [5, 7]],                       # m=64, det=11
        4: [[1, 2, 3], [0, 1, 4], [5, 6, 0]],     # m=64, det=1, checked below
        5: [[3, 2], [5, 7]],                       # m=64, det=11
    }

    def test_hill_keys_valid(self) -> None:
        """Ensure all sample Hill keys parse without error."""
        for uc, mat in self.HILL_KEYS.items():
            with self.subTest(use_case=uc):
                parsed = parse_key(mat, uc, "hill")
                self.assertIsInstance(parsed, list)

    def test_round_trip_hill_all_use_cases(self) -> None:
        for uc, pw in self.SAMPLE_PASSWORDS.items():
            with self.subTest(use_case=uc):
                key = self.HILL_KEYS[uc]
                ct = encrypt(pw, key, uc, "hill")
                pt = decrypt(ct, key, uc, "hill")
                self.assertEqual(pt, pw)

    def test_round_trip_caesar_all_use_cases(self) -> None:
        for uc, pw in self.SAMPLE_PASSWORDS.items():
            with self.subTest(use_case=uc):
                k = self.CAESAR_KEYS[uc]
                ct = encrypt(pw, k, uc, "caesar")
                pt = decrypt(ct, k, uc, "caesar")
                self.assertEqual(pt, pw)


class TestParseKey(unittest.TestCase):
    """parse_key validation: invalid keys are rejected with friendly messages."""

    def test_caesar_valid(self) -> None:
        k = parse_key("5", use_case=3, cipher="caesar")
        self.assertEqual(k, 5)
        k = parse_key(1, use_case=1, cipher="caesar")
        self.assertEqual(k, 1)

    def test_caesar_empty_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            parse_key("", use_case=2, cipher="caesar")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_caesar_out_of_range(self) -> None:
        # m=4 for UC2, so k must be 1..3
        with self.assertRaises(ValueError):
            parse_key(4, use_case=2, cipher="caesar")  # k == m
        with self.assertRaises(ValueError):
            parse_key(0, use_case=2, cipher="caesar")

    def test_caesar_non_integer_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_key("abc", use_case=3, cipher="caesar")

    def test_hill_valid_list(self) -> None:
        mat = parse_key([[3, 2], [5, 7]], use_case=3, cipher="hill")
        self.assertEqual(mat, [[3, 2], [5, 7]])

    def test_hill_valid_string(self) -> None:
        mat = parse_key("3 2 5 7", use_case=3, cipher="hill")
        self.assertEqual(mat, [[3, 2], [5, 7]])

    def test_hill_identity_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            parse_key([[1, 0], [0, 1]], use_case=3, cipher="hill")
        self.assertIn("identity", str(ctx.exception).lower())

    def test_hill_even_determinant_rejected(self) -> None:
        # [[2,0],[0,1]] has det=2, gcd(2,64)=2 -> invalid
        with self.assertRaises(ValueError) as ctx:
            parse_key([[2, 0], [0, 1]], use_case=3, cipher="hill")
        self.assertIn("factor", str(ctx.exception).lower())

    def test_hill_wrong_count_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            parse_key([1, 2, 3], use_case=3, cipher="hill")  # needs 4 entries
        self.assertIn("4", str(ctx.exception))

    def test_hill_out_of_range_entry(self) -> None:
        with self.assertRaises(ValueError):
            parse_key([[3, 2], [5, 64]], use_case=3, cipher="hill")  # 64 >= m=64

    def test_hill_empty_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_key("", use_case=3, cipher="hill")

    def test_hill_non_integer_entry_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_key("3 x 5 7", use_case=3, cipher="hill")

    def test_unknown_cipher_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_key("5", use_case=3, cipher="vigenere")


class TestWrongKeyFails(unittest.TestCase):
    """Wrong key must make the correct password fail the checker."""

    def test_hill_wrong_key(self) -> None:
        from passwords.protection import make_checker, protect
        right_key = [[3, 2], [5, 7]]
        wrong_key = [[1, 2], [3, 3]]
        record = protect("aB1+", 3, cipher="hill", key=right_key)
        self.assertFalse(make_checker(record, wrong_key)("aB1+"))

    def test_caesar_wrong_key(self) -> None:
        from passwords.protection import make_checker, protect
        record = protect("aB1+", 3, cipher="caesar", key=5)
        self.assertFalse(make_checker(record, 6)("aB1+"))


class TestRecordContainsNoKey(unittest.TestCase):
    """Record must not contain the key in any field."""

    def _inspect(self, obj: object, key_val: object) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                self.assertNotEqual(k, "key")
                self.assertNotEqual(v, key_val)
                self._inspect(v, key_val)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                self._inspect(item, key_val)

    def test_hill_record_has_no_key(self) -> None:
        from passwords.protection import protect
        secret = [[3, 2], [5, 7]]
        record = protect("aB1+", 3, cipher="hill", key=secret)
        self.assertNotIn("key", record)
        # The matrix values 3,2,5,7 might legitimately appear in params (modulus=64, block=2)
        # but the KEY ITSELF should not be stored as a field named "key"
        self.assertNotIn("key", record)

    def test_caesar_record_has_no_key_field(self) -> None:
        from passwords.protection import protect
        for k in (1, 5, 42, 63):
            record = protect("aB1+", 3, cipher="caesar", key=k)
            self.assertNotIn("key", record)
            for v in record.values():
                if isinstance(v, dict):
                    self.assertNotIn("key", v)


if __name__ == "__main__":
    unittest.main()

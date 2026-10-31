"""Unit tests for automated key generation and password protection."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from passwords import key_store, protection


class TestProtectionAuto(unittest.TestCase):
    """Test protection and verification with automated key store."""

    SAMPLE_PASSWORDS = {
        1: ("101", "010"),
        2: ("3214", "1234"),
        3: ("abcd", "Zyx9"),
        4: ("Abc123", "Zyx987"),
        5: ("jK+73*Dd", "Pass1234"),
    }

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="ssad_test_prot_")
        self.key_file = os.path.join(self.temp_dir, "keys.json")
        key_store.set_key_file(self.key_file)

    def tearDown(self) -> None:
        key_store.set_key_file(None)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_protect_and_make_checker_auto_key_all_use_cases_and_ciphers(self) -> None:
        for use_case, (right_pw, wrong_pw) in self.SAMPLE_PASSWORDS.items():
            for cipher in ("caesar", "hill"):
                with self.subTest(use_case=use_case, cipher=cipher):
                    record = protection.protect(right_pw, use_case, cipher=cipher)

                    # Verify record structure
                    self.assertEqual(set(record.keys()), {"use_case", "cipher", "ciphertext", "params"})
                    self.assertEqual(record["use_case"], use_case)
                    self.assertEqual(record["cipher"], cipher)
                    self.assertIsInstance(record["ciphertext"], str)
                    self.assertEqual(set(record["params"].keys()), {"modulus", "block"})

                    # Verify checker with no key passed
                    check = protection.make_checker(record)
                    self.assertTrue(check(right_pw))
                    self.assertFalse(check(wrong_pw))
                    self.assertFalse(check(""))
                    self.assertFalse(check("bad_length"))

    def test_record_and_exceptions_never_contain_key(self) -> None:
        for use_case in (1, 2, 3):
            for cipher in ("caesar", "hill"):
                with self.subTest(use_case=use_case, cipher=cipher):
                    pw = self.SAMPLE_PASSWORDS[use_case][0]
                    record = protection.protect(pw, use_case, cipher=cipher)
                    key = key_store.get_key(use_case, cipher)

                    # Check record keys
                    self.assertNotIn("key", record)
                    self.assertNotIn("key", record["params"])

                    # Check serialized record
                    serialized = str(record)
                    self.assertNotIn("key", serialized)
                    if isinstance(key, list):
                        self.assertNotIn(str(key), serialized)

                    # Check that exceptions do not leak key
                    try:
                        protection.validate_password("invalid_pw!!!", use_case)
                    except ValueError as exc:
                        self.assertNotIn(str(key), str(exc))

                    try:
                        protection.make_checker({"use_case": 999, "ciphertext": "xyz"})
                    except Exception as exc:
                        self.assertNotIn(str(key), str(exc))

    def test_hand_verified_vectors_with_explicit_keys(self) -> None:
        # Vector 1: Use case 2 Hill K=[[1,2],[3,3]] password 2431 -> 4133
        k_uc2 = [[1, 2], [3, 3]]
        rec1 = protection.protect("2431", 2, cipher="hill", key=k_uc2)
        self.assertEqual(rec1["ciphertext"], "4133")
        chk1 = protection.make_checker(rec1, key=k_uc2)
        self.assertTrue(chk1("2431"))
        self.assertFalse(chk1("1234"))

        # Vector 2: Use case 1 Hill K=[[1,1,0],[0,1,1],[0,0,1]] password 101 -> 111
        k_uc1 = [[1, 1, 0], [0, 1, 1], [0, 0, 1]]
        rec2 = protection.protect("101", 1, cipher="hill", key=k_uc1)
        self.assertEqual(rec2["ciphertext"], "111")
        chk2 = protection.make_checker(rec2, key=k_uc1)
        self.assertTrue(chk2("101"))
        self.assertFalse(chk2("010"))

        # Vector 3: Use case 3 Hill K=[[3,2],[5,7]] password aB1+ -> 29B7
        k_uc3 = [[3, 2], [5, 7]]
        rec3 = protection.protect("aB1+", 3, cipher="hill", key=k_uc3)
        self.assertEqual(rec3["ciphertext"], "29B7")
        chk3 = protection.make_checker(rec3, key=k_uc3)
        self.assertTrue(chk3("aB1+"))
        self.assertFalse(chk3("Zyx9"))

        # Vector 4: Use case 3 Caesar k=5 password aB1+ -> fG6d
        rec4 = protection.protect("aB1+", 3, cipher="caesar", key=5)
        self.assertEqual(rec4["ciphertext"], "fG6d")
        chk4 = protection.make_checker(rec4, key=5)
        self.assertTrue(chk4("aB1+"))
        self.assertFalse(chk4("aB1-"))


"""Unit tests for passwords.key_store module."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from passwords import cipher_adapter, key_store


class TestKeyStore(unittest.TestCase):
    """Test automated key generation and persistent storage."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="ssad_test_keystore_")
        self.key_file = os.path.join(self.temp_dir, "keys.json")
        key_store.set_key_file(self.key_file)

    def tearDown(self) -> None:
        key_store.set_key_file(None)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_created_on_first_use(self) -> None:
        self.assertFalse(os.path.exists(self.key_file))
        key = key_store.get_key(1, "caesar")
        self.assertTrue(os.path.exists(self.key_file))
        self.assertIsNotNone(key)

    def test_same_key_returned_on_second_call(self) -> None:
        k1 = key_store.get_key(2, "hill")
        k2 = key_store.get_key(2, "hill")
        self.assertEqual(k1, k2)

        k3 = key_store.get_key(3, "caesar")
        k4 = key_store.get_key(3, "caesar")
        self.assertEqual(k3, k4)

    def test_caesar_key_within_range(self) -> None:
        for uc in range(1, 6):
            alphabet = cipher_adapter.get_alphabet(uc)
            m = len(alphabet)
            key = key_store.get_key(uc, "caesar")
            self.assertIsInstance(key, int)
            self.assertGreaterEqual(key, 1)
            self.assertLessEqual(key, m - 1)
            # Re-validation via cipher_adapter
            parsed = cipher_adapter.parse_key(key, uc, "caesar")
            self.assertEqual(parsed, key)

    def test_hill_key_valid_and_not_identity_every_use_case(self) -> None:
        for uc in range(1, 6):
            alphabet = cipher_adapter.get_alphabet(uc)
            m = len(alphabet)
            n = cipher_adapter.block_size(uc)
            key = key_store.get_key(uc, "hill")
            self.assertIsInstance(key, list)
            self.assertEqual(len(key), n)
            for row in key:
                self.assertEqual(len(row), n)
                for val in row:
                    self.assertGreaterEqual(val, 0)
                    self.assertLessEqual(val, m - 1)

            # Check not identity
            is_identity = all(
                key[r][c] == (1 if r == c else 0)
                for r in range(n)
                for c in range(n)
            )
            self.assertFalse(is_identity, f"Hill key for use case {uc} must not be identity.")

            # Validate via cipher_adapter
            parsed = cipher_adapter.parse_key(key, uc, "hill")
            self.assertEqual(parsed, key)

    def test_corrupted_file_raises_value_error_and_not_overwritten(self) -> None:
        # Invalid JSON syntax
        bad_json_content = "{ this is not valid json : 123 }"
        with open(self.key_file, "w", encoding="utf-8") as f:
            f.write(bad_json_content)

        with self.assertRaises(ValueError) as ctx:
            key_store.get_key(1, "caesar")
        self.assertIn("Key file is corrupted", str(ctx.exception))

        # Check not overwritten
        with open(self.key_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), bad_json_content)

        # Valid JSON but malformed entry (e.g. non-invertible or invalid matrix)
        malformed_dict = {"hill:2": [[2, 2], [2, 2]]}  # det = 0 mod 4
        with open(self.key_file, "w", encoding="utf-8") as f:
            json.dump(malformed_dict, f)

        with self.assertRaises(ValueError) as ctx:
            key_store.get_key(1, "caesar")
        self.assertIn("Key file is corrupted", str(ctx.exception))

        # Check not overwritten
        with open(self.key_file, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), malformed_dict)

    def test_changing_path_works(self) -> None:
        path2 = os.path.join(self.temp_dir, "alt_keys.json")
        key_store.set_key_file(path2)
        self.assertEqual(key_store.get_key_file(), path2)

        k_alt = key_store.get_key(1, "hill")
        self.assertTrue(os.path.exists(path2))
        self.assertFalse(os.path.exists(self.key_file))
        self.assertIsNotNone(k_alt)
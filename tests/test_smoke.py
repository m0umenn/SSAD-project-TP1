
"""Smoke tests for SSAD Toolkit."""

from __future__ import annotations

import importlib
import unittest


class TestImports(unittest.TestCase):
    """Verify the top-level packages import successfully."""

    def test_packages_import(self) -> None:
        package_names = ["crypto", "passwords", "integrity", "attacks", "gui"]
        for package_name in package_names:
            with self.subTest(package=package_name):
                importlib.import_module(package_name)


class TestCipherFunctions(unittest.TestCase):
    """Verify the implemented ciphers behave as expected."""

    def test_crypto_implementations(self) -> None:
        from crypto import caesar, hill, playfair

        self.assertEqual(caesar.encrypt("HELLO", 3), "KHOOR")
        self.assertEqual(caesar.decrypt("KHOOR", 3), "HELLO")
        self.assertTrue(caesar.validate_key(3))
        self.assertFalse(caesar.validate_key(0))

        self.assertTrue(playfair.validate_key("MONARCHY"))
        self.assertEqual(playfair.encrypt("HELLO", "MONARCHY"), "CFSUPM")
        self.assertEqual(playfair.decrypt("CFSUPM", "MONARCHY"), "HELLO")
        self.assertEqual(playfair.encrypt("MEETME", "MONARCHY"), "CLKLCL")
        self.assertEqual(playfair.decrypt("CLKLCL", "MONARCHY"), "MEETME")

        self.assertTrue(hill.validate_key([[1, 0], [0, 1]]))
        self.assertEqual(hill.encrypt("HELLO", [[1, 0], [0, 1]]), "HELLOX")
        self.assertEqual(hill.decrypt("HELLOX", [[1, 0], [0, 1]], pad_len=1), "HELLO")

    def test_password_and_integrity_stubs(self) -> None:
        from integrity import integrity
        from passwords import brute_force, dictionary

        stub_calls = [
            (brute_force.brute_force, ("target", "abc", 3)),
            (dictionary.dictionary_attack, ("target", ["one", "two"])),
            (integrity.hash_data, ("payload",)),
            (integrity.verify_data, ("payload", "digest")),
        ]

        for func, args in stub_calls:
            with self.subTest(func=func.__name__):
                with self.assertRaises(NotImplementedError):
                    func(*args)

    def test_attack_stubs(self) -> None:
        from attacks import caesar_attack, hill_attack, playfair_attack

        stub_calls = [
            (caesar_attack.brute_force_all_keys, ("CIPHERTEXT",)),
            (caesar_attack.frequency_analysis, ("CIPHERTEXT",)),
            (playfair_attack.digraph_frequency_analysis, ("CIPHERTEXT",)),
            (hill_attack.known_plaintext_attack, ("PLAINTEXT", "CIPHERTEXT", 2)),
        ]

        for func, args in stub_calls:
            with self.subTest(func=func.__name__):
                with self.assertRaises(NotImplementedError):
                    func(*args)
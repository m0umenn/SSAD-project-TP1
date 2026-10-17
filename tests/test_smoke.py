
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


class TestStubFunctions(unittest.TestCase):
    """Verify stub functions still raise NotImplementedError."""

    def test_crypto_stubs(self) -> None:
        from crypto import caesar, hill, playfair

        stub_calls = [
            (caesar.encrypt, ("HELLO", 3)),
            (caesar.decrypt, ("KHOOR", 3)),
            (caesar.validate_key, (3,)),
            (playfair.encrypt, ("HELLO", "KEY")),
            (playfair.decrypt, ("KEY", "KEY")),
            (playfair.validate_key, ("KEY",)),
        ]

        for func, args in stub_calls:
            with self.subTest(func=func.__name__):
                with self.assertRaises(NotImplementedError):
                    func(*args)

        self.assertTrue(hill.validate_key([[1, 0], [0, 1]]))
        self.assertEqual(hill.encrypt("HELLO", [[1, 0], [0, 1]]), "HELLOX")
        self.assertEqual(hill.decrypt("HELLOX", [[1, 0], [0, 1]], pad_len=1), "HELLO")

    def test_password_and_integrity_stubs(self) -> None:
        from integrity import integrity
        from passwords import brute_force, dictionary, generators, protection

        stub_calls = [
            (generators.get_sets, ()),
            (brute_force.brute_force, ("target", "abc", 3)),
            (dictionary.dictionary_attack, ("target", ["one", "two"])),
            (protection.hash_password, ("secret",)),
            (protection.verify_password, ("secret", "hash")),
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
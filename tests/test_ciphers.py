"""Cipher tests for SSAD Toolkit."""

from __future__ import annotations

import unittest

from crypto import caesar, hill, playfair
from tests.vectors import CAESAR_VECTORS, HILL_VECTORS, PLAYFAIR_VECTORS


class TestCaesarCipher(unittest.TestCase):
    """Tests for the Caesar cipher."""

    def test_vectors(self) -> None:
        vectors = [
            {"plaintext": "Meriem", "key": 4, "ciphertext": "Qivmiq"},
            {"plaintext": "Zoe", "key": 3, "ciphertext": "crh"},
            {"plaintext": "xyz", "key": 3, "ciphertext": "ABC"},
            {"plaintext": "XYZ", "key": 3, "ciphertext": "abc"},
            {"plaintext": "abc", "key": -3, "ciphertext": "XYZ"},
            {"plaintext": "Hello World 2026!", "key": 5, "ciphertext": "Mjqqt btwqi 2026!"},
        ]

        for vector in vectors:
            with self.subTest(vector=vector):
                plaintext = vector["plaintext"]
                key = vector["key"]
                ciphertext = vector["ciphertext"]
                self.assertEqual(caesar.encrypt(plaintext, key), ciphertext)
                self.assertEqual(caesar.decrypt(ciphertext, key), plaintext)
                self.assertTrue(caesar.validate_key(key))


class TestPlayfairCipher(unittest.TestCase):
    """Tests for the Playfair cipher."""

    def test_vectors(self) -> None:
        if not PLAYFAIR_VECTORS:
            self.skipTest("no Playfair test vectors yet")

        for vector in PLAYFAIR_VECTORS:
            with self.subTest(vector=vector):
                try:
                    self.assertEqual(playfair.encrypt(vector["plaintext"], vector["key"]), vector["ciphertext"])
                    self.assertEqual(playfair.decrypt(vector["ciphertext"], vector["key"]), vector["plaintext"])
                except NotImplementedError:
                    self.skipTest("not implemented yet")


class TestHillCipher(unittest.TestCase):
    """Tests for the Hill cipher."""

    def test_vectors(self) -> None:
        if not HILL_VECTORS:
            self.skipTest("no Hill test vectors yet")

        for vector in HILL_VECTORS:
            with self.subTest(vector=vector):
                try:
                    plain_text = vector["plaintext"]
                    key = vector["key"]
                    n = len(key)
                    ciphertext = hill.encrypt(plain_text, key)
                    self.assertEqual(ciphertext, vector["ciphertext"])
                    self.assertEqual(
                        hill.decrypt(
                            ciphertext,
                            key,
                            pad_len=hill.padding_length(hill.normalize(plain_text), n),
                        ),
                        hill.normalize(plain_text),
                    )
                except NotImplementedError:
                    self.skipTest("not implemented yet")
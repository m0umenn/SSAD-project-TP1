"""Cipher tests for SSAD Toolkit."""

from __future__ import annotations

import unittest

from crypto import caesar, hill, playfair
from tests.vectors import CAESAR_VECTORS, HILL_VECTORS, PLAYFAIR_VECTORS


class TestCaesarCipher(unittest.TestCase):
    """Tests for the Caesar cipher."""

    def test_vectors(self) -> None:
        if not CAESAR_VECTORS:
            self.skipTest("no Caesar test vectors yet")

        for vector in CAESAR_VECTORS:
            with self.subTest(vector=vector):
                try:
                    self.assertEqual(caesar.encrypt(vector["plaintext"], vector["key"]), vector["ciphertext"])
                    self.assertEqual(caesar.decrypt(vector["ciphertext"], vector["key"]), vector["plaintext"])
                except NotImplementedError:
                    self.skipTest("not implemented yet")


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
                    self.assertEqual(hill.encrypt(vector["plaintext"], vector["key"]), vector["ciphertext"])
                    self.assertEqual(hill.decrypt(vector["ciphertext"], vector["key"]), vector["plaintext"])
                except NotImplementedError:
                    self.skipTest("not implemented yet")
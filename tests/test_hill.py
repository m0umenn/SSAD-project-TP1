"""Unit tests for the Hill cipher."""

from __future__ import annotations

import random
import unittest

from crypto import hill


class TestHillCipherLogic(unittest.TestCase):
    """Tests for Hill cipher validation, round-trips, and padding behavior."""

    def test_validate_key_rejects_invalid_keys(self) -> None:
        invalid_keys = [
            [[2, 4], [1, 3]],
            [[13, 0], [0, 1]],
            [[1, 2], [3, 4]],
            [[1, 2, 3], [4, 5]],
            [[1, 2], [3, "4"]],
        ]

        for key in invalid_keys:
            with self.subTest(key=key):
                self.assertFalse(hill.validate_key(key))

        for key in invalid_keys:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    hill.encrypt("HELLO", key)

    def test_round_trip_randomized_text(self) -> None:
        valid_keys = [
            [[3, 2], [5, 7]],
            [[3, 3], [2, 5]],
            [[6, 24, 1], [13, 16, 10], [20, 17, 15]],
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        ]

        rng = random.Random(7)
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for key in valid_keys:
            for _ in range(12):
                length = rng.randint(1, 20)
                text_parts: list[str] = []
                for _ in range(length):
                    roll = rng.random()
                    if roll < 0.15:
                        text_parts.append(" ")
                    elif roll < 0.30:
                        text_parts.append("!")
                    elif roll < 0.45:
                        text_parts.append(",")
                    elif roll < 0.60:
                        text_parts.append("?")
                    else:
                        text_parts.append(alphabet[rng.randrange(len(alphabet))])
                text = "".join(text_parts)
                normalized = hill.normalize(text)
                if not normalized:
                    continue
                pad_len = hill.padding_length(normalized, len(key))
                ciphertext = hill.encrypt(text, key)
                self.assertEqual(hill.decrypt(ciphertext, key, pad_len=pad_len), normalized)

    def test_padding_length(self) -> None:
        self.assertEqual(hill.padding_length("HELLO", 2), 1)
        self.assertEqual(hill.padding_length("HELLO", 3), 1)
        self.assertEqual(hill.padding_length("HELLO", 4), 3)
        self.assertEqual(hill.padding_length("HELLO", 5), 0)
        self.assertEqual(hill.padding_length("", 3), 0)

    def test_decrypt_rejects_padding_range_and_type(self) -> None:
        key = [[3, 2], [5, 7]]
        ciphertext = hill.encrypt("BONJOUR", key)

        for pad_len in (-1, 2, 5, 99):
            with self.subTest(pad_len=pad_len):
                with self.assertRaisesRegex(ValueError, "Padding length must be between 0 and 1."):
                    hill.decrypt(ciphertext, key, pad_len=pad_len)

        with self.assertRaisesRegex(ValueError, "Padding length must be between 0 and 1."):
            hill.decrypt(ciphertext, key, pad_len="1")

    def test_empty_message_rejected(self) -> None:
        key = [[3, 2], [5, 7]]
        with self.assertRaisesRegex(ValueError, "Message has no letters A-Z."):
            hill.encrypt("", key)
        with self.assertRaisesRegex(ValueError, "Message has no letters A-Z."):
            hill.encrypt("!!!", key)

    def test_box_padding_behavior(self) -> None:
        key = [[3, 2], [5, 7]]
        ciphertext = hill.encrypt("BOX", key)
        self.assertEqual(hill.decrypt(ciphertext, key, pad_len=1), "BOX")
        self.assertEqual(hill.decrypt(ciphertext, key), "BOXX")

    def test_algorithm_vector_3x3(self) -> None:
        key = [[6, 24, 1], [13, 16, 10], [20, 17, 15]]
        ciphertext = hill.encrypt("ALGORITHM", key)
        self.assertEqual(ciphertext, "KCRGONILD")
        self.assertEqual(hill.decrypt(ciphertext, key, pad_len=0), "ALGORITHM")

    def test_decrypt_without_pad_len_keeps_padding(self) -> None:
        key = [[3, 2], [5, 7]]
        ciphertext = hill.encrypt("BONJOUR", key)
        self.assertEqual(hill.decrypt(ciphertext, key), "BONJOURX")

    def test_decrypt_rejects_non_multiple_length(self) -> None:
        key = [[3, 2], [5, 7]]
        with self.assertRaises(ValueError):
            hill.decrypt("ABC", key)


if __name__ == "__main__":
    unittest.main()

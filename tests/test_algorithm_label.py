"""Unit tests for recipient algorithm label verification and ciphertext lengths."""

from __future__ import annotations

import unittest

from crypto import caesar, hill, playfair
from crypto.recipient_check import check_recipient_algorithm


class TestAlgorithmLabel(unittest.TestCase):
    """Test algorithm label matching logic and exact ciphertext lengths."""

    ALGORITHMS = ["caesar", "playfair", "hill"]

    def test_every_algorithm_pair_matching_and_mismatching(self) -> None:
        """Every matching pair is accepted, and every mismatched pair is rejected."""
        for selected in self.ALGORITHMS:
            for received in self.ALGORITHMS:
                with self.subTest(selected=selected, received=received):
                    result = check_recipient_algorithm(selected, received)
                    if selected == received:
                        self.assertTrue(result)
                    else:
                        self.assertFalse(result)

    def test_case_insensitivity_and_formatting(self) -> None:
        """Label checks are case-insensitive and handle whitespace."""
        self.assertTrue(check_recipient_algorithm("Caesar", "caesar"))
        self.assertTrue(check_recipient_algorithm("PLAYFAIR", "playfair"))
        self.assertTrue(check_recipient_algorithm("Hill", "  hill  "))
        self.assertFalse(check_recipient_algorithm("Caesar", "Hill"))

    def test_missing_label_is_accepted(self) -> None:
        """When no label is received (e.g. pasted by hand), the check accepts any algorithm."""
        for algo in self.ALGORITHMS:
            with self.subTest(algo=algo, label=None):
                self.assertTrue(check_recipient_algorithm(algo, None))
            with self.subTest(algo=algo, label=""):
                self.assertTrue(check_recipient_algorithm(algo, ""))

    def test_ciphertext_length_equals_padded_message_length_caesar(self) -> None:
        """Caesar ciphertext length equals the original message length (no padding/marker)."""
        for msg in ["HELLO", "ATTACKATDAWN", "SecretMessage123!"]:
            ct = caesar.encrypt(msg, 3)
            self.assertEqual(len(ct), len(msg))

    def test_ciphertext_length_equals_padded_message_length_playfair(self) -> None:
        """Playfair ciphertext length equals prepared digraph length (no marker added)."""
        key = "MONARCHY"
        # Even length, no adjacent duplicate letters -> length unchanged
        msg_clean = "SECRET"
        ct_clean = playfair.encrypt(msg_clean, key)
        self.assertEqual(len(ct_clean), len(msg_clean))

        # Message requiring padding/filler (e.g. HELLO -> HE LX LO, length 6)
        msg_dup = "HELLO"
        prep_pairs = playfair._prepare(msg_dup)
        ct_dup = playfair.encrypt(msg_dup, key)
        self.assertEqual(len(ct_dup), len(prep_pairs) * 2)
        self.assertEqual(len(ct_dup), 6)

    def test_ciphertext_length_equals_padded_message_length_hill(self) -> None:
        """Hill ciphertext length equals normalized length plus padding (no marker added)."""
        key_2x2 = [[3, 3], [2, 5]]
        key_3x3 = [
            [6, 24, 1],
            [13, 16, 10],
            [20, 17, 15],
        ]

        messages = ["HELP", "BONJOUR", "ALGORITHM", "ATTACKATDAWN"]
        for msg in messages:
            norm = hill.normalize(msg)

            # 2x2 key
            pad_2 = hill.padding_length(norm, 2)
            ct_2 = hill.encrypt(msg, key_2x2)
            self.assertEqual(len(ct_2), len(norm) + pad_2)

            # 3x3 key
            pad_3 = hill.padding_length(norm, 3)
            ct_3 = hill.encrypt(msg, key_3x3)
            self.assertEqual(len(ct_3), len(norm) + pad_3)

    def test_decryption_gui_recipient_label_enforcement(self) -> None:
        """Test DecryptionContent widget behavior with matching and mismatched labels."""
        import tkinter as tk
        from gui.pages.decryption_page import DecryptionContent

        root = tk.Tk()
        root.withdraw()
        try:
            content = DecryptionContent(root)
            raw_msg = "TESTING"
            ct = caesar.encrypt(raw_msg, 3)

            # Transmit with Caesar label
            content.set_incoming_ciphertext(ct, algorithm="caesar")
            self.assertEqual(content._received_algorithm, "caesar")

            # Mismatched selection (Hill) -> error, no decryption
            content.algorithm_var.set("Hill")
            content._decrypt_message()
            self.assertEqual(content.result_var.get(), "")
            self.assertEqual(content.status_var.get(), "You are not the intended recipient.")
            self.assertEqual(str(content.status_label.cget("foreground")), "#c92a2a")

            # Matching selection (Caesar) with correct key -> succeeds
            content.algorithm_var.set("Caesar")
            content.caesar_key_var.set("3")
            content._decrypt_message()
            self.assertEqual(content.result_var.get(), raw_msg)
            self.assertIn("Decryption succeeded!", content.status_var.get())

            # Pasting / typing ciphertext by hand clears received algorithm
            content.ciphertext_var.set("KHOOR")
            self.assertIsNone(content._received_algorithm)

            # Now decrypts with no label check
            content.caesar_key_var.set("3")
            content._decrypt_message()
            self.assertEqual(content.result_var.get(), "HELLO")

            # Decryption error (e.g. invalid key) shows "You are not the intended recipient."
            content.caesar_key_var.set("invalid_key")
            content._decrypt_message()
            self.assertEqual(content.result_var.get(), "")
            self.assertEqual(content.status_var.get(), "You are not the intended recipient.")
            self.assertEqual(str(content.status_label.cget("foreground")), "#c92a2a")
        finally:
            root.destroy()


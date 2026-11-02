"""Tests for transferring encrypted messages to the decryption interfaces."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from gui.app import SSADToolkitApp


class TestDecryptionTransfer(unittest.TestCase):
    def test_ciphertext_and_algorithm_reach_page_and_popup(self) -> None:
        page = Mock()
        popup = Mock()
        popup.winfo_exists.return_value = True
        app = SimpleNamespace(
            shared={},
            _pages={"Decryption": page},
            _decryption_popup=popup,
        )

        SSADToolkitApp.send_ciphertext_to_decryption(app, "KHOOR", "0", "caesar")

        self.assertEqual(app.shared["pending_ciphertext"], "KHOOR")
        self.assertEqual(app.shared["pending_padding"], "0")
        page.set_incoming_ciphertext.assert_called_once_with("KHOOR", "0", "caesar")
        popup.set_incoming_ciphertext.assert_called_once_with("KHOOR", "0", "caesar")


if __name__ == "__main__":
    unittest.main()

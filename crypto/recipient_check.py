"""Recipient algorithm verification helper for Entity B (Decryption).

Verifies whether the recipient's chosen decryption algorithm matches
the algorithm label transmitted from the sender (Entity A).
"""

from __future__ import annotations


def check_recipient_algorithm(selected_algorithm: str, received_label: str | None) -> bool:
    """Verify that the recipient's chosen algorithm matches the transmitted label.

    Parameters:
        selected_algorithm (str): The algorithm selected by the recipient (e.g. 'Caesar').
        received_label (str | None): The algorithm label sent alongside the ciphertext,
            or None / empty string if the ciphertext was entered manually.

    Returns:
        bool: True if no label was received, or if selected_algorithm matches received_label
            (case-insensitive); False otherwise.
    """
    if not received_label:
        return True
    return selected_algorithm.lower().strip() == received_label.lower().strip()


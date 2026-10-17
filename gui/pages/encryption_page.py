"""Encryption and decryption page with Hill cipher support."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

from crypto import hill
from crypto import caesar
from gui.pages.base_page import BasePage


class EncryptionPage(BasePage):
    """Encryption and decryption page shell with Hill cipher implementation."""

    HILL_KEY_DEFAULTS = {
        "2x2": [3, 3, 2, 5],
        "3x3": [6, 24, 1, 13, 16, 10, 20, 17, 15],
    }

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, "Encryption / Decryption", "")

        for child in self.winfo_children():
            if child.winfo_class() == "Label" and child.cget("text") == "":
                child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.algorithm_var = tk.StringVar(value="Hill")
        self.status_var = tk.StringVar(value="")
        self.hill_key_size_var = tk.StringVar(value="2x2")

        self.page_frame = ttk.Frame(self, padding=(10, 6))
        self.page_frame.grid(row=1, column=0, sticky="nsew")
        self.page_frame.columnconfigure(0, weight=1)
        self.page_frame.rowconfigure(0, weight=1)

        self._build_algorithm_selector()
        self._build_algorithm_panel()
        self._render_algorithm_panel()

    def _build_algorithm_selector(self) -> None:
        selector = ttk.Frame(self.page_frame)
        selector.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        selector.columnconfigure(0, weight=0)
        selector.columnconfigure(1, weight=1)

        ttk.Label(selector, text="Algorithm:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        algorithm_combo = ttk.Combobox(
            selector,
            textvariable=self.algorithm_var,
            values=["Caesar", "Playfair", "Hill"],
            state="readonly",
            width=18,
        )
        algorithm_combo.grid(row=0, column=1, sticky="w")
        algorithm_combo.bind("<<ComboboxSelected>>", lambda _event: self._render_algorithm_panel())

        self.status_label = ttk.Label(selector, textvariable=self.status_var, foreground="#0f5132")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def _build_algorithm_panel(self) -> None:
        self.algorithm_panel = ttk.Frame(self.page_frame)
        self.algorithm_panel.grid(row=1, column=0, sticky="nsew")
        self.algorithm_panel.columnconfigure(0, weight=1)

    def _render_algorithm_panel(self) -> None:
        for widget in self.algorithm_panel.winfo_children():
            widget.destroy()

        algorithm = self.algorithm_var.get()
        if algorithm == "Caesar":
            self._build_caesar_panel()
        elif algorithm == "Playfair":
            self._build_playfair_panel()
        else:
            self._build_hill_panel()

    def _build_caesar_panel(self) -> None:
        self.caesar_key_var = tk.StringVar(value="4")
        self.caesar_key_status_var = tk.StringVar(value="")
        self.caesar_ciphertext_var = tk.StringVar(value="")
        self.caesar_result_var = tk.StringVar(value="")

        main = ttk.Frame(self.algorithm_panel)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1, uniform="entities")
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=1, uniform="entities")
        main.rowconfigure(0, weight=1)

        sender = ttk.LabelFrame(main, text="Entity A (sender)", padding=(10, 8))
        sender.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        sender.columnconfigure(0, weight=1)

        ttk.Separator(main, orient="vertical").grid(row=0, column=1, sticky="ns", padx=(0, 6))

        receiver = ttk.LabelFrame(main, text="Entity B (receiver)", padding=(10, 8))
        receiver.grid(row=0, column=2, sticky="nsew")
        receiver.columnconfigure(0, weight=1)

        controls = ttk.Frame(sender)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        controls.columnconfigure(2, weight=1)

        ttk.Label(controls, text="Key n:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(controls, textvariable=self.caesar_key_var, width=8).grid(row=0, column=1, sticky="w")

        self.caesar_key_status_label = ttk.Label(
            controls, textvariable=self.caesar_key_status_var, foreground="#0f5132"
        )
        self.caesar_key_status_label.grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Button(controls, text="Check key", command=self._check_caesar_key).grid(
            row=0, column=3, sticky="w", padx=(10, 0)
        )

        ttk.Label(
            sender,
            text="1 to 51. Negative or L = shift left (e.g. 4, -4, R4, L4).",
            foreground="#5f6f7a",
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        self.caesar_sender_message = tk.Text(sender, height=3, wrap="word")
        self.caesar_sender_message.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        action_row = ttk.Frame(sender)
        action_row.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        action_row.columnconfigure(0, weight=1)
        ttk.Button(action_row, text="Encrypt", command=self._encrypt_caesar_message).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(action_row, text="Send to B", command=self._send_caesar_cipher_to_b).grid(
            row=0, column=1, sticky="e", padx=(10, 0)
        )

        cipher_row = ttk.Frame(sender)
        cipher_row.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(cipher_row, text="Ciphertext:").pack(side="left")
        ttk.Entry(cipher_row, textvariable=self.caesar_ciphertext_var, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(6, 0)
        )

        ttk.Label(sender, text="Shared secret key:").grid(row=5, column=0, sticky="w", pady=(2, 2))
        ttk.Label(sender, textvariable=self.caesar_key_var, justify="left").grid(
            row=6, column=0, sticky="w"
        )

        ttk.Label(receiver, text="Ciphertext:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.caesar_receiver_ciphertext = ttk.Entry(receiver, width=24)
        self.caesar_receiver_ciphertext.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Button(receiver, text="Decrypt", command=self._decrypt_caesar_message).grid(
            row=2, column=0, sticky="w", pady=(0, 10)
        )

        ttk.Label(receiver, text="Result:").grid(row=3, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(receiver, textvariable=self.caesar_result_var, state="readonly").grid(
            row=4, column=0, sticky="ew"
        )

    def _check_caesar_key(self) -> None:
        if caesar.validate_key(self.caesar_key_var.get()):
            self.caesar_key_status_var.set("VALID")
            self.caesar_key_status_label.configure(foreground="#0f5132")
            self._set_status("Key is valid.")
        else:
            self.caesar_key_status_var.set("INVALID")
            self.caesar_key_status_label.configure(foreground="#c92a2a")
            self._set_error_status("Key is invalid: use an integer from 1 to 51 (negative = left).")

    def _encrypt_caesar_message(self) -> None:
        text = self.caesar_sender_message.get("1.0", "end-1c")
        try:
            self.caesar_ciphertext_var.set(caesar.encrypt(text, self.caesar_key_var.get()))
            self._set_status("Encryption complete.")
        except ValueError as exc:
            self.caesar_ciphertext_var.set("")
            self._set_error_status(str(exc))

    def _send_caesar_cipher_to_b(self) -> None:
        self.caesar_receiver_ciphertext.delete(0, tk.END)
        self.caesar_receiver_ciphertext.insert(0, self.caesar_ciphertext_var.get())
        self._set_status("Ciphertext sent to Entity B.")

    def _decrypt_caesar_message(self) -> None:
        try:
            self.caesar_result_var.set(
                caesar.decrypt(self.caesar_receiver_ciphertext.get(), self.caesar_key_var.get())
            )
            self._set_status("Decryption complete.")
        except ValueError as exc:
            self.caesar_result_var.set("")
            self._set_error_status(str(exc))

    def _build_playfair_panel(self) -> None:
        label = ttk.Label(
            self.algorithm_panel,
            text="Not implemented yet",
            foreground="#5f6f7a",
            font=("Segoe UI", 11, "bold"),
        )
        label.grid(row=0, column=0, padx=6, pady=10, sticky="w")

    def _build_hill_panel(self) -> None:
        main = ttk.Frame(self.algorithm_panel)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1, uniform="entities")
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=1, uniform="entities")
        main.rowconfigure(0, weight=1)

        sender = ttk.LabelFrame(main, text="Entity A (sender)", padding=(10, 8))
        sender.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        sender.columnconfigure(0, weight=1)

        separator = ttk.Separator(main, orient="vertical")
        separator.grid(row=0, column=1, sticky="ns", padx=(0, 6))

        receiver = ttk.LabelFrame(main, text="Entity B (receiver)", padding=(10, 8))
        receiver.grid(row=0, column=2, sticky="nsew")
        receiver.columnconfigure(0, weight=1)

        controls = ttk.Frame(sender)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        controls.columnconfigure(0, weight=0)
        controls.columnconfigure(1, weight=0)
        controls.columnconfigure(2, weight=1)

        ttk.Label(controls, text="Key size:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        key_size_combo = ttk.Combobox(
            controls,
            textvariable=self.hill_key_size_var,
            values=["2x2", "3x3"],
            state="readonly",
            width=8,
        )
        key_size_combo.grid(row=0, column=1, sticky="w")
        key_size_combo.bind("<<ComboboxSelected>>", lambda _event: self._rebuild_hill_key_grid())

        self.key_status_var = tk.StringVar(value="")
        self.key_status_label = ttk.Label(controls, textvariable=self.key_status_var, foreground="#0f5132")
        self.key_status_label.grid(row=0, column=2, sticky="w", padx=(10, 0))

        check_button = ttk.Button(controls, text="Check key", command=self._check_hill_key)
        check_button.grid(row=0, column=3, sticky="w", padx=(10, 0))

        self.hill_key_matrix_frame = ttk.Frame(sender)
        self.hill_key_matrix_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.hill_key_matrix_frame.columnconfigure(0, weight=1)

        self.sender_message = tk.Text(sender, height=3, wrap="word")
        self.sender_message.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        action_row = ttk.Frame(sender)
        action_row.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        action_row.columnconfigure(0, weight=1)
        action_row.columnconfigure(1, weight=0)
        action_row.columnconfigure(2, weight=0)

        encrypt_button = ttk.Button(action_row, text="Encrypt", command=self._encrypt_hill_message)
        encrypt_button.grid(row=0, column=0, sticky="w")

        send_button = ttk.Button(action_row, text="Send to B", command=self._send_hill_cipher_to_b)
        send_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

        cipher_row = ttk.Frame(sender)
        cipher_row.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        cipher_row.columnconfigure(0, weight=1)

        ttk.Label(cipher_row, text="Ciphertext:").pack(side="left")
        self.ciphertext_var = tk.StringVar(value="")
        ttk.Entry(cipher_row, textvariable=self.ciphertext_var, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(6, 10)
        )
        self.padding_label_var = tk.StringVar(value="0")
        ttk.Label(cipher_row, text="Padding added:").pack(side="left")
        ttk.Label(cipher_row, textvariable=self.padding_label_var, font=("Segoe UI", 10, "bold")).pack(
            side="left", padx=(4, 0)
        )

        self._rebuild_hill_key_grid()

        ttk.Label(sender, text="Shared secret key:").grid(row=5, column=0, sticky="w", pady=(2, 2))
        ttk.Label(
            sender,
            text=str(self._current_hill_key()),
            wraplength=300,
            justify="left",
        ).grid(row=6, column=0, sticky="w")

        ttk.Label(receiver, text="Ciphertext:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.receiver_ciphertext = ttk.Entry(receiver, width=24)
        self.receiver_ciphertext.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(receiver, text="Padding length (optional):").grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.receiver_padding = ttk.Entry(receiver, width=18)
        self.receiver_padding.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        decrypt_button = ttk.Button(receiver, text="Decrypt", command=self._decrypt_hill_message)
        decrypt_button.grid(row=4, column=0, sticky="w", pady=(0, 10))

        ttk.Label(receiver, text="Result:").grid(row=5, column=0, sticky="w", pady=(0, 4))
        self.receiver_result = tk.StringVar(value="")
        ttk.Entry(receiver, textvariable=self.receiver_result, state="readonly").grid(
            row=6, column=0, sticky="ew"
        )

        self._rebuild_hill_key_grid()

    def _rebuild_hill_key_grid(self) -> None:
        if not hasattr(self, "hill_key_matrix_frame"):
            return

        for widget in self.hill_key_matrix_frame.winfo_children():
            widget.destroy()

        size = 2 if self.hill_key_size_var.get() == "2x2" else 3
        values = self.HILL_KEY_DEFAULTS.get(self.hill_key_size_var.get(), [3, 3, 2, 5])
        self.hill_entries: list[list[ttk.Entry]] = []

        for row_index in range(size):
            row_entries: list[ttk.Entry] = []
            for col_index in range(size):
                value = str(values[row_index * size + col_index])
                entry = ttk.Entry(self.hill_key_matrix_frame, width=4)
                entry.insert(0, value)
                entry.grid(row=row_index, column=col_index, padx=2, pady=2)
                row_entries.append(entry)
            self.hill_entries.append(row_entries)

    def _current_hill_key(self) -> list[list[int]]:
        size = 2 if self.hill_key_size_var.get() == "2x2" else 3
        matrix: list[list[int]] = []
        for row_index in range(size):
            row: list[int] = []
            for col_index in range(size):
                text = self.hill_entries[row_index][col_index].get().strip()
                try:
                    row.append(int(text))
                except ValueError:
                    row.append(0)
            matrix.append(row)
        return matrix

    def _parse_hill_key(self) -> list[list[int]] | None:
        size = 2 if self.hill_key_size_var.get() == "2x2" else 3
        matrix: list[list[int]] = []

        for row_index in range(size):
            row: list[int] = []
            for col_index in range(size):
                entry = self.hill_entries[row_index][col_index].get().strip()
                try:
                    value = int(entry)
                except ValueError:
                    self._set_error_status(f"Entry at row {row_index + 1}, column {col_index + 1} is not an integer.")
                    return None
                row.append(value)
            matrix.append(row)
        return matrix

    def _set_status(self, message: str, is_error: bool = False) -> None:
        self.status_var.set(message)
        self.status_label.configure(foreground="#c92a2a" if is_error else "#0f5132")

    def _set_error_status(self, message: str) -> None:
        self._set_status(message, is_error=True)

    def _check_hill_key(self) -> None:
        key = self._parse_hill_key()
        if key is None:
            return

        try:
            valid = hill.validate_key(key)
            det = hill.determinant(key) % 26
            gcd_value = math.gcd(det, 26)
            if valid:
                self.key_status_var.set("VALID")
                self.key_status_label.configure(foreground="#0f5132")
                self._set_status("Key is valid.")
            else:
                self.key_status_var.set("INVALID")
                self.key_status_label.configure(foreground="#c92a2a")
                self._set_error_status("Key is invalid.")
        except ValueError as exc:
            self.key_status_var.set("INVALID")
            self.key_status_label.configure(foreground="#c92a2a")
            self._set_error_status(str(exc))

    def _encrypt_hill_message(self) -> None:
        key = self._parse_hill_key()
        if key is None:
            return
        try:
            text = self.sender_message.get("1.0", tk.END).strip()
            ciphertext = hill.encrypt(text, key)
            padding = hill.padding_length(hill.normalize(text), len(key))
            self.ciphertext_var.set(ciphertext)
            self.padding_label_var.set(str(padding))
            self._set_status("Encryption complete.")
        except ValueError as exc:
            self._set_error_status(str(exc))
            self.ciphertext_var.set("")
            self.padding_label_var.set("0")

    def _send_hill_cipher_to_b(self) -> None:
        ciphertext = self.ciphertext_var.get().strip()
        pad_len = self.padding_label_var.get().strip()
        self.receiver_ciphertext.delete(0, tk.END)
        self.receiver_ciphertext.insert(0, ciphertext)
        self.receiver_padding.delete(0, tk.END)
        self.receiver_padding.insert(0, pad_len if pad_len and pad_len != "0" else "")
        self._set_status("Ciphertext sent to Entity B.")

    def _decrypt_hill_message(self) -> None:
        key = self._parse_hill_key()
        if key is None:
            return
        ciphertext = self.receiver_ciphertext.get().strip()
        pad_value = self.receiver_padding.get().strip()
        try:
            pad_len = None if pad_value == "" else int(pad_value)
            result = hill.decrypt(ciphertext, key, pad_len=pad_len)
            self.receiver_result.set(result)
            self._set_status("Decryption complete.")
        except ValueError as exc:
            self._set_error_status(str(exc))
            self.receiver_result.set("")

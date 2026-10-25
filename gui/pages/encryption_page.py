"""Encryption and decryption page with Caesar, Playfair, and Hill support."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

from crypto import caesar, hill, playfair
from gui.pages.base_page import BasePage


class EncryptionPage(BasePage):
    """Encryption and decryption page shell with algorithm-specific panels."""

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
        self.hill_receiver_key_size_var = tk.StringVar(value="2x2")

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
        selector.columnconfigure(1, weight=0)
        selector.columnconfigure(2, weight=0)
        selector.columnconfigure(3, weight=1)

        ttk.Label(selector, text="Algorithm:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        algorithm_combo = ttk.Combobox(
            selector,
            textvariable=self.algorithm_var,
            values=["Caesar", "Playfair", "Hill"],
            state="readonly",
            width=18,
        )
        algorithm_combo.grid(row=0, column=1, sticky="w")
        algorithm_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_algorithm_changed())

        ttk.Button(selector, text="Clear keys", command=self.clear_keys).grid(row=0, column=2, sticky="w", padx=(12, 0))

        self.status_label = ttk.Label(selector, textvariable=self.status_var, foreground="#0f5132")
        self.status_label.grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))

    def _on_algorithm_changed(self) -> None:
        self.clear_keys()
        self._render_algorithm_panel()

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
        main = ttk.Frame(self.algorithm_panel)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1, uniform="entities")
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=1, uniform="entities")

        sender = ttk.LabelFrame(main, text="Entity A (sender)", padding=(10, 8))
        sender.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        sender.columnconfigure(0, weight=1)

        separator = ttk.Separator(main, orient="vertical")
        separator.grid(row=0, column=1, sticky="ns", padx=(0, 6))

        receiver = ttk.LabelFrame(main, text="Entity B (receiver)", padding=(10, 8))
        receiver.grid(row=0, column=2, sticky="nsew")
        receiver.columnconfigure(0, weight=1)

        ttk.Label(sender, text="Encryption key:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.caesar_key_var = tk.StringVar(value="")
        ttk.Entry(sender, textvariable=self.caesar_key_var, width=16).grid(row=1, column=0, sticky="ew")

        ttk.Label(sender, text="Message:").grid(row=2, column=0, sticky="w", pady=(10, 4))
        self.caesar_message = tk.Text(sender, height=4, wrap="word")
        self.caesar_message.grid(row=3, column=0, sticky="ew")

        action_row = ttk.Frame(sender)
        action_row.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(action_row, text="Encrypt", command=self._encrypt_caesar_message).pack(side="left")
        ttk.Button(action_row, text="Send to B", command=self._send_caesar_cipher_to_b).pack(side="left", padx=(10, 0))

        ttk.Label(sender, text="Ciphertext:").grid(row=5, column=0, sticky="w", pady=(10, 4))
        self.caesar_ciphertext_var = tk.StringVar(value="")
        ttk.Entry(sender, textvariable=self.caesar_ciphertext_var, state="readonly").grid(row=6, column=0, sticky="ew")

        ttk.Label(receiver, text="Ciphertext:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.caesar_receiver_ciphertext = ttk.Entry(receiver, width=24)
        self.caesar_receiver_ciphertext.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(receiver, text="Key:").grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.caesar_receiver_key_var = tk.StringVar(value="")
        ttk.Entry(receiver, textvariable=self.caesar_receiver_key_var, width=16).grid(row=3, column=0, sticky="ew")

        ttk.Button(receiver, text="Decrypt", command=self._decrypt_caesar_message).grid(row=4, column=0, sticky="w", pady=(8, 8))

        ttk.Label(receiver, text="Result:").grid(row=5, column=0, sticky="w", pady=(0, 4))
        self.caesar_result_var = tk.StringVar(value="")
        ttk.Entry(receiver, textvariable=self.caesar_result_var, state="readonly").grid(row=6, column=0, sticky="ew")

    def _encrypt_caesar_message(self) -> None:
        key_value = self.caesar_key_var.get().strip()
        try:
            key = self._parse_caesar_key(key_value)
        except ValueError as exc:
            self._set_error_status(str(exc))
            return

        plaintext = self.caesar_message.get("1.0", tk.END).strip()
        try:
            ciphertext = caesar.encrypt(plaintext, key)
            self.caesar_ciphertext_var.set(ciphertext)
            self._set_status("Encryption complete.")
        except ValueError as exc:
            self._set_error_status(str(exc))
            self.caesar_ciphertext_var.set("")

    def _send_caesar_cipher_to_b(self) -> None:
        ciphertext = self.caesar_ciphertext_var.get().strip()
        self.caesar_receiver_ciphertext.delete(0, tk.END)
        self.caesar_receiver_ciphertext.insert(0, ciphertext)
        self._set_status("Ciphertext sent to Entity B.")

    def _decrypt_caesar_message(self) -> None:
        ciphertext = self.caesar_receiver_ciphertext.get().strip()
        key_value = self.caesar_receiver_key_var.get().strip()
        try:
            key = self._parse_caesar_key(key_value)
            plaintext = caesar.decrypt(ciphertext, key)
            self.caesar_result_var.set(plaintext)
            self._set_status("Decryption complete.")
        except ValueError as exc:
            self._set_error_status(str(exc))
            self.caesar_result_var.set("")

    def _parse_caesar_key(self, key_value: str):
        if key_value == "":
            raise ValueError("A Caesar key is required.")
        if caesar.validate_key(key_value):
            return key_value
        try:
            return int(key_value)
        except ValueError as exc:
            raise ValueError("Key must be an integer or left/right notation like 'L4' or 'R4'.") from exc

    def _build_playfair_panel(self) -> None:
        self.playfair_key_var = tk.StringVar(value="")
        self.playfair_key_status_var = tk.StringVar(value="")
        self.playfair_ciphertext_var = tk.StringVar(value="")
        self.playfair_result_var = tk.StringVar(value="")
        self.playfair_matrix_var = tk.StringVar(value="")

        main = ttk.Frame(self.algorithm_panel)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1, uniform="entities")
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=1, uniform="entities")

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
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=0)

        ttk.Label(controls, text="Keyword:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(controls, textvariable=self.playfair_key_var, width=20).grid(row=0, column=1, sticky="ew")
        self.playfair_key_status_label = ttk.Label(controls, textvariable=self.playfair_key_status_var, foreground="#0f5132")
        self.playfair_key_status_label.grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Button(controls, text="Check key", command=self._check_playfair_key).grid(row=0, column=3, sticky="w", padx=(10, 0))

        ttk.Label(sender, text="Type the keyword manually. Letters only, spaces ignored, J treated as I.", foreground="#5f6f7a").grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.playfair_message = tk.Text(sender, height=4, wrap="word")
        self.playfair_message.grid(row=2, column=0, sticky="ew")

        action_row = ttk.Frame(sender)
        action_row.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(action_row, text="Encrypt", command=self._encrypt_playfair_message).pack(side="left")
        ttk.Button(action_row, text="Send to B", command=self._send_playfair_cipher_to_b).pack(side="left", padx=(10, 0))

        ttk.Label(sender, text="Ciphertext:").grid(row=4, column=0, sticky="w", pady=(10, 4))
        ttk.Entry(sender, textvariable=self.playfair_ciphertext_var, state="readonly").grid(row=5, column=0, sticky="ew")

        ttk.Label(sender, text="5x5 matrix:").grid(row=6, column=0, sticky="w", pady=(10, 4))
        ttk.Label(sender, textvariable=self.playfair_matrix_var, font=("Courier New", 10), justify="left").grid(row=7, column=0, sticky="w")

        ttk.Label(receiver, text="Ciphertext:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.playfair_receiver_ciphertext = ttk.Entry(receiver, width=24)
        self.playfair_receiver_ciphertext.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(receiver, text="Keyword:").grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.playfair_receiver_key_var = tk.StringVar(value="")
        ttk.Entry(receiver, textvariable=self.playfair_receiver_key_var, width=20).grid(row=3, column=0, sticky="ew")

        ttk.Button(receiver, text="Decrypt", command=self._decrypt_playfair_message).grid(row=4, column=0, sticky="w", pady=(8, 8))

        ttk.Label(receiver, text="Result:").grid(row=5, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(receiver, textvariable=self.playfair_result_var, state="readonly").grid(row=6, column=0, sticky="ew")

        self._update_playfair_matrix()

    def _update_playfair_matrix(self) -> None:
        key = self.playfair_key_var.get().strip()
        if playfair.validate_key(key):
            matrix = playfair._build_matrix(key)
            self.playfair_matrix_var.set("\n".join(" ".join(row) for row in matrix))
        else:
            self.playfair_matrix_var.set("(invalid key)")

    def _check_playfair_key(self) -> None:
        self._update_playfair_matrix()
        if playfair.validate_key(self.playfair_key_var.get().strip()):
            self.playfair_key_status_var.set("VALID")
            self.playfair_key_status_label.configure(foreground="#0f5132")
            self._set_status("Key is valid.")
        else:
            self.playfair_key_status_var.set("INVALID")
            self.playfair_key_status_label.configure(foreground="#c92a2a")
            self._set_error_status("Key is invalid: use a non-empty string of letters.")

    def _encrypt_playfair_message(self) -> None:
        key = self.playfair_key_var.get().strip()
        if not key:
            self._set_error_status("A Playfair key is required.")
            return
        self._update_playfair_matrix()
        plaintext = self.playfair_message.get("1.0", tk.END).strip()
        try:
            ciphertext = playfair.encrypt(plaintext, key)
            self.playfair_ciphertext_var.set(ciphertext)
            self._set_status("Encryption complete.")
        except ValueError as exc:
            self._set_error_status(str(exc))
            self.playfair_ciphertext_var.set("")

    def _send_playfair_cipher_to_b(self) -> None:
        ciphertext = self.playfair_ciphertext_var.get().strip()
        self.playfair_receiver_ciphertext.delete(0, tk.END)
        self.playfair_receiver_ciphertext.insert(0, ciphertext)
        self._set_status("Ciphertext sent to Entity B.")

    def _decrypt_playfair_message(self) -> None:
        ciphertext = self.playfair_receiver_ciphertext.get().strip()
        key = self.playfair_receiver_key_var.get().strip()
        if not key:
            self._set_error_status("A Playfair key is required.")
            return
        try:
            plaintext = playfair.decrypt(ciphertext, key)
            self.playfair_result_var.set(plaintext)
            self._set_status("Decryption complete.")
        except ValueError as exc:
            self._set_error_status(str(exc))
            self.playfair_result_var.set("")

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
        controls.columnconfigure(3, weight=0)

        ttk.Label(controls, text="Key size:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        key_size_combo = ttk.Combobox(
            controls,
            textvariable=self.hill_key_size_var,
            values=["2x2", "3x3"],
            state="readonly",
            width=8,
        )
        key_size_combo.grid(row=0, column=1, sticky="w")
        key_size_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_sender_hill_size_changed())

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

        clear_button = ttk.Button(action_row, text="Clear keys", command=self.clear_keys)
        clear_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

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

        receiver_controls = ttk.Frame(receiver)
        receiver_controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        receiver_controls.columnconfigure(0, weight=0)
        receiver_controls.columnconfigure(1, weight=0)
        receiver_controls.columnconfigure(2, weight=1)
        receiver_controls.columnconfigure(3, weight=0)

        ttk.Label(receiver_controls, text="Key size:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        receiver_key_size_combo = ttk.Combobox(
            receiver_controls,
            textvariable=self.hill_receiver_key_size_var,
            values=["2x2", "3x3"],
            state="readonly",
            width=8,
        )
        receiver_key_size_combo.grid(row=0, column=1, sticky="w")
        receiver_key_size_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_receiver_hill_size_changed())

        self.receiver_key_status_var = tk.StringVar(value="")
        self.receiver_key_status_label = ttk.Label(
            receiver_controls, textvariable=self.receiver_key_status_var, foreground="#0f5132"
        )
        self.receiver_key_status_label.grid(row=0, column=2, sticky="w", padx=(10, 0))

        receiver_check_button = ttk.Button(receiver_controls, text="Check key", command=self._check_hill_receiver_key)
        receiver_check_button.grid(row=0, column=3, sticky="w", padx=(10, 0))

        self.hill_receiver_key_matrix_frame = ttk.Frame(receiver)
        self.hill_receiver_key_matrix_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.hill_receiver_key_matrix_frame.columnconfigure(0, weight=1)

        ttk.Label(receiver, text="Ciphertext:").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.receiver_ciphertext = ttk.Entry(receiver, width=24)
        self.receiver_ciphertext.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        padding_row = ttk.Frame(receiver)
        padding_row.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(padding_row, text="Padding length (optional):").pack(side="left", padx=(0, 8))
        self.receiver_padding = ttk.Entry(padding_row, width=8)
        self.receiver_padding.pack(side="left")

        decrypt_button = ttk.Button(receiver, text="Decrypt", command=self._decrypt_hill_message)
        decrypt_button.grid(row=5, column=0, sticky="w", pady=(4, 6))

        ttk.Label(receiver, text="Result:").grid(row=6, column=0, sticky="w", pady=(0, 4))
        self.receiver_result = tk.StringVar(value="")
        ttk.Entry(receiver, textvariable=self.receiver_result, state="readonly").grid(
            row=7, column=0, sticky="ew"
        )

        self._rebuild_hill_grids()

    def _rebuild_hill_grids(self) -> None:
        self._rebuild_hill_key_grid()
        self._rebuild_hill_receiver_key_grid()

    def _on_sender_hill_size_changed(self) -> None:
        self.hill_receiver_key_size_var.set(self.hill_key_size_var.get())
        self._rebuild_hill_grids()

    def _on_receiver_hill_size_changed(self) -> None:
        self._rebuild_hill_grids()

    def _rebuild_hill_key_grid(self) -> None:
        if not hasattr(self, "hill_key_matrix_frame"):
            return

        for widget in self.hill_key_matrix_frame.winfo_children():
            widget.destroy()

        size = 2 if self.hill_key_size_var.get() == "2x2" else 3
        self.hill_entries: list[list[ttk.Entry]] = []

        for row_index in range(size):
            row_entries: list[ttk.Entry] = []
            for col_index in range(size):
                entry = ttk.Entry(self.hill_key_matrix_frame, width=4)
                entry.grid(row=row_index, column=col_index, padx=2, pady=2)
                row_entries.append(entry)
            self.hill_entries.append(row_entries)

        self.key_status_var.set("")
        self.key_status_label.configure(foreground="#0f5132")

    def _rebuild_hill_receiver_key_grid(self) -> None:
        if not hasattr(self, "hill_receiver_key_matrix_frame"):
            return

        for widget in self.hill_receiver_key_matrix_frame.winfo_children():
            widget.destroy()

        size = 2 if self.hill_receiver_key_size_var.get() == "2x2" else 3
        self.hill_receiver_entries: list[list[ttk.Entry]] = []

        for row_index in range(size):
            row_entries: list[ttk.Entry] = []
            for col_index in range(size):
                entry = ttk.Entry(self.hill_receiver_key_matrix_frame, width=4)
                entry.grid(row=row_index, column=col_index, padx=2, pady=2)
                row_entries.append(entry)
            self.hill_receiver_entries.append(row_entries)

        self.receiver_key_status_var.set("")
        self.receiver_key_status_label.configure(foreground="#0f5132")

    def _parse_hill_key(self) -> list[list[int]] | None:
        size = 2 if self.hill_key_size_var.get() == "2x2" else 3
        matrix: list[list[int]] = []

        for row_index in range(size):
            row: list[int] = []
            for col_index in range(size):
                entry = self.hill_entries[row_index][col_index].get().strip()
                if entry == "":
                    self._set_error_status(f"Entry at row {row_index + 1}, column {col_index + 1} is empty.")
                    return None
                try:
                    value = int(entry)
                except ValueError:
                    self._set_error_status(f"Entry at row {row_index + 1}, column {col_index + 1} is not an integer.")
                    return None
                row.append(value)
            matrix.append(row)
        return matrix

    def _parse_hill_receiver_key(self) -> list[list[int]] | None:
        size = 2 if self.hill_receiver_key_size_var.get() == "2x2" else 3
        matrix: list[list[int]] = []

        for row_index in range(size):
            row: list[int] = []
            for col_index in range(size):
                entry = self.hill_receiver_entries[row_index][col_index].get().strip()
                if entry == "":
                    self._set_error_status(f"Entry at row {row_index + 1}, column {col_index + 1} is empty.")
                    return None
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

    def _check_hill_receiver_key(self) -> None:
        key = self._parse_hill_receiver_key()
        if key is None:
            return

        try:
            valid = hill.validate_key(key)
            if valid:
                self.receiver_key_status_var.set("VALID")
                self.receiver_key_status_label.configure(foreground="#0f5132")
                self._set_status("Key is valid.")
            else:
                self.receiver_key_status_var.set("INVALID")
                self.receiver_key_status_label.configure(foreground="#c92a2a")
                self._set_error_status("Key is invalid.")
        except ValueError as exc:
            self.receiver_key_status_var.set("INVALID")
            self.receiver_key_status_label.configure(foreground="#c92a2a")
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
        key = self._parse_hill_receiver_key()
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

    def clear_keys(self) -> None:
        """Clear all key fields across sender and receiver."""
        if hasattr(self, "caesar_key_var"):
            self.caesar_key_var.set("")
        if hasattr(self, "caesar_receiver_key_var"):
            self.caesar_receiver_key_var.set("")
        if hasattr(self, "playfair_key_var"):
            self.playfair_key_var.set("")
            self._update_playfair_matrix()
        if hasattr(self, "playfair_key_status_var"):
            self.playfair_key_status_var.set("")
        if hasattr(self, "playfair_receiver_key_var"):
            self.playfair_receiver_key_var.set("")
        if hasattr(self, "hill_entries"):
            for row in self.hill_entries:
                for entry in row:
                    entry.delete(0, tk.END)
        if hasattr(self, "hill_receiver_entries"):
            for row in self.hill_receiver_entries:
                for entry in row:
                    entry.delete(0, tk.END)
        if hasattr(self, "key_status_var"):
            self.key_status_var.set("")
        if hasattr(self, "receiver_key_status_var"):
            self.receiver_key_status_var.set("")
        self._set_status("Keys cleared.")

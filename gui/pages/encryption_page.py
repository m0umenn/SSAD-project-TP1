"""Encryption page for Entity A (Sender).

Provides an encryption interface for classical ciphers (Caesar, Playfair, Hill).
Encrypted messages can be transmitted directly to the separate Decryption window (Entity B)
without revealing the algorithm or key, ensuring secure end-to-end recipient verification.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from crypto import caesar, hill, playfair
from gui.pages.base_page import BasePage


class EncryptionPage(BasePage):
    """Sender-side encryption interface for Entity A."""

    HILL_KEY_DEFAULTS = {
        "2x2": [3, 3, 2, 5],
        "3x3": [6, 24, 1, 13, 16, 10, 20, 17, 15],
    }

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, "Encryption", "")

        for child in self.winfo_children():
            if child.winfo_class() == "Label" and child.cget("text") == "":
                child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.algorithm_var = tk.StringVar(value="Hill")
        self.status_var = tk.StringVar(value="")
        self.hill_key_size_var = tk.StringVar(value="2x2")

        # Caesar state
        self.caesar_key_var = tk.StringVar(value="")
        self.caesar_key_status_var = tk.StringVar(value="")
        self.caesar_ciphertext_var = tk.StringVar(value="")

        # Playfair state
        self.playfair_key_var = tk.StringVar(value="")
        self.playfair_key_status_var = tk.StringVar(value="")
        self.playfair_ciphertext_var = tk.StringVar(value="")
        self.playfair_matrix_var = tk.StringVar(value="")

        # Hill state
        self.hill_ciphertext_var = tk.StringVar(value="")
        self.hill_padding_var = tk.StringVar(value="0")
        self.hill_key_status_var = tk.StringVar(value="")
        self.hill_entries: list[list[ttk.Entry]] = []

        self.page_frame = ttk.Frame(self, padding=(10, 6))
        self.page_frame.grid(row=1, column=0, sticky="nsew")
        self.page_frame.columnconfigure(0, weight=1)
        self.page_frame.rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_algorithm_panel()
        self._render_algorithm_panel()

    def _build_top_bar(self) -> None:
        top = ttk.Frame(self.page_frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Algorithm:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        algorithm_combo = ttk.Combobox(
            top,
            textvariable=self.algorithm_var,
            values=["Caesar", "Playfair", "Hill"],
            state="readonly",
            width=18,
        )
        algorithm_combo.grid(row=0, column=1, sticky="w")
        algorithm_combo.bind("<<ComboboxSelected>>", lambda _e: self._render_algorithm_panel())

        ttk.Button(
            top,
            text="Open Separate Decryption Window (Entity B)",
            command=self._open_decryption_window,
        ).grid(row=0, column=2, sticky="e")

        self.status_label = ttk.Label(top, textvariable=self.status_var, foreground="#0f5132")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

    def _build_algorithm_panel(self) -> None:
        self.algorithm_panel = ttk.Frame(self.page_frame)
        self.algorithm_panel.grid(row=1, column=0, sticky="nsew")
        self.algorithm_panel.columnconfigure(0, weight=1)

    def _render_algorithm_panel(self) -> None:
        for w in self.algorithm_panel.winfo_children():
            w.destroy()

        algo = self.algorithm_var.get()
        if algo == "Caesar":
            self._build_caesar_panel()
        elif algo == "Playfair":
            self._build_playfair_panel()
        else:
            self._build_hill_panel()

    # --- Caesar Panel ---

    def _build_caesar_panel(self) -> None:
        frame = ttk.LabelFrame(self.algorithm_panel, text="Caesar Cipher — Entity A (Sender)", padding=(12, 10))
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        key_row = ttk.Frame(frame)
        key_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        key_row.columnconfigure(2, weight=1)

        ttk.Label(key_row, text="Shift key n:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(key_row, textvariable=self.caesar_key_var, width=10).grid(row=0, column=1, sticky="w")

        self.caesar_key_status_label = ttk.Label(
            key_row, textvariable=self.caesar_key_status_var, foreground="#0f5132"
        )
        self.caesar_key_status_label.grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Button(key_row, text="Check key", command=self._check_caesar_key).grid(
            row=0, column=3, sticky="e"
        )

        ttk.Label(
            frame,
            text="1 to 51. Negative or L = shift left (e.g. 4, -4, R4, L4).",
            foreground="#5f6f7a",
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        ttk.Label(frame, text="Plaintext Message:").grid(row=2, column=0, sticky="w", pady=(4, 2))
        self.caesar_message_text = tk.Text(frame, height=4, wrap="word")
        self.caesar_message_text.grid(row=3, column=0, sticky="ew", pady=(0, 8))


        btn_row = ttk.Frame(frame)
        btn_row.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(btn_row, text="Encrypt", command=self._encrypt_caesar_message).pack(side="left")
        ttk.Button(
            btn_row,
            text="Send to Decryption Window (Entity B)",
            command=self._send_caesar_to_decryption,
        ).pack(side="left", padx=(10, 0))

        cipher_row = ttk.Frame(frame)
        cipher_row.grid(row=5, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(cipher_row, text="Ciphertext:").pack(side="left", padx=(0, 6))
        ttk.Entry(cipher_row, textvariable=self.caesar_ciphertext_var, state="readonly").pack(
            side="left", fill="x", expand=True
        )

    def _check_caesar_key(self) -> None:
        if caesar.validate_key(self.caesar_key_var.get()):
            self.caesar_key_status_var.set("VALID")
            self.caesar_key_status_label.configure(foreground="#0f5132")
            self._set_status("Caesar key is valid.")
        else:
            self.caesar_key_status_var.set("INVALID")
            self.caesar_key_status_label.configure(foreground="#c92a2a")
            self._set_error_status("Invalid Caesar key. Must be an integer 1..51.")

    def _encrypt_caesar_message(self) -> None:
        text = self.caesar_message_text.get("1.0", "end-1c")
        try:
            ct = caesar.encrypt(text, self.caesar_key_var.get())
            self.caesar_ciphertext_var.set(ct)
            self._set_status("Encryption complete.")
        except Exception as exc:
            self.caesar_ciphertext_var.set("")
            self._set_error_status(str(exc))

    def _send_caesar_to_decryption(self) -> None:
        ct = self.caesar_ciphertext_var.get()
        if not ct:
            self._set_error_status("Encrypt a message first before sending.")
            return
        self._transmit_ciphertext(ct)

    # --- Playfair Panel ---

    def _build_playfair_panel(self) -> None:
        frame = ttk.LabelFrame(self.algorithm_panel, text="Playfair Cipher — Entity A (Sender)", padding=(12, 10))
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        key_row = ttk.Frame(frame)
        key_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        key_row.columnconfigure(2, weight=1)

        ttk.Label(key_row, text="Keyword:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(key_row, textvariable=self.playfair_key_var, width=18).grid(
            row=0, column=1, sticky="w"
        )

        self.playfair_key_status_label = ttk.Label(
            key_row, textvariable=self.playfair_key_status_var, foreground="#0f5132"
        )
        self.playfair_key_status_label.grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Button(key_row, text="Check key", command=self._check_playfair_key).grid(
            row=0, column=3, sticky="e"
        )

        ttk.Label(
            frame,
            text="Letters only (spaces ignored). J is combined with I.",
            foreground="#5f6f7a",
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        matrix_frame = ttk.Frame(frame)
        matrix_frame.grid(row=2, column=0, sticky="w", pady=(0, 6))
        ttk.Label(matrix_frame, text="Key Square (5x5 matrix):").pack(anchor="w")
        ttk.Label(
            matrix_frame,
            textvariable=self.playfair_matrix_var,
            font=("Courier New", 9),
            justify="left",
        ).pack(anchor="w")

        self.playfair_key_var.trace_add("write", lambda *_: self._update_playfair_matrix())
        self._update_playfair_matrix()

        ttk.Label(frame, text="Plaintext Message:").grid(row=3, column=0, sticky="w", pady=(4, 2))
        self.playfair_message_text = tk.Text(frame, height=4, wrap="word")
        self.playfair_message_text.grid(row=4, column=0, sticky="ew", pady=(0, 8))


        btn_row = ttk.Frame(frame)
        btn_row.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(btn_row, text="Encrypt", command=self._encrypt_playfair_message).pack(side="left")
        ttk.Button(
            btn_row,
            text="Send to Decryption Window (Entity B)",
            command=self._send_playfair_to_decryption,
        ).pack(side="left", padx=(10, 0))

        cipher_row = ttk.Frame(frame)
        cipher_row.grid(row=6, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(cipher_row, text="Ciphertext:").pack(side="left", padx=(0, 6))
        ttk.Entry(cipher_row, textvariable=self.playfair_ciphertext_var, state="readonly").pack(
            side="left", fill="x", expand=True
        )

    def _update_playfair_matrix(self) -> None:
        key = self.playfair_key_var.get()
        if not key.strip():
            self.playfair_matrix_var.set("(enter a keyword)")
        elif playfair.validate_key(key):
            rows = playfair._build_matrix(key)
            self.playfair_matrix_var.set("\n".join(" ".join(row) for row in rows))
        else:
            self.playfair_matrix_var.set("(invalid keyword)")

    def _check_playfair_key(self) -> None:
        if playfair.validate_key(self.playfair_key_var.get()):
            self.playfair_key_status_var.set("VALID")
            self.playfair_key_status_label.configure(foreground="#0f5132")
            self._set_status("Playfair keyword is valid.")
        else:
            self.playfair_key_status_var.set("INVALID")
            self.playfair_key_status_label.configure(foreground="#c92a2a")
            self._set_error_status("Invalid Playfair keyword. Must contain letters.")

    def _encrypt_playfair_message(self) -> None:
        text = self.playfair_message_text.get("1.0", "end-1c")
        try:
            ct = playfair.encrypt(text, self.playfair_key_var.get())
            self.playfair_ciphertext_var.set(ct)
            self._set_status("Encryption complete.")
        except Exception as exc:
            self.playfair_ciphertext_var.set("")
            self._set_error_status(str(exc))

    def _send_playfair_to_decryption(self) -> None:
        ct = self.playfair_ciphertext_var.get()
        if not ct:
            self._set_error_status("Encrypt a message first before sending.")
            return
        self._transmit_ciphertext(ct)

    # --- Hill Panel ---

    def _build_hill_panel(self) -> None:
        frame = ttk.LabelFrame(self.algorithm_panel, text="Hill Cipher — Entity A (Sender)", padding=(12, 10))
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        key_row = ttk.Frame(frame)
        key_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        key_row.columnconfigure(2, weight=1)

        ttk.Label(key_row, text="Key size:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        key_size_combo = ttk.Combobox(
            key_row,
            textvariable=self.hill_key_size_var,
            values=["2x2", "3x3"],
            state="readonly",
            width=8,
        )
        key_size_combo.grid(row=0, column=1, sticky="w")
        key_size_combo.bind("<<ComboboxSelected>>", lambda _e: self._rebuild_hill_key_grid())

        self.hill_key_status_label = ttk.Label(
            key_row, textvariable=self.hill_key_status_var, foreground="#0f5132"
        )
        self.hill_key_status_label.grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Button(key_row, text="Check key", command=self._check_hill_key).grid(
            row=0, column=3, sticky="e"
        )

        self.hill_key_matrix_frame = ttk.Frame(frame)
        self.hill_key_matrix_frame.grid(row=1, column=0, sticky="w", pady=(0, 6))

        self._rebuild_hill_key_grid()

        ttk.Label(frame, text="Plaintext Message:").grid(row=2, column=0, sticky="w", pady=(4, 2))
        self.hill_message_text = tk.Text(frame, height=4, wrap="word")
        self.hill_message_text.grid(row=3, column=0, sticky="ew", pady=(0, 8))


        btn_row = ttk.Frame(frame)
        btn_row.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(btn_row, text="Encrypt", command=self._encrypt_hill_message).pack(side="left")
        ttk.Button(
            btn_row,
            text="Send to Decryption Window (Entity B)",
            command=self._send_hill_to_decryption,
        ).pack(side="left", padx=(10, 0))

        cipher_row = ttk.Frame(frame)
        cipher_row.grid(row=5, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(cipher_row, text="Ciphertext:").pack(side="left", padx=(0, 6))
        ttk.Entry(cipher_row, textvariable=self.hill_ciphertext_var, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(0, 10)
        )
        ttk.Label(cipher_row, text="Padding added:").pack(side="left")
        ttk.Label(
            cipher_row,
            textvariable=self.hill_padding_var,
            font=("Segoe UI", 10, "bold"),
            foreground="#243447",
        ).pack(side="left", padx=(4, 0))

    def _rebuild_hill_key_grid(self) -> None:
        if not hasattr(self, "hill_key_matrix_frame"):
            return
        for w in self.hill_key_matrix_frame.winfo_children():
            w.destroy()

        size_label = self.hill_key_size_var.get()
        size = 2 if size_label == "2x2" else 3

        self.hill_entries = []
        for r in range(size):
            row_entries: list[ttk.Entry] = []
            for c in range(size):
                e = ttk.Entry(self.hill_key_matrix_frame, width=5, justify="center")
                e.grid(row=r, column=c, padx=3, pady=3)
                row_entries.append(e)
            self.hill_entries.append(row_entries)

    def _parse_hill_key(self) -> list[list[int]]:
        size = len(self.hill_entries)
        matrix: list[list[int]] = []
        for r in range(size):
            row_vals: list[int] = []
            for c in range(size):
                raw = self.hill_entries[r][c].get().strip()
                if not raw:
                    raise ValueError(f"Matrix cell ({r+1},{c+1}) is empty.")
                try:
                    row_vals.append(int(raw))
                except ValueError as exc:
                    raise ValueError(f"Matrix cell ({r+1},{c+1}) must be integer, got: {raw!r}") from exc
            matrix.append(row_vals)
        return matrix

    def _check_hill_key(self) -> None:
        try:
            mat = self._parse_hill_key()
            if hill.validate_key(mat):
                self.hill_key_status_var.set("VALID")
                self.hill_key_status_label.configure(foreground="#0f5132")
                self._set_status("Hill key matrix is valid and invertible modulo 26.")
            else:
                self.hill_key_status_var.set("INVALID")
                self.hill_key_status_label.configure(foreground="#c92a2a")
                self._set_error_status("Hill key matrix determinant is not coprime with 26.")
        except ValueError as exc:
            self.hill_key_status_var.set("INVALID")
            self.hill_key_status_label.configure(foreground="#c92a2a")
            self._set_error_status(str(exc))

    def _encrypt_hill_message(self) -> None:
        text = self.hill_message_text.get("1.0", "end-1c")
        try:
            mat = self._parse_hill_key()
            ct = hill.encrypt(text, mat)
            n = len(mat)
            norm = hill.normalize(text)
            pad_len = hill.padding_length(norm, n)
            self.hill_ciphertext_var.set(ct)
            self.hill_padding_var.set(str(pad_len))
            self._set_status("Encryption complete.")
        except Exception as exc:
            self.hill_ciphertext_var.set("")
            self.hill_padding_var.set("0")
            self._set_error_status(str(exc))

    def _send_hill_to_decryption(self) -> None:
        ct = self.hill_ciphertext_var.get()
        if not ct:
            self._set_error_status("Encrypt a message first before sending.")
            return
        self._transmit_ciphertext(ct, padding=self.hill_padding_var.get())

    # --- Communication with Decryption Window ---

    def _transmit_ciphertext(self, ciphertext: str, padding: str = "") -> None:
        top: Any = self.winfo_toplevel()
        if hasattr(top, "send_ciphertext_to_decryption"):
            top.send_ciphertext_to_decryption(ciphertext, padding)
        self._set_status("Ciphertext sent to Entity B (Decryption window).")

    def _open_decryption_window(self) -> None:
        top: Any = self.winfo_toplevel()
        if hasattr(top, "open_separate_decryption_window"):
            top.open_separate_decryption_window()
        elif hasattr(top, "show_page"):
            top.show_page("Decryption")

    def _set_status(self, msg: str, is_error: bool = False) -> None:
        self.status_var.set(msg)
        self.status_label.configure(foreground="#c92a2a" if is_error else "#0f5132")

    def _set_error_status(self, msg: str) -> None:
        self._set_status(msg, is_error=True)

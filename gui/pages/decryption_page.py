"""Decryption page and separate window for Entity B (receiver).

Provides an independent decryption interface where the recipient must manually
select the cipher algorithm and enter the secret key to decrypt the received message,
acting as a security verification layer to confirm the recipient's identity.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from crypto import caesar, hill, playfair
from gui.pages.base_page import BasePage


class DecryptionContent(ttk.Frame):
    """Reusable decryption content panel (used in both page tab and popup window)."""

    def __init__(self, parent: tk.Widget, is_toplevel: bool = False) -> None:
        super().__init__(parent)
        self.is_toplevel = is_toplevel

        self.algorithm_var = tk.StringVar(value="Caesar")
        self.status_var = tk.StringVar(
            value="Ready. Waiting for ciphertext or enter your own."
        )
        self.ciphertext_var = tk.StringVar(value="")
        self.result_var = tk.StringVar(value="")

        # Caesar state
        self.caesar_key_var = tk.StringVar(value="")
        self.caesar_key_status_var = tk.StringVar(value="")

        # Playfair state
        self.playfair_key_var = tk.StringVar(value="")
        self.playfair_key_status_var = tk.StringVar(value="")
        self.playfair_matrix_var = tk.StringVar(value="")

        # Hill state
        self.hill_key_size_var = tk.StringVar(value="2x2")
        self.hill_key_status_var = tk.StringVar(value="")
        self.hill_padding_var = tk.StringVar(value="")
        self.hill_key_entries: list[list[ttk.Entry]] = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._build_header()
        self._build_ciphertext_section()
        self._build_key_section()
        self._build_result_section()
        self._render_key_controls()

    def _build_header(self) -> None:
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="Decryption (Entity B - Receiver)",
            font=("Segoe UI", 12, "bold"),
            foreground="#243447",
        ).grid(row=0, column=0, sticky="w")

        if not self.is_toplevel:
            ttk.Button(
                header,
                text="Pop Out to Separate Window",
                command=self._pop_out_window,
            ).grid(row=0, column=2, sticky="e")

        # Algorithm selection
        algo_row = ttk.Frame(self)
        algo_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        algo_row.columnconfigure(1, weight=1)

        ttk.Label(algo_row, text="Recipient Algorithm Choice:").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.algo_combo = ttk.Combobox(
            algo_row,
            textvariable=self.algorithm_var,
            values=["Caesar", "Playfair", "Hill"],
            state="readonly",
            width=18,
        )
        self.algo_combo.grid(row=0, column=1, sticky="w")
        self.algo_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_algorithm_changed())

        ttk.Label(
            algo_row,
            text="(Recipient must independently select the expected algorithm)",
            font=("Segoe UI", 9, "italic"),
            foreground="#5f6f7a",
        ).grid(row=0, column=2, sticky="w", padx=(10, 0))

        self.status_label = ttk.Label(
            self, textvariable=self.status_var, foreground="#0f5132"
        )
        self.status_label.grid(row=2, column=0, sticky="w", pady=(0, 6))

    def _build_ciphertext_section(self) -> None:
        frame = ttk.LabelFrame(self, text="Received Ciphertext", padding=(10, 8))
        frame.grid(row=3, column=0, sticky="nsew", pady=(0, 6))
        frame.columnconfigure(0, weight=1)

        self.cipher_entry = ttk.Entry(frame, textvariable=self.ciphertext_var, width=50)
        self.cipher_entry.grid(row=0, column=0, sticky="ew")

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Button(btn_row, text="Clear", command=self._clear_ciphertext).pack(side="left")

    def _build_key_section(self) -> None:
        self.key_frame = ttk.LabelFrame(
            self, text="Secret Decryption Key (Enter by hand)", padding=(10, 8)
        )
        self.key_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 6))
        self.key_frame.columnconfigure(0, weight=1)

        self.key_controls_container = ttk.Frame(self.key_frame)
        self.key_controls_container.grid(row=0, column=0, sticky="nsew")
        self.key_controls_container.columnconfigure(0, weight=1)

    def _build_result_section(self) -> None:
        frame = ttk.LabelFrame(self, text="Decryption Output", padding=(10, 8))
        frame.grid(row=5, column=0, sticky="nsew", pady=(0, 6))
        frame.columnconfigure(0, weight=1)

        action_row = ttk.Frame(frame)
        action_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(action_row, text="Decrypt Message", command=self._decrypt_message).pack(
            side="left"
        )

        ttk.Label(frame, text="Recovered Plaintext:").grid(
            row=1, column=0, sticky="w", pady=(2, 2)
        )
        self.result_entry = ttk.Entry(frame, textvariable=self.result_var, state="readonly")
        self.result_entry.grid(row=2, column=0, sticky="ew")

    def _on_algorithm_changed(self) -> None:
        self._render_key_controls()
        self.result_var.set("")
        self._set_status(f"Selected algorithm: {self.algorithm_var.get()}. Enter the secret key.")

    def _render_key_controls(self) -> None:
        for w in self.key_controls_container.winfo_children():
            w.destroy()

        algo = self.algorithm_var.get()
        if algo == "Caesar":
            self._render_caesar_key_controls()
        elif algo == "Playfair":
            self._render_playfair_key_controls()
        else:
            self._render_hill_key_controls()

    def _render_caesar_key_controls(self) -> None:
        row = ttk.Frame(self.key_controls_container)
        row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        row.columnconfigure(2, weight=1)

        ttk.Label(row, text="Shift key n:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(row, textvariable=self.caesar_key_var, width=10).grid(
            row=0, column=1, sticky="w"
        )

        self.caesar_status_lbl = ttk.Label(
            row, textvariable=self.caesar_key_status_var, foreground="#0f5132"
        )
        self.caesar_status_lbl.grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Button(row, text="Check Key", command=self._check_caesar_key).grid(
            row=0, column=3, sticky="e"
        )

        ttk.Label(
            self.key_controls_container,
            text="Integer from 1 to 51 (negative or L = left shift, e.g. 4, -4, R4, L4).",
            foreground="#5f6f7a",
            font=("Segoe UI", 8),
        ).grid(row=1, column=0, sticky="w")

    def _render_playfair_key_controls(self) -> None:
        row = ttk.Frame(self.key_controls_container)
        row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        row.columnconfigure(2, weight=1)

        ttk.Label(row, text="Keyword:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(row, textvariable=self.playfair_key_var, width=20).grid(
            row=0, column=1, sticky="w"
        )

        self.playfair_status_lbl = ttk.Label(
            row, textvariable=self.playfair_key_status_var, foreground="#0f5132"
        )
        self.playfair_status_lbl.grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Button(row, text="Check Key", command=self._check_playfair_key).grid(
            row=0, column=3, sticky="e"
        )

        matrix_frame = ttk.Frame(self.key_controls_container)
        matrix_frame.grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(matrix_frame, text="Key Square (5x5 matrix):").pack(anchor="w")
        ttk.Label(
            matrix_frame,
            textvariable=self.playfair_matrix_var,
            font=("Courier New", 9),
            justify="left",
        ).pack(anchor="w")

        self.playfair_key_var.trace_add("write", lambda *_: self._update_playfair_matrix())
        self._update_playfair_matrix()

    def _update_playfair_matrix(self) -> None:
        k = self.playfair_key_var.get()
        if not k.strip():
            self.playfair_matrix_var.set("(enter a keyword)")
        elif playfair.validate_key(k):
            rows = playfair._build_matrix(k)
            self.playfair_matrix_var.set("\n".join(" ".join(r) for r in rows))
        else:
            self.playfair_matrix_var.set("(invalid keyword)")

    def _render_hill_key_controls(self) -> None:
        top_row = ttk.Frame(self.key_controls_container)
        top_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        top_row.columnconfigure(2, weight=1)

        ttk.Label(top_row, text="Matrix size:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        size_combo = ttk.Combobox(
            top_row,
            textvariable=self.hill_key_size_var,
            values=["2x2", "3x3"],
            state="readonly",
            width=8,
        )
        size_combo.grid(row=0, column=1, sticky="w")
        size_combo.bind("<<ComboboxSelected>>", lambda _e: self._rebuild_hill_grid())

        self.hill_status_lbl = ttk.Label(
            top_row, textvariable=self.hill_key_status_var, foreground="#0f5132"
        )
        self.hill_status_lbl.grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Button(top_row, text="Check Key", command=self._check_hill_key).grid(
            row=0, column=3, sticky="e"
        )

        self.hill_grid_frame = ttk.Frame(self.key_controls_container)
        self.hill_grid_frame.grid(row=1, column=0, sticky="w", pady=(4, 4))

        pad_row = ttk.Frame(self.key_controls_container)
        pad_row.grid(row=2, column=0, sticky="w", pady=(2, 0))
        ttk.Label(pad_row, text="Padding length (optional):").pack(side="left", padx=(0, 6))
        ttk.Entry(pad_row, textvariable=self.hill_padding_var, width=8).pack(side="left")

        self._rebuild_hill_grid()

    def _rebuild_hill_grid(self) -> None:
        if not hasattr(self, "hill_grid_frame"):
            return
        for w in self.hill_grid_frame.winfo_children():
            w.destroy()

        size = 2 if self.hill_key_size_var.get() == "2x2" else 3
        self.hill_key_entries = []
        for r in range(size):
            row_entries: list[ttk.Entry] = []
            for c in range(size):
                e = ttk.Entry(self.hill_grid_frame, width=5, justify="center")
                e.grid(row=r, column=c, padx=3, pady=3)
                row_entries.append(e)
            self.hill_key_entries.append(row_entries)

    def _parse_hill_matrix(self) -> list[list[int]]:
        size = len(self.hill_key_entries)
        matrix: list[list[int]] = []
        for r in range(size):
            row_vals: list[int] = []
            for c in range(size):
                val_str = self.hill_key_entries[r][c].get().strip()
                if not val_str:
                    raise ValueError(f"Cell ({r+1},{c+1}) is empty.")
                try:
                    row_vals.append(int(val_str))
                except ValueError as exc:
                    raise ValueError(f"Cell ({r+1},{c+1}) must be an integer, got: {val_str!r}") from exc
            matrix.append(row_vals)
        return matrix

    def _check_caesar_key(self) -> None:
        k = self.caesar_key_var.get()
        if caesar.validate_key(k):
            self.caesar_key_status_var.set("VALID")
            self.caesar_status_lbl.configure(foreground="#0f5132")
            self._set_status("Caesar key is valid.")
        else:
            self.caesar_key_status_var.set("INVALID")
            self.caesar_status_lbl.configure(foreground="#c92a2a")
            self._set_error_status("Invalid Caesar key. Must be an integer 1..51.")

    def _check_playfair_key(self) -> None:
        k = self.playfair_key_var.get()
        if playfair.validate_key(k):
            self.playfair_key_status_var.set("VALID")
            self.playfair_status_lbl.configure(foreground="#0f5132")
            self._set_status("Playfair keyword is valid.")
        else:
            self.playfair_key_status_var.set("INVALID")
            self.playfair_status_lbl.configure(foreground="#c92a2a")
            self._set_error_status("Invalid Playfair keyword. Must contain letters.")

    def _check_hill_key(self) -> None:
        try:
            mat = self._parse_hill_matrix()
            if hill.validate_key(mat):
                self.hill_key_status_var.set("VALID (Invertible mod 26)")
                self.hill_status_lbl.configure(foreground="#0f5132")
                self._set_status("Hill key matrix is valid and invertible.")
            else:
                self.hill_key_status_var.set("INVALID (Not invertible mod 26)")
                self.hill_status_lbl.configure(foreground="#c92a2a")
                self._set_error_status("Matrix determinant is not coprime with 26.")
        except ValueError as exc:
            self.hill_key_status_var.set("INVALID")
            self.hill_status_lbl.configure(foreground="#c92a2a")
            self._set_error_status(str(exc))

    def _decrypt_message(self) -> None:
        ct = self.ciphertext_var.get().strip()
        if not ct:
            self._set_error_status("No ciphertext to decrypt.")
            return

        algo = self.algorithm_var.get()
        try:
            if algo == "Caesar":
                key = self.caesar_key_var.get()
                if not caesar.validate_key(key):
                    raise ValueError("Invalid Caesar key.")
                pt = caesar.decrypt(ct, key)
            elif algo == "Playfair":
                key = self.playfair_key_var.get()
                if not playfair.validate_key(key):
                    raise ValueError("Invalid Playfair keyword.")
                pt = playfair.decrypt(ct, key)
            elif algo == "Hill":
                matrix = self._parse_hill_matrix()
                if not hill.validate_key(matrix):
                    raise ValueError("Hill key matrix is not invertible modulo 26.")
                pad_raw = self.hill_padding_var.get().strip()
                pad_len = int(pad_raw) if pad_raw else None
                pt = hill.decrypt(ct, matrix, pad_len=pad_len)
            else:
                raise ValueError(f"Unknown algorithm: {algo}")

            self.result_var.set(pt)
            self._set_status("Decryption succeeded! Recipient identity verified.")
        except Exception as exc:
            self.result_var.set("")
            self._set_error_status(
                f"Decryption failed: {exc}. Recipient unverified (wrong algorithm or key)."
            )

    def _clear_ciphertext(self) -> None:
        self.ciphertext_var.set("")
        self.result_var.set("")
        self._set_status("Ciphertext cleared.")

    def set_incoming_ciphertext(self, ciphertext: str, padding: str = "") -> None:
        """Receive incoming ciphertext from Entity A without revealing algorithm or key."""
        self.ciphertext_var.set(ciphertext)
        if padding:
            self.hill_padding_var.set(padding)
        self.result_var.set("")
        self._set_status(
            "New encrypted message received from Entity A! Select the algorithm and enter the secret key to decrypt."
        )

    def _set_status(self, msg: str, is_error: bool = False) -> None:
        self.status_var.set(msg)
        self.status_label.configure(foreground="#c92a2a" if is_error else "#0f5132")

    def _set_error_status(self, msg: str) -> None:
        self._set_status(msg, is_error=True)

    def _pop_out_window(self) -> None:
        top: Any = self.winfo_toplevel()
        if hasattr(top, "open_separate_decryption_window"):
            top.open_separate_decryption_window()


class DecryptionPage(BasePage):
    """Sidebar tab page for Entity B Decryption."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, "Decryption", "")

        for child in self.winfo_children():
            if child.winfo_class() == "Label" and child.cget("text") == "":
                child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.content = DecryptionContent(self, is_toplevel=False)
        self.content.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)

    def set_incoming_ciphertext(self, ciphertext: str, padding: str = "") -> None:
        self.content.set_incoming_ciphertext(ciphertext, padding)


class DecryptionToplevel(tk.Toplevel):
    """Dedicated floating top-level window for Entity B Decryption."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.title("SSAD Toolkit — Entity B (Decryption Window)")
        self.geometry("680x560")
        self.minsize(580, 480)

        self.content = DecryptionContent(self, is_toplevel=True)
        self.content.pack(fill="both", expand=True, padx=12, pady=10)

    def set_incoming_ciphertext(self, ciphertext: str, padding: str = "") -> None:
        self.content.set_incoming_ciphertext(ciphertext, padding)

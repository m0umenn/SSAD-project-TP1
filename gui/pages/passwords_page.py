"""Passwords page for encrypting passwords and testing login with lockout."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui.pages.base_page import BasePage
from passwords import cipher_adapter, generators, protection
from passwords.cipher_adapter import block_size, get_alphabet


# ---------------------------------------------------------------------------
# Key format hints shown below the key field
# ---------------------------------------------------------------------------

def _key_hint(use_case: int, cipher: str) -> str:
    """Return a short format hint for the key field."""
    alphabet = get_alphabet(use_case)
    m = len(alphabet)
    spec = generators.USE_CASES[use_case]
    length = int(spec["length"])
    if cipher == "caesar":
        if m == 2:
            # Only one valid Caesar key exists: k=1. Flag it clearly.
            return (
                f"Only 1 valid key (k=1) \u2014 alphabet has {m} symbols so range [1, m-1] = {{1}}. "
                f"Hill is strongly recommended for this use case."
            )
        return f"Integer from 1 to {m - 1}  (shift modulo {m})"
    else:  # hill
        n = block_size(use_case)
        return (
            f"{n}\u00d7{n} matrix = {n*n} integers 0\u2013{m - 1}, row by row  "
            f"(block {n} divides password length {length})"
        )


class PasswordsPage(BasePage):
    """Defender-side password storage (by encryption) and login verification page."""

    CIPHERS = ["hill", "caesar"]

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, "Passwords", "")

        for child in self.winfo_children():
            if child.winfo_class() == "Label" and child.cget("text") == "":
                child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="")
        self.use_case_var = tk.StringVar(value="")
        self.cipher_var = tk.StringVar(value="hill")
        self.show_store_pw_var = tk.BooleanVar(value=False)
        self.show_login_pw_var = tk.BooleanVar(value=False)

        # Record display variables (strictly no secret key)
        self.record_use_case_var = tk.StringVar(value="")
        self.record_cipher_var = tk.StringVar(value="")
        self.record_ciphertext_var = tk.StringVar(value="")
        self.record_modulus_var = tk.StringVar(value="")
        self.record_block_var = tk.StringVar(value="")
        self.login_state_var = tk.StringVar(value="No password stored.")

        self.store_key_hint_var = tk.StringVar(value="")
        self.login_key_hint_var = tk.StringVar(value="")

        self._record: dict[str, Any] | None = None
        self._lockout: protection.Lockout | None = None
        self._countdown_job: str | None = None

        self.page_frame = ttk.Frame(self, padding=(10, 6))
        self.page_frame.grid(row=1, column=0, sticky="nsew")
        self.page_frame.columnconfigure(0, weight=1)
        self.page_frame.rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_sections()
        self._on_cipher_changed()
        self._sync_shared(None, None, None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _use_case_options(self) -> list[str]:
        options: list[str] = []
        for uc_id, spec in sorted(generators.USE_CASES.items()):
            alphabet = str(spec["alphabet"])
            if len(alphabet) > 16:
                alpha_desc = f"{alphabet[:6]}...{alphabet[-2:]} (64 chars)"
            else:
                alpha_desc = alphabet
            options.append(f"{uc_id} - alphabet {alpha_desc}, length {spec['length']}")
        return options

    def _selected_use_case(self) -> int:
        raw = self.use_case_var.get().strip()
        if not raw:
            raise ValueError("Unknown use case.")
        prefix = raw.split("-", 1)[0].strip()
        try:
            return int(prefix)
        except ValueError as exc:
            raise ValueError("Unknown use case.") from exc

    def _selected_cipher(self) -> str:
        return self.cipher_var.get().strip().lower() or "hill"

    # ------------------------------------------------------------------
    # Top bar (use-case + cipher selection)
    # ------------------------------------------------------------------

    def _build_top_bar(self) -> None:
        top = ttk.Frame(self.page_frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Use case:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        options = self._use_case_options()
        if options:
            self.use_case_var.set(options[0])

        self.use_case_combo = ttk.Combobox(
            top,
            textvariable=self.use_case_var,
            values=options,
            state="readonly",
            width=44,
        )
        self.use_case_combo.grid(row=0, column=1, sticky="w")
        self.use_case_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._on_use_case_changed(),
        )

        ttk.Label(top, text="Cipher:").grid(row=0, column=2, sticky="w", padx=(14, 6))
        cipher_combo = ttk.Combobox(
            top,
            textvariable=self.cipher_var,
            values=self.CIPHERS,
            state="readonly",
            width=10,
        )
        cipher_combo.grid(row=0, column=3, sticky="w")
        cipher_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._on_cipher_changed(),
        )

        self.status_label = ttk.Label(top, textvariable=self.status_var, foreground="#0f5132")
        self.status_label.grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))

    # ------------------------------------------------------------------
    # Main two-column layout
    # ------------------------------------------------------------------

    def _build_sections(self) -> None:
        main = ttk.Frame(self.page_frame)
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1, uniform="pw_sections")
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=1, uniform="pw_sections")

        store_frame = ttk.LabelFrame(main, text="Store a password (Encryption)", padding=(10, 8))
        store_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        store_frame.columnconfigure(0, weight=1)

        separator = ttk.Separator(main, orient="vertical")
        separator.grid(row=0, column=1, sticky="ns", padx=(0, 6))

        login_frame = ttk.LabelFrame(main, text="Log in", padding=(10, 8))
        login_frame.grid(row=0, column=2, sticky="nsew")
        login_frame.columnconfigure(0, weight=1)

        self._build_store_section(store_frame)
        self._build_login_section(login_frame)

    def _build_store_section(self, frame: ttk.LabelFrame) -> None:
        ttk.Label(frame, text="Password:").grid(row=0, column=0, sticky="w", pady=(0, 4))

        pw_row = ttk.Frame(frame)
        pw_row.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        pw_row.columnconfigure(0, weight=1)

        self.store_password_entry = ttk.Entry(pw_row, show="*", width=24)
        self.store_password_entry.grid(row=0, column=0, sticky="ew")
        ttk.Checkbutton(
            pw_row,
            text="Show",
            variable=self.show_store_pw_var,
            command=self._toggle_store_password_visibility,
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        # Secret encryption key
        ttk.Label(frame, text="Secret encryption key:").grid(
            row=2, column=0, sticky="w", pady=(0, 2)
        )
        self.store_key_hint_label = ttk.Label(
            frame,
            textvariable=self.store_key_hint_var,
            foreground="#5f6f7a",
            font=("Segoe UI", 9),
        )
        self.store_key_hint_label.grid(row=3, column=0, sticky="w", pady=(0, 2))
        self.store_key_entry = ttk.Entry(frame, width=36)
        self.store_key_entry.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(btn_row, text="Store", command=self._store_password).pack(side="left")
        ttk.Button(btn_row, text="Send to Attacks", command=self._send_to_attacks).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(btn_row, text="Clear", command=self._clear_all).pack(side="left", padx=(8, 0))

        ttk.Label(frame, text="Protected record (key is never stored):").grid(
            row=6, column=0, sticky="w", pady=(0, 4)
        )

        record_grid = ttk.Frame(frame)
        record_grid.grid(row=7, column=0, sticky="ew")
        record_grid.columnconfigure(1, weight=1)

        for row_idx, (label, var) in enumerate([
            ("Use case:", self.record_use_case_var),
            ("Cipher:", self.record_cipher_var),
            ("Ciphertext:", self.record_ciphertext_var),
            ("Modulus (m):", self.record_modulus_var),
            ("Block size (n):", self.record_block_var),
        ]):
            ttk.Label(record_grid, text=label).grid(
                row=row_idx, column=0, sticky="w", padx=(0, 6), pady=2
            )
            ttk.Entry(record_grid, textvariable=var, state="readonly").grid(
                row=row_idx, column=1, sticky="ew", pady=2
            )

    def _build_login_section(self, frame: ttk.LabelFrame) -> None:
        ttk.Label(frame, text="Password attempt:").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        attempt_row = ttk.Frame(frame)
        attempt_row.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        attempt_row.columnconfigure(0, weight=1)

        self.attempt_entry = ttk.Entry(attempt_row, show="*", width=24)
        self.attempt_entry.grid(row=0, column=0, sticky="ew")
        ttk.Checkbutton(
            attempt_row,
            text="Show",
            variable=self.show_login_pw_var,
            command=self._toggle_login_password_visibility,
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(frame, text="Secret decryption key:").grid(
            row=2, column=0, sticky="w", pady=(0, 2)
        )
        self.login_key_hint_label = ttk.Label(
            frame,
            textvariable=self.login_key_hint_var,
            foreground="#5f6f7a",
            font=("Segoe UI", 9),
        )
        self.login_key_hint_label.grid(row=3, column=0, sticky="w", pady=(0, 2))
        self.login_key_entry = ttk.Entry(frame, width=36)
        self.login_key_entry.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.login_button = ttk.Button(frame, text="Log in", command=self._login)
        self.login_button.grid(row=5, column=0, sticky="w", pady=(0, 10))

        ttk.Label(frame, text="Protection status:").grid(
            row=6, column=0, sticky="w", pady=(0, 4)
        )
        self.login_state_label = ttk.Label(
            frame,
            textvariable=self.login_state_var,
            foreground="#52616f",
            font=("Segoe UI", 10, "bold"),
        )
        self.login_state_label.grid(row=7, column=0, sticky="w")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_use_case_changed(self) -> None:
        self._clear_all()
        self._on_cipher_changed()

    def _on_cipher_changed(self) -> None:
        try:
            uc = self._selected_use_case()
            cipher = self._selected_cipher()
            hint = _key_hint(uc, cipher)
        except Exception:
            hint = ""
        self.store_key_hint_var.set(hint)
        self.login_key_hint_var.set(hint)

    def _toggle_store_password_visibility(self) -> None:
        self.store_password_entry.configure(show="" if self.show_store_pw_var.get() else "*")

    def _toggle_login_password_visibility(self) -> None:
        self.attempt_entry.configure(show="" if self.show_login_pw_var.get() else "*")

    def _set_status(self, message: str, is_error: bool = False) -> None:
        self.status_var.set(message)
        self.status_label.configure(foreground="#c92a2a" if is_error else "#0f5132")

    def _set_error_status(self, message: str) -> None:
        self._set_status(message, is_error=True)

    def _sync_shared(
        self,
        use_case: int | None,
        cipher: str | None,
        record: dict[str, Any] | None,
    ) -> None:
        top: Any = self.winfo_toplevel()
        shared = getattr(top, "shared", None)
        payload: dict[str, Any] = {
            "use_case": use_case,
            "cipher": cipher,
            "record": dict(record) if record is not None else None,
        }
        if isinstance(shared, dict):
            shared.update(payload)
        else:
            try:
                top.shared = payload
            except Exception:
                pass

    def _cancel_countdown(self) -> None:
        if self._countdown_job is not None:
            try:
                self.after_cancel(self._countdown_job)
            except Exception:
                pass
            self._countdown_job = None

    def _clear_all(self) -> None:
        self._cancel_countdown()
        self.store_password_entry.delete(0, tk.END)
        self.store_key_entry.delete(0, tk.END)
        self.attempt_entry.delete(0, tk.END)
        self.login_key_entry.delete(0, tk.END)
        self.record_use_case_var.set("")
        self.record_cipher_var.set("")
        self.record_ciphertext_var.set("")
        self.record_modulus_var.set("")
        self.record_block_var.set("")
        self._record = None
        self._lockout = None
        self.login_button.configure(state="normal")
        self.login_state_var.set("No password stored.")
        self.login_state_label.configure(foreground="#52616f")
        self.status_var.set("")
        self._sync_shared(None, None, None)

    # ------------------------------------------------------------------
    # Store
    # ------------------------------------------------------------------

    def _store_password(self) -> None:
        password = self.store_password_entry.get()
        key_raw = self.store_key_entry.get()
        self.store_password_entry.delete(0, tk.END)
        self.store_key_entry.delete(0, tk.END)
        try:
            use_case = self._selected_use_case()
            cipher = self._selected_cipher()
            protection.validate_password(password, use_case)
            record = protection.protect(password, use_case, cipher=cipher, key=key_raw)
        except ValueError as exc:
            self._set_error_status(str(exc))
            return
        finally:
            password = ""
            key_raw = ""

        self._cancel_countdown()
        self._record = record
        self._lockout = protection.Lockout()

        params = record.get("params", {})
        self.record_use_case_var.set(str(record["use_case"]))
        self.record_cipher_var.set(str(record["cipher"]))
        self.record_ciphertext_var.set(str(record["ciphertext"]))
        self.record_modulus_var.set(str(params.get("modulus", "")))
        self.record_block_var.set(str(params.get("block", "")))

        self.login_button.configure(state="normal")
        left = self._lockout.attempts_left()
        self.login_state_var.set(f"Attempts left: {left}")
        self.login_state_label.configure(foreground="#0f5132")

        self._sync_shared(use_case, str(record["cipher"]), record)
        self._set_status("Stored. Target ready for the Attacks page.")

    def _send_to_attacks(self) -> None:
        if self._record is None:
            self._set_error_status("Store a password first.")
            return
        try:
            use_case = self._selected_use_case()
        except ValueError as exc:
            self._set_error_status(str(exc))
            return
        self._sync_shared(use_case, str(self._record["cipher"]), self._record)
        self._set_status("Target is available on the Attacks page.")

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def _login(self) -> None:
        attempt = self.attempt_entry.get()
        key_raw = self.login_key_entry.get()
        self.attempt_entry.delete(0, tk.END)
        self.login_key_entry.delete(0, tk.END)
        try:
            if self._record is None or self._lockout is None:
                self._set_error_status("Store a password first.")
                return

            # Determine cipher from record so the login key is parsed consistently
            cipher = str(self._record.get("cipher", "hill"))
            use_case = int(self._record["use_case"])
            parsed_key = cipher_adapter.parse_key(key_raw, use_case, cipher)
            check = protection.make_checker(self._record, parsed_key)
            ok = check(attempt)
            granted = self._lockout.record(ok)
        except ValueError as exc:
            self._set_error_status(str(exc))
            if self._lockout is not None and self._lockout.remaining() > 0.0:
                self._start_lock_countdown()
            return
        finally:
            attempt = ""
            key_raw = ""

        if granted:
            self._cancel_countdown()
            self.login_button.configure(state="normal")
            left = self._lockout.attempts_left()
            self.login_state_var.set(f"Attempts left: {left}")
            self.login_state_label.configure(foreground="#0f5132")
            self._set_status("Access granted.")
            return

        rem = self._lockout.remaining()
        if rem > 0.0:
            self._start_lock_countdown()
        else:
            left = self._lockout.attempts_left()
            self.login_state_var.set(f"Attempts left: {left}")
            self.login_state_label.configure(foreground="#c92a2a")
            self._set_error_status(f"Wrong password or key, {left} attempts left.")

    def _start_lock_countdown(self) -> None:
        self._cancel_countdown()
        if self._lockout is None:
            return
        rem = self._lockout.remaining()
        if rem <= 0.0:
            self.login_button.configure(state="normal")
            left = self._lockout.attempts_left()
            self.login_state_var.set(f"Attempts left: {left}")
            self.login_state_label.configure(foreground="#0f5132")
            self._set_status("Lock expired. You may try again.")
            return

        secs = max(1, int(math.ceil(rem)))
        self.login_button.configure(state="disabled")
        msg = f"Locked. Try again in {secs} s."
        self.login_state_var.set(msg)
        self.login_state_label.configure(foreground="#c92a2a")
        self._set_error_status(msg)
        self._countdown_job = self.after(1000, self._start_lock_countdown)

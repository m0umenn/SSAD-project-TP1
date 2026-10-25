"""Passwords page for storing protected passwords and testing login with lockout."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui.pages.base_page import BasePage
from passwords import generators, protection


class PasswordsPage(BasePage):
    """Defender-side password storage and login verification page."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, "Passwords", "")

        for child in self.winfo_children():
            if child.winfo_class() == "Label" and child.cget("text") == "":
                child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="")
        self.use_case_var = tk.StringVar(value="")
        self.show_store_pw_var = tk.BooleanVar(value=False)
        self.show_login_pw_var = tk.BooleanVar(value=False)

        self.fast_hash_var = tk.StringVar(value="")
        self.salt_var = tk.StringVar(value="")
        self.iterations_var = tk.StringVar(value="")
        self.protected_hash_var = tk.StringVar(value="")
        self.login_state_var = tk.StringVar(value="No password stored.")

        self._fast_hash: str | None = None
        self._record: dict[str, str | int] | None = None
        self._lockout: protection.Lockout | None = None
        self._countdown_job: str | None = None

        self.page_frame = ttk.Frame(self, padding=(10, 6))
        self.page_frame.grid(row=1, column=0, sticky="nsew")
        self.page_frame.columnconfigure(0, weight=1)
        self.page_frame.rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_sections()
        self._sync_shared(None, None, None)

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

    def _build_top_bar(self) -> None:
        top = ttk.Frame(self.page_frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.columnconfigure(0, weight=0)
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Use case:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        options = self._use_case_options()
        if options:
            self.use_case_var.set(options[0])

        self.use_case_combo = ttk.Combobox(
            top,
            textvariable=self.use_case_var,
            values=options,
            state="readonly",
            width=45,
        )
        self.use_case_combo.grid(row=0, column=1, sticky="w")
        self.use_case_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_use_case_changed())

        self.status_label = ttk.Label(top, textvariable=self.status_var, foreground="#0f5132")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def _build_sections(self) -> None:
        main = ttk.Frame(self.page_frame)
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1, uniform="pw_sections")
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=1, uniform="pw_sections")

        store_frame = ttk.LabelFrame(main, text="Store a password", padding=(10, 8))
        store_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        store_frame.columnconfigure(0, weight=1)

        separator = ttk.Separator(main, orient="vertical")
        separator.grid(row=0, column=1, sticky="ns", padx=(0, 6))

        login_frame = ttk.LabelFrame(main, text="Log in", padding=(10, 8))
        login_frame.grid(row=0, column=2, sticky="nsew")
        login_frame.columnconfigure(0, weight=1)

        # --- Section 1: Store a password ---
        ttk.Label(store_frame, text="Password:").grid(row=0, column=0, sticky="w", pady=(0, 4))

        pw_row = ttk.Frame(store_frame)
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

        btn_row = ttk.Frame(store_frame)
        btn_row.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(btn_row, text="Store", command=self._store_password).pack(side="left")
        ttk.Button(btn_row, text="Send to Attacks", command=self._send_to_attacks).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(btn_row, text="Clear", command=self._clear_all).pack(side="left", padx=(8, 0))

        ttk.Label(store_frame, text="Fast hash (SHA-256, unprotected):").grid(
            row=3, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Entry(store_frame, textvariable=self.fast_hash_var, state="readonly").grid(
            row=4, column=0, sticky="ew", pady=(0, 8)
        )

        ttk.Label(store_frame, text="Protected record (PBKDF2-HMAC-SHA256):").grid(
            row=5, column=0, sticky="w", pady=(0, 4)
        )

        record_grid = ttk.Frame(store_frame)
        record_grid.grid(row=6, column=0, sticky="ew")
        record_grid.columnconfigure(1, weight=1)

        ttk.Label(record_grid, text="Salt:").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(record_grid, textvariable=self.salt_var, state="readonly").grid(
            row=0, column=1, sticky="ew", pady=2
        )

        ttk.Label(record_grid, text="Iterations:").grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=2
        )
        ttk.Entry(record_grid, textvariable=self.iterations_var, state="readonly").grid(
            row=1, column=1, sticky="ew", pady=2
        )

        ttk.Label(record_grid, text="Hash:").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(record_grid, textvariable=self.protected_hash_var, state="readonly").grid(
            row=2, column=1, sticky="ew", pady=2
        )

        # --- Section 2: Log in ---
        ttk.Label(login_frame, text="Password attempt:").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        attempt_row = ttk.Frame(login_frame)
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

        self.login_button = ttk.Button(login_frame, text="Log in", command=self._login)
        self.login_button.grid(row=2, column=0, sticky="w", pady=(0, 10))

        ttk.Label(login_frame, text="Protection status:").grid(
            row=3, column=0, sticky="w", pady=(0, 4)
        )
        self.login_state_label = ttk.Label(
            login_frame,
            textvariable=self.login_state_var,
            foreground="#52616f",
            font=("Segoe UI", 10, "bold"),
        )
        self.login_state_label.grid(row=4, column=0, sticky="w")

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
        fast_hash: str | None,
        record: dict[str, str | int] | None,
    ) -> None:
        top: Any = self.winfo_toplevel()
        shared = getattr(top, "shared", None)
        payload: dict[str, Any] = {
            "use_case": use_case,
            "fast_hash": fast_hash,
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

    def _on_use_case_changed(self) -> None:
        self._clear_all()

    def _clear_all(self) -> None:
        self._cancel_countdown()
        self.store_password_entry.delete(0, tk.END)
        self.attempt_entry.delete(0, tk.END)
        self.fast_hash_var.set("")
        self.salt_var.set("")
        self.iterations_var.set("")
        self.protected_hash_var.set("")
        self._fast_hash = None
        self._record = None
        self._lockout = None
        self.login_button.configure(state="normal")
        self.login_state_var.set("No password stored.")
        self.login_state_label.configure(foreground="#52616f")
        self.status_var.set("")
        self._sync_shared(None, None, None)

    def _store_password(self) -> None:
        password = self.store_password_entry.get()
        self.store_password_entry.delete(0, tk.END)
        try:
            use_case = self._selected_use_case()
            protection.validate_password(password, use_case)
            fast_digest = generators.hash_fast(password)
            record = protection.hash_protected(password)
        except ValueError as exc:
            self._set_error_status(str(exc))
            return
        finally:
            password = ""

        self._cancel_countdown()
        self._fast_hash = fast_digest
        self._record = record
        self._lockout = protection.Lockout()

        self.fast_hash_var.set(fast_digest)
        self.salt_var.set(str(record["salt"]))
        self.iterations_var.set(str(record["iterations"]))
        self.protected_hash_var.set(str(record["hash"]))

        self.login_button.configure(state="normal")
        left = self._lockout.attempts_left()
        self.login_state_var.set(f"Attempts left: {left}")
        self.login_state_label.configure(foreground="#0f5132")

        self._sync_shared(use_case, fast_digest, record)
        self._set_status("Stored. Target ready for the Attacks page.")

    def _send_to_attacks(self) -> None:
        if self._record is None or self._fast_hash is None:
            self._set_error_status("Store a password first.")
            return
        try:
            use_case = self._selected_use_case()
        except ValueError as exc:
            self._set_error_status(str(exc))
            return
        self._sync_shared(use_case, self._fast_hash, self._record)
        self._set_status("Target is available on the Attacks page.")

    def _login(self) -> None:
        attempt = self.attempt_entry.get()
        self.attempt_entry.delete(0, tk.END)
        try:
            if self._record is None or self._lockout is None:
                self._set_error_status("Store a password first.")
                return

            ok = protection.verify_protected(attempt, self._record)
            granted = self._lockout.record(ok)
        except ValueError as exc:
            self._set_error_status(str(exc))
            if self._lockout is not None and self._lockout.remaining() > 0.0:
                self._start_lock_countdown()
            return
        finally:
            attempt = ""

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
            self._set_error_status(f"Wrong password, {left} attempts left.")

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

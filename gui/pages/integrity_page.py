"""Authenticity and integrity page (Part 4).

Tabs:
  - Hash & verify : A hashes a text or a file (SHA-256, or HMAC-SHA-256 if a secret key
                    is given) and sends it to B, who verifies it.
  - Salt demo     : same password + two random salts = two different stored values.
  - Tamper demo   : check whether a digest or HMAC detects a ciphertext modification.

Everything here relies on the integrity package (standard library only).
"""

from __future__ import annotations

import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Any, Callable

from gui.pages.base_page import BasePage
from integrity import (
    ITERATIONS,
    estimate_slowdown,
    hash_data,
    hash_fast,
    hash_file,
    hash_protected,
    hmac_file,
    hmac_sha256,
    verify_digest,
    verify_hmac,
    verify_hmac_file,
    verify_protected,
)

OK_COLOR = "#0f5132"
FAIL_COLOR = "#c92a2a"
INFO_COLOR = "#52616f"
WARN_COLOR = "#b45309"  # amber: a check passed although the content was changed
MONO = ("Courier New", 10)


class IntegrityPage(BasePage):
    """Integrity (SHA-256) and authenticity (HMAC) tools plus short demos."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, "Authenticity / Integrity", "")

        # Remove BasePage's empty placeholder label, like the Attacks page does.
        for child in self.winfo_children():
            if child.winfo_class() in ("Label", "TLabel") and child.cget("text") == "":
                child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.page_frame = ttk.Frame(self, padding=(10, 6))
        self.page_frame.grid(row=1, column=0, sticky="nsew")
        self.page_frame.columnconfigure(0, weight=1)
        self.page_frame.rowconfigure(1, weight=1)

        self._build_intro_section()

        self.notebook = ttk.Notebook(self.page_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self._build_hash_tab()
        self._build_salt_tab()
        self._build_tamper_tab()

    # ------------------------------------------------------------ shared UI

    def _build_intro_section(self) -> None:
        intro = ttk.Frame(self.page_frame, padding=(0, 0, 0, 10))
        intro.grid(row=0, column=0, sticky="ew")
        intro.columnconfigure(0, weight=1)
        text = (
            "Integrity: a SHA-256 digest changes completely if the content changes by "
            "even one character, so the receiver can detect a modification.\n"
            "Authenticity: an HMAC mixes a secret key into the hash, so only someone who "
            "knows the key can produce a valid tag - an attacker cannot simply recompute it."
        )
        ttk.Label(
            intro, text=text, wraplength=900, justify="left", foreground=INFO_COLOR
        ).grid(row=0, column=0, sticky="w")

    def _new_tab(self, title: str) -> ttk.Frame:
        tab = ttk.Frame(self.notebook, padding=(0, 10, 0, 0))
        tab.columnconfigure(0, weight=1, uniform="integrity_sides")
        tab.columnconfigure(1, weight=0)
        tab.columnconfigure(2, weight=1, uniform="integrity_sides")
        tab.rowconfigure(0, weight=1)
        self.notebook.add(tab, text=title)
        return tab

    @staticmethod
    def _make_sides(tab: ttk.Frame, left_title: str, right_title: str) -> tuple[ttk.LabelFrame, ttk.LabelFrame]:
        left = ttk.LabelFrame(tab, text=left_title, padding=(10, 8))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.columnconfigure(0, weight=1)
        ttk.Separator(tab, orient="vertical").grid(row=0, column=1, sticky="ns", padx=(0, 6))
        right = ttk.LabelFrame(tab, text=right_title, padding=(10, 8))
        right.grid(row=0, column=2, sticky="nsew")
        right.columnconfigure(0, weight=1)
        return left, right

    @staticmethod
    def _text_box(parent: tk.Widget, row: int) -> tk.Text:
        box = tk.Text(
            parent,
            height=4,
            wrap="word",
            font=MONO,
            background="#f7f8fc",
            borderwidth=1,
            relief="solid",
            highlightthickness=0,
            padx=6,
            pady=4,
        )
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        return box

    @staticmethod
    def _label(parent: tk.Widget, row: int, text: str) -> None:
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w")

    @staticmethod
    def _readonly(parent: tk.Widget, row: int, var: tk.StringVar) -> ttk.Entry:
        entry = ttk.Entry(parent, textvariable=var, state="readonly")
        entry.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        return entry

    @staticmethod
    def _status(parent: tk.Widget, row: int, text: str = "") -> ttk.Label:
        label = ttk.Label(parent, text=text, foreground=INFO_COLOR, wraplength=480, justify="left")
        label.grid(row=row, column=0, sticky="w")
        return label

    @staticmethod
    def _buttons(parent: tk.Widget, row: int, *specs: tuple[str, Callable[[], None]]) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        for index, (label, command) in enumerate(specs):
            ttk.Button(frame, text=label, command=command).pack(
                side="left", padx=(0 if index == 0 else 8, 0)
            )
        return frame

    def _file_row(self, parent: tk.Widget, row: int, var: tk.StringVar) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(0, weight=1)
        ttk.Entry(frame, textvariable=var).grid(row=0, column=0, sticky="ew")
        ttk.Button(frame, text="Browse...", command=lambda: self._browse(var)).grid(
            row=0, column=1, padx=(8, 0)
        )

    @staticmethod
    def _browse(var: tk.StringVar) -> None:
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    @staticmethod
    def _get_text(widget: tk.Text) -> str:
        return widget.get("1.0", "end-1c")

    @staticmethod
    def _set_text(widget: tk.Text, value: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", value)

    @staticmethod
    def _say(label: ttk.Label, text: str, color: str = INFO_COLOR) -> None:
        label.configure(text=text, foreground=color)

    def _background(self, work: Callable[[], Any], done: Callable[[Any, str | None], None]) -> None:
        """Run `work` in a thread so large files never freeze the window."""

        box: dict[str, Any] = {}

        def runner() -> None:
            try:
                box["result"] = work()
            except Exception as exc:  # noqa: BLE001 - shown to the user
                box["error"] = str(exc)
            finally:
                box["finished"] = True

        def poll() -> None:
            # Tk is only touched from the main thread: it polls for the result.
            if box.get("finished"):
                done(box.get("result"), box.get("error"))
            else:
                self.after(30, poll)

        threading.Thread(target=runner, daemon=True).start()
        self.after(30, poll)

    # ------------------------------------------------------- tab: hash & verify
    #
    # One screen for integrity and authenticity. Without a secret key the result
    # is a plain SHA-256 digest; with a key it is an HMAC-SHA-256 tag (SHA-256
    # mixed with the key). Side B uses the same rule to verify.

    def _build_hash_tab(self) -> None:
        tab = self._new_tab("Hash & verify")
        left, right = self._make_sides(
            tab,
            "Entity A (sender): hash a text or a file",
            "Entity B (receiver): verify the content",
        )
        self.show_keys = tk.BooleanVar(value=False)
        self._hashed_kind: str | None = None  # "text" or "file": what A last hashed
        self._hashed_value = ""
        self._hashed_key = ""

        # Left: A
        self._label(left, 0, "Secret key (optional): empty = SHA-256 digest, filled = HMAC-SHA-256 tag")
        self.hash_key = ttk.Entry(left, show="*")
        self.hash_key.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        ttk.Checkbutton(
            left, text="Show keys", variable=self.show_keys, command=self._toggle_keys
        ).grid(row=2, column=0, sticky="w", pady=(0, 8))
        self.hash_text = self._text_box_with_label(left, 3, "Text:")
        self._buttons(left, 5, ("Hash text", self._hash_text_clicked))
        self._label(left, 6, "File:")
        self.hash_path = tk.StringVar()
        self._file_row(left, 7, self.hash_path)
        self._buttons(left, 8, ("Hash file", self._hash_file_clicked))
        self.hash_result_label = ttk.Label(left, text="SHA-256 digest / HMAC tag:")
        self.hash_result_label.grid(row=9, column=0, sticky="w")
        self.hash_digest = tk.StringVar()
        self._readonly(left, 10, self.hash_digest)
        self._buttons(left, 11, ("Send to B →", self._send_to_b), ("Clear all", self._hash_clear))
        self.hash_status = self._status(left, 12, "Enter a text or choose a file.")

        # Right: B
        self._label(right, 0, "Content received (editable):")
        self.verify_mode = tk.StringVar(value="text")
        modes = ttk.Frame(right)
        modes.grid(row=1, column=0, sticky="w", pady=(0, 4))
        ttk.Radiobutton(modes, text="Text", variable=self.verify_mode, value="text").pack(side="left")
        ttk.Radiobutton(modes, text="File", variable=self.verify_mode, value="file").pack(
            side="left", padx=(12, 0)
        )
        self.verify_text = self._text_box(right, 2)
        self.verify_path = tk.StringVar()
        self._file_row(right, 3, self.verify_path)
        self._label(right, 4, "Secret key (optional, the same as A's):")
        self.verify_key = ttk.Entry(right, show="*")
        self.verify_key.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        self._label(right, 6, "Expected digest or tag (64 hex characters):")
        self.verify_digest_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.verify_digest_var).grid(
            row=7, column=0, sticky="ew", pady=(0, 8)
        )
        self._buttons(right, 8, ("Verify", self._verify_clicked))
        self._label(right, 9, "Result:")
        self.verify_result = ttk.Label(
            right,
            text="No check yet.",
            font=("TkDefaultFont", 10, "bold"),
            wraplength=480,
            justify="left",
            foreground=INFO_COLOR,
        )
        self.verify_result.grid(row=10, column=0, sticky="w")

    def _text_box_with_label(self, parent: tk.Widget, row: int, label: str) -> tk.Text:
        self._label(parent, row, label)
        return self._text_box(parent, row + 1)

    def _toggle_keys(self) -> None:
        show = "" if self.show_keys.get() else "*"
        for entry in (self.hash_key, self.verify_key, self.salt_entry, self.tamper_key):
            entry.configure(show=show)

    def _set_result(self, value: str, with_key: bool) -> None:
        self.hash_digest.set(value)
        self.hash_result_label.configure(
            text="HMAC-SHA-256 tag:" if with_key else "SHA-256 digest:"
        )

    def _hash_text_clicked(self) -> None:
        text = self._get_text(self.hash_text)
        if not text:
            self.hash_digest.set("")
            self._say(self.hash_status, "Enter a text first.", FAIL_COLOR)
            return
        key = self.hash_key.get()
        try:
            value = hmac_sha256(key, text) if key else hash_data(text)
        except ValueError as exc:
            self._say(self.hash_status, str(exc), FAIL_COLOR)
            return
        self._set_result(value, bool(key))
        self._hashed_kind, self._hashed_value, self._hashed_key = "text", text, key
        self._say(self.hash_status, "Tag computed with the key." if key else "Text hashed.", OK_COLOR)

    def _hash_file_clicked(self) -> None:
        path = self.hash_path.get().strip()
        if not path:
            self._say(self.hash_status, "Choose a file first.", FAIL_COLOR)
            return
        key = self.hash_key.get()
        self._say(self.hash_status, "Hashing the file...")

        def work() -> str:
            return hmac_file(key, Path(path)) if key else hash_file(Path(path))

        def done(result: Any, error: str | None) -> None:
            if error:
                self.hash_digest.set("")
                self._say(self.hash_status, error, FAIL_COLOR)
            else:
                self._set_result(result, bool(key))
                self._hashed_kind, self._hashed_value, self._hashed_key = "file", path, key
                self._say(
                    self.hash_status,
                    "File tag computed with the key." if key else "File hashed.",
                    OK_COLOR,
                )

        self._background(work, done)

    def _send_to_b(self) -> None:
        """Copy what A hashed (text or file), its digest or tag, and the key to B."""
        digest = self.hash_digest.get()
        if not digest or self._hashed_kind is None:
            self._say(self.hash_status, "Compute a digest first.", FAIL_COLOR)
            return
        if self._hashed_kind == "text":
            self.verify_mode.set("text")
            self._set_text(self.verify_text, self._hashed_value)
        else:
            self.verify_mode.set("file")
            self.verify_path.set(self._hashed_value)
        self.verify_key.delete(0, "end")
        self.verify_key.insert(0, self._hashed_key)
        self.verify_digest_var.set(digest)
        self._say(self.verify_result, "Content and digest received. Click \"Verify\".")
        self._say(self.hash_status, "Content, digest and key sent to B.", OK_COLOR)

    def _hash_clear(self) -> None:
        """Reset both sides: A (key, text, file, result) and B (content, key, digest, result)."""
        self.hash_key.delete(0, "end")
        self._set_text(self.hash_text, "")
        self.hash_path.set("")
        self._set_result("", False)
        self.hash_result_label.configure(text="SHA-256 digest / HMAC tag:")
        self._hashed_kind, self._hashed_value, self._hashed_key = None, "", ""
        self._say(self.hash_status, "Enter a text or choose a file.")
        self.verify_mode.set("text")
        self._set_text(self.verify_text, "")
        self.verify_path.set("")
        self.verify_key.delete(0, "end")
        self.verify_digest_var.set("")
        self._say(self.verify_result, "No check yet.")

    def _show_verify(self, ok: bool, with_key: bool) -> None:
        if with_key:
            if ok:
                self._say(
                    self.verify_result,
                    "HMAC valid: the content is unchanged and comes from a holder of the key.",
                    OK_COLOR,
                )
            else:
                self._say(
                    self.verify_result,
                    "HMAC INVALID: the content was modified or the key is wrong.",
                    FAIL_COLOR,
                )
        elif ok:
            self._say(self.verify_result, "Digest matches: the content is unchanged.", OK_COLOR)
        else:
            self._say(self.verify_result, "Digest does NOT match: the content was modified.", FAIL_COLOR)

    def _verify_clicked(self) -> None:
        digest = self.verify_digest_var.get().strip()
        if not digest:
            self._say(self.verify_result, "Enter the expected digest or tag.", FAIL_COLOR)
            return
        key = self.verify_key.get()
        with_key = bool(key)
        if self.verify_mode.get() == "text":
            text = self._get_text(self.verify_text)
            try:
                ok = verify_hmac(key, text, digest) if with_key else verify_digest(text, digest)
            except ValueError as exc:
                self._say(self.verify_result, str(exc), FAIL_COLOR)
                return
            self._show_verify(ok, with_key)
            return

        path = self.verify_path.get().strip()
        if not path:
            self._say(self.verify_result, "Choose a file first.", FAIL_COLOR)
            return
        self._say(self.verify_result, "Checking the file...")

        def work() -> bool:
            if with_key:
                return verify_hmac_file(key, Path(path), digest)
            return verify_digest(path, digest, is_path=True)

        def done(result: Any, error: str | None) -> None:
            if error:
                self._say(self.verify_result, error, FAIL_COLOR)
            else:
                self._show_verify(bool(result), with_key)

        self._background(work, done)

    # ------------------------------------------------------------- tab: salt demo

    def _build_salt_tab(self) -> None:
        tab = self._new_tab("Salt demo")
        left, right = self._make_sides(
            tab, "Protected records (PBKDF2, random salt)", "Fast hash (SHA-256, no salt)"
        )
        self._salt_records: list[dict[str, Any]] = []

        # Left: the two salted records, then a password check
        self._label(left, 0, "Password:")
        self.salt_entry = ttk.Entry(left, show="*")
        self.salt_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._buttons(left, 2, ("Hash it twice", self._salt_run), ("Clear all", self._salt_clear))

        self.salt_vars = {name: tk.StringVar() for name in ("salt1", "hash1", "salt2", "hash2", "fast1", "fast2")}
        rows = [
            ("Record 1 - salt:", "salt1"),
            ("Record 1 - stored hash:", "hash1"),
            ("Record 2 - salt:", "salt2"),
            ("Record 2 - stored hash:", "hash2"),
        ]
        for index, (label, key) in enumerate(rows):
            self._label(left, 3 + index * 2, label)
            self._readonly(left, 4 + index * 2, self.salt_vars[key])

        self._label(left, 11, "Try a password against both records:")
        self.salt_guess = ttk.Entry(left, show="*")
        self.salt_guess.grid(row=12, column=0, sticky="ew", pady=(0, 8))
        self._buttons(left, 13, ("Verify", self._salt_verify))
        self.salt_verify_result = self._status(left, 14, "")
        self.salt_verify_result.configure(font=("TkDefaultFont", 10, "bold"))

        # Right: the same password without salt, then the speed measurement
        self._label(right, 0, "Hash, first time:")
        self._readonly(right, 1, self.salt_vars["fast1"])
        self._label(right, 2, "Hash, second time:")
        self._readonly(right, 3, self.salt_vars["fast2"])

        self.salt_summary = ttk.Label(
            right,
            text="Enter a password and click \"Hash it twice\".",
            wraplength=480,
            justify="left",
            foreground=INFO_COLOR,
            font=("TkDefaultFont", 10, "bold"),
        )
        self.salt_summary.grid(row=4, column=0, sticky="w", pady=(8, 12))

        self._label(right, 5, "Speed: why a plain SHA-256 is too fast for passwords")
        self._buttons(right, 6, ("Measure speed", self._salt_measure))
        self.salt_speed = ttk.Label(
            right, text="", wraplength=480, justify="left", foreground=INFO_COLOR
        )
        self.salt_speed.grid(row=7, column=0, sticky="w")

    def _salt_run(self) -> None:
        password = self.salt_entry.get()
        if not password:
            self._say(self.salt_summary, "Enter a password first.", FAIL_COLOR)
            return
        first = hash_protected(password)
        second = hash_protected(password)
        fast_first, fast_second = hash_fast(password), hash_fast(password)
        self._salt_records = [first, second]

        self.salt_vars["salt1"].set(str(first["salt"]))
        self.salt_vars["hash1"].set(str(first["hash"]))
        self.salt_vars["salt2"].set(str(second["salt"]))
        self.salt_vars["hash2"].set(str(second["hash"]))
        self.salt_vars["fast1"].set(fast_first)
        self.salt_vars["fast2"].set(fast_second)
        self._say(self.salt_verify_result, "")

        both_verify = verify_protected(password, first) and verify_protected(password, second)
        different = first["hash"] != second["hash"] and first["salt"] != second["salt"]
        same_fast = fast_first == fast_second
        if different and same_fast and both_verify:
            self._say(
                self.salt_summary,
                "Same password, two salts: the stored values are different, yet both records "
                "still verify the password. Without a salt, the hash is identical every time, "
                "so equal passwords are visible and precomputed tables work.",
                OK_COLOR,
            )
        else:
            self._say(self.salt_summary, "Unexpected result: check the integrity package.", FAIL_COLOR)

    def _salt_verify(self) -> None:
        if not self._salt_records:
            self._say(self.salt_verify_result, "Click \"Hash it twice\" first.", FAIL_COLOR)
            return
        guess = self.salt_guess.get()
        if not guess:
            self._say(self.salt_verify_result, "Enter a password to try.", FAIL_COLOR)
            return
        results = [verify_protected(guess, record) for record in self._salt_records]
        if all(results):
            self._say(self.salt_verify_result, "Correct password: both records accept it.", OK_COLOR)
        elif not any(results):
            self._say(self.salt_verify_result, "Wrong password: both records reject it.", FAIL_COLOR)
        else:
            self._say(self.salt_verify_result, "Unexpected result: check the integrity package.", FAIL_COLOR)

    @staticmethod
    def _duration(seconds: float) -> str:
        if seconds == float("inf"):
            return "infinite"
        for limit, unit, size in ((60, "s", 1), (3600, "min", 60), (86400, "h", 3600),
                                  (86400 * 365, "days", 86400)):
            if seconds < limit:
                return f"{seconds / size:,.1f} {unit}"
        return f"{seconds / (86400 * 365):,.1f} years"

    def _salt_measure(self) -> None:
        guesses = 16_777_216  # size of the password space of use case 3
        self._say(self.salt_speed, "Measuring...")

        def work() -> tuple[float, float]:
            start = time.perf_counter()
            for _ in range(1000):
                hash_fast("password")
            fast = (time.perf_counter() - start) / 1000
            start = time.perf_counter()
            for _ in range(20):
                hash_protected("password")
            slow = (time.perf_counter() - start) / 20
            return fast, slow

        def done(result: Any, error: str | None) -> None:
            if error:
                self._say(self.salt_speed, error, FAIL_COLOR)
                return
            fast, slow = result
            fast_total = estimate_slowdown(guesses, 1 / fast)
            slow_total = estimate_slowdown(guesses, 1 / slow)
            self._say(
                self.salt_speed,
                f"hash_fast (SHA-256): {fast * 1e6:,.1f} microseconds per guess\n"
                f"   -> all {guesses:,} passwords in about {self._duration(fast_total)}\n"
                f"hash_protected (PBKDF2, {ITERATIONS:,} iterations + salt): {slow * 1e3:,.1f} ms per guess\n"
                f"   -> all {guesses:,} passwords in about {self._duration(slow_total)}\n"
                f"The protected hash is about {slow / fast:,.0f} times slower for an attacker.",
                INFO_COLOR,
            )

        self._background(work, done)

    def _salt_clear(self) -> None:
        self.salt_entry.delete(0, "end")
        self.salt_guess.delete(0, "end")
        for var in self.salt_vars.values():
            var.set("")
        self._salt_records = []
        self._say(self.salt_summary, "Enter a password and click \"Hash it twice\".")
        self._say(self.salt_verify_result, "")
        self._say(self.salt_speed, "")

    # ------------------------------------------------------------ tab: tamper demo
    #
    # Shows that encryption alone does not detect a modification: a changed
    # ciphertext still decrypts, with no warning. Then two attackers:
    #   - a clumsy one changes the ciphertext only: the digest and the HMAC both detect it;
    #   - a clever one also recomputes the SHA-256 digest: the digest no longer detects
    #     anything, but the HMAC still does, because the attacker does not know the key.
    # The Encryption page exposes the sent ciphertext through the main window's
    # shared["pending_ciphertext"] state; it is not modified.

    def _build_tamper_tab(self) -> None:
        tab = self._new_tab("Tamper demo")
        left, right = self._make_sides(
            tab, "Entity A (sender): ciphertext + protection", "Entity B (receiver): in transit"
        )
        self._tamper_original = ""

        # Left: what A sent
        self._status(
            left,
            0,
            "1. Encryption page: type a message and a key, click Encrypt, then \"Send to B\".\n"
            "2. Come back here, type the shared key (for the HMAC) and click \"Load from Encryption\".",
        )
        self._buttons(left, 1, ("Load from Encryption", self._tamper_load))
        self.tamper_status = self._status(left, 10, "")
        self._label(left, 2, "Ciphertext sent by A:")
        self.tamper_text_a = tk.Text(
            left,
            height=4,
            wrap="word",
            font=MONO,
            state="disabled",
            background="#f7f8fc",
            borderwidth=1,
            relief="solid",
            highlightthickness=0,
            padx=6,
            pady=4,
        )
        self.tamper_text_a.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self._label(left, 4, "SHA-256 digest computed by A:")
        self.tamper_digest = tk.StringVar()
        self._readonly(left, 5, self.tamper_digest)
        self._label(left, 6, "Shared secret key for the HMAC (optional, type it before loading):")
        self.tamper_key = ttk.Entry(left, show="*")
        self.tamper_key.grid(row=7, column=0, sticky="ew", pady=(0, 8))
        self._label(left, 8, "HMAC-SHA-256 tag computed by A:")
        self.tamper_tag = tk.StringVar()
        self._readonly(left, 9, self.tamper_tag)

        # Right: what B received (everything here can be edited, like on a real network)
        self._label(right, 0, "Ciphertext received by B (editable):")
        self.tamper_text_b = self._text_box(right, 1)
        self._label(right, 2, "SHA-256 digest received by B (an attacker can replace it):")
        self.tamper_digest_b = tk.StringVar()
        ttk.Entry(right, textvariable=self.tamper_digest_b).grid(
            row=3, column=0, sticky="ew", pady=(0, 8)
        )
        self._label(right, 4, "HMAC tag received by B:")
        self.tamper_tag_b = tk.StringVar()
        ttk.Entry(right, textvariable=self.tamper_tag_b).grid(
            row=5, column=0, sticky="ew", pady=(0, 8)
        )
        self._buttons(right, 6, ("Attacker: change + recompute SHA-256", self._tamper_attack))
        self._label(
            right, 8, "3. Check whether the digest / HMAC detects the modification:"
        )
        self._buttons(
            right, 9, ("Check digest / HMAC", self._tamper_check), ("Clear all", self._tamper_clear)
        )
        self._label(right, 10, "Digest check:")
        self.tamper_digest_result = ttk.Label(
            right, text="-", font=("TkDefaultFont", 10, "bold"), wraplength=480, justify="left",
            foreground=INFO_COLOR,
        )
        self.tamper_digest_result.grid(row=11, column=0, sticky="w", pady=(0, 8))
        self._label(right, 12, "HMAC check:")
        self.tamper_hmac_result = ttk.Label(
            right, text="-", font=("TkDefaultFont", 10, "bold"), wraplength=480, justify="left",
            foreground=INFO_COLOR,
        )
        self.tamper_hmac_result.grid(row=13, column=0, sticky="w")

    def _main_window(self) -> Any:
        return self.winfo_toplevel()

    def _shared_state(self) -> dict[str, Any]:
        shared = getattr(self._main_window(), "shared", None)
        return shared if isinstance(shared, dict) else {}

    def _set_readonly_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        self._set_text(widget, value)
        widget.configure(state="disabled")

    def _tamper_load(self) -> None:
        shared = self._shared_state()
        ciphertext = shared.get("pending_ciphertext")
        if not ciphertext:
            self._say(
                self.tamper_status,
                "No ciphertext yet. On the Encryption page, encrypt a message and click \"Send to B\".",
                FAIL_COLOR,
            )
            return
        self._tamper_original = str(ciphertext)

        self._set_readonly_text(self.tamper_text_a, self._tamper_original)
        self.tamper_digest.set(hash_data(self._tamper_original))
        key = self.tamper_key.get()
        if key:
            self.tamper_tag.set(hmac_sha256(key, self._tamper_original))
            note = "Ciphertext loaded: digest and HMAC computed by A."
        else:
            self.tamper_tag.set("")
            note = "Ciphertext loaded: digest computed. Type a key and reload to add an HMAC."
        # What travels on the network: B receives the ciphertext, the digest and the tag.
        self._set_text(self.tamper_text_b, self._tamper_original)
        self.tamper_digest_b.set(self.tamper_digest.get())
        self.tamper_tag_b.set(self.tamper_tag.get())
        self._say(self.tamper_digest_result, "-")
        self._say(self.tamper_hmac_result, "-")
        self._say(self.tamper_status, note, OK_COLOR)

    @staticmethod
    def _letter_to_change(ciphertext: str) -> int:
        """Index of a letter well after the first characters.

        The Decryption page rejects a message whose beginning (the TOKEN marker) is
        damaged, so the change is made later in the ciphertext.
        """
        start = min(len(ciphertext) - 1, max(len(ciphertext) // 2, 6))
        for index in range(start, len(ciphertext)):
            if ciphertext[index].isascii() and ciphertext[index].isalpha():
                return index
        for index in range(start, -1, -1):
            if ciphertext[index].isascii() and ciphertext[index].isalpha():
                return index
        return start

    def _modify_ciphertext(self) -> str | None:
        """Change one letter of B's ciphertext and return a short description."""
        ciphertext = self._get_text(self.tamper_text_b)
        if not ciphertext:
            self._say(self.tamper_status, "Load a ciphertext first.", FAIL_COLOR)
            return None
        index = self._letter_to_change(ciphertext)
        char = ciphertext[index]
        if char.isascii() and char.isalpha():
            base = ord("a") if char.islower() else ord("A")
            replacement = chr(base + (ord(char) - base + 1) % 26)
        else:
            replacement = "X"
        self._set_text(
            self.tamper_text_b, ciphertext[:index] + replacement + ciphertext[index + 1:]
        )
        return f"Letter {index + 1} changed ({char} → {replacement})."

    def _tamper_attack(self) -> None:
        description = self._modify_ciphertext()
        if not description:
            return
        # The attacker knows SHA-256, so he can recompute the digest. He does not know
        # the key, so he cannot recompute the HMAC tag: it stays the one computed by A.
        self.tamper_digest_b.set(hash_data(self._get_text(self.tamper_text_b)))
        self._say(
            self.tamper_status,
            f"{description} The attacker recomputed the SHA-256 digest, "
            "but he cannot recompute the HMAC without the key.",
            INFO_COLOR,
        )

    def _tamper_check(self) -> None:
        if not self._tamper_original:
            self._say(self.tamper_status, "Load the ciphertext sent by A first.", FAIL_COLOR)
            return
        received = self._get_text(self.tamper_text_b)
        changed = received != self._tamper_original

        try:
            digest_ok = verify_digest(received, self.tamper_digest_b.get().strip())
        except ValueError as exc:
            self._say(self.tamper_digest_result, str(exc), FAIL_COLOR)
        else:
            if digest_ok and not changed:
                self._say(self.tamper_digest_result, "Digest matches: the ciphertext is unchanged.", OK_COLOR)
            elif digest_ok:
                self._say(
                    self.tamper_digest_result,
                    "Digest matches, but the ciphertext WAS changed: the attacker recomputed "
                    "the digest. The change is NOT detected.",
                    WARN_COLOR,
                )
            else:
                self._say(self.tamper_digest_result, "Digest does NOT match: the ciphertext was modified.", FAIL_COLOR)

        tag = self.tamper_tag_b.get().strip()
        if not tag:
            self._say(self.tamper_hmac_result, "No HMAC key was used.", INFO_COLOR)
            return
        try:
            hmac_ok = verify_hmac(self.tamper_key.get(), received, tag)
        except ValueError as exc:
            self._say(self.tamper_hmac_result, str(exc), FAIL_COLOR)
            return
        if hmac_ok:
            self._say(self.tamper_hmac_result, "HMAC valid: the ciphertext is unchanged.", OK_COLOR)
        else:
            self._say(
                self.tamper_hmac_result,
                "HMAC INVALID: the ciphertext was modified (the attacker does not know the key).",
                FAIL_COLOR,
            )

    def _tamper_clear(self) -> None:
        self._tamper_original = ""
        self._set_readonly_text(self.tamper_text_a, "")
        self._set_text(self.tamper_text_b, "")
        for var in (self.tamper_digest, self.tamper_tag, self.tamper_digest_b, self.tamper_tag_b):
            var.set("")
        self.tamper_key.delete(0, "end")
        self._say(self.tamper_digest_result, "-")
        self._say(self.tamper_hmac_result, "-")
        self._say(self.tamper_status, "")
"""Attacks page: unprotected vs protected target, brute force and dictionary,
side by side, to compare the real effectiveness of the protections (Part 3).
"""

from __future__ import annotations

import random
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from gui.pages.base_page import BasePage
from passwords import generators
from passwords.brute_force import force_brute
from passwords.dictionary import COMMON_PASSWORDS, dictionary_attack
from passwords.protection import LOCK_SECONDS, MAX_FAILURES, Lockout, make_checker, make_plain_checker

# A "Run" button is only enabled when the estimated worst-case duration for
# that attack is below this cap, so clicking it never freezes the GUI for a
# long time. Above the cap, only the estimated time is shown.
LIVE_CAP_SECONDS = 60.0

# Number of candidates used to measure the real speed of a checker, so the
# estimate for the full space is based on an actual measurement, not a guess.
# This benchmark NEVER goes through the Lockout - only the raw check speed.
BENCHMARK_SAMPLE = 2_000


def _format_duration(seconds: float) -> str:
    """Format a duration in seconds as a short, human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.1f} ms"
    if seconds < 60:
        return f"{seconds:.2f} s"
    if seconds < 3600:
        return f"{seconds / 60:.2f} min"
    if seconds < 86400:
        return f"{seconds / 3600:.2f} h"
    if seconds < 365 * 86400:
        return f"{seconds / 86400:.2f} days"
    return f"{seconds / (365 * 86400):,.0f} years"


def _benchmark_rate(check: Callable[[str], bool], alphabet: str, length: int) -> float:
    """Measure how many checks per second `check` can sustain.

    IMPORTANT: `check` must be a "raw" checker with no Lockout involved, or
    this will block for a very long time (Lockout introduces real sleeps).
    """
    n = min(BENCHMARK_SAMPLE, len(alphabet) ** length)
    sample = ["".join(random.choice(alphabet) for _ in range(length)) for _ in range(n)]
    start = time.perf_counter()
    for cand in sample:
        check(cand)
    elapsed = time.perf_counter() - start
    if elapsed <= 0:
        return 1_000_000.0  # avoid division by zero on a very fast checker
    return n / elapsed


def _lockout_time_estimate(attempts: int) -> float:
    """Worst-case time (seconds) to make `attempts` online attempts through
    the Lockout: every MAX_FAILURES wrong attempts costs one LOCK_SECONDS
    wait. The encryption cost itself is negligible next to the 30 s wait.
    """
    cycles = attempts // MAX_FAILURES
    return cycles * LOCK_SECONDS


class AttacksPage(BasePage):
    """Two-column comparison: attack with no protection vs. attack with protection."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, "Attacks", "")

        for child in self.winfo_children():
            if child.winfo_class() == "Label" and child.cget("text") == "":
                child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.target_var = tk.StringVar(value="")
        self._running = False

        self.page_frame = self._build_scrollable_area()
        self.page_frame.columnconfigure(0, weight=1)

        self._build_intro_section()
        self._build_target_section()
        self._build_columns()
        self._refresh_target()

    # --- scrolling ----------------------------------------------------------

    def _build_scrollable_area(self) -> ttk.Frame:
        """Create the content frame; scrolling is handled by the shared page shell."""
        self.rowconfigure(1, weight=1)
        container = ttk.Frame(self, padding=(10, 6))
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)
        return container

    # --- shared state -----------------------------------------------------

    def _shared(self) -> dict[str, Any]:
        top: Any = self.winfo_toplevel()
        shared = getattr(top, "shared", None)
        return shared if isinstance(shared, dict) else {}

    # --- layout: intro ------------------------------------------------------

    def _build_intro_section(self) -> None:
        intro = ttk.Frame(self.page_frame, padding=(0, 0, 0, 10))
        intro.grid(row=0, column=0, sticky="ew")
        intro.columnconfigure(0, weight=1)
        text = (
            "Left: the password is stored in clear text, with no lockout - the "
            "attacker compares each guess directly. Right: the password is "
            "protected by encryption (Part 3) and login attempts are limited "
            f"({MAX_FAILURES} failures -> {LOCK_SECONDS:.0f} s lockout). "
            "A \"Run\" button is only clickable when the attack would finish "
            f"in under {LIVE_CAP_SECONDS:.0f} s - otherwise rely on the "
            "estimated time shown above it."
        )
        ttk.Label(intro, text=text, wraplength=1000, justify="left", foreground="#52616f").grid(
            row=0, column=0, sticky="w"
        )

    # --- layout: target -----------------------------------------------------

    def _build_target_section(self) -> None:
        frame = ttk.LabelFrame(self.page_frame, text="Target", padding=(10, 8))
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, textvariable=self.target_var, wraplength=1000, justify="left").grid(
            row=0, column=0, sticky="w"
        )
        self.refresh_button = ttk.Button(frame, text="Refresh target", command=self._refresh_target)
        self.refresh_button.grid(row=1, column=0, sticky="w", pady=(8, 0))

    # --- layout: two columns -------------------------------------------------

    def _build_columns(self) -> None:
        main = ttk.Frame(self.page_frame)
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1, uniform="cols")
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=1, uniform="cols")
        main.rowconfigure(0, weight=1)

        unprot_frame = ttk.LabelFrame(main, text="Without protection (plain text)", padding=(10, 8))
        unprot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        unprot_frame.columnconfigure(0, weight=1)

        ttk.Separator(main, orient="vertical").grid(row=0, column=1, sticky="ns", padx=(0, 6))

        prot_frame = ttk.LabelFrame(
            main, text="With protection (encryption + lockout)", padding=(10, 8)
        )
        prot_frame.grid(row=0, column=2, sticky="nsew")
        prot_frame.columnconfigure(0, weight=1)

        self.unprot = self._build_side(unprot_frame, "unprotected")
        self.prot = self._build_side(prot_frame, "protected")

    def _build_side(self, parent: ttk.LabelFrame, side_id: str) -> dict[str, Any]:
        """Build one side (brute force + dictionary) and return its widget vars."""
        vars_: dict[str, Any] = {}

        ttk.Label(parent, text="Search space:").grid(row=0, column=0, sticky="w")
        vars_["space"] = tk.StringVar(value="")
        ttk.Entry(parent, textvariable=vars_["space"], state="readonly").grid(
            row=1, column=0, sticky="ew", pady=(0, 6)
        )

        # --- Brute force controls ---
        ttk.Label(parent, text="Brute force", font=("", 10, "bold")).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(parent, text="Estimated time (worst case, full space):").grid(
            row=3, column=0, sticky="w"
        )
        vars_["bf_estimate"] = tk.StringVar(value="")
        ttk.Label(parent, textvariable=vars_["bf_estimate"], foreground="#52616f").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        vars_["bf_button"] = ttk.Button(
            parent, text="Run brute force", command=lambda: self._start_attack(side_id, "brute")
        )
        vars_["bf_button"].grid(row=5, column=0, sticky="w", pady=(2, 2))
        vars_["bf_status"] = tk.StringVar(value="")
        vars_["bf_status_label"] = ttk.Label(parent, textvariable=vars_["bf_status"], foreground="#0f5132")
        vars_["bf_status_label"].grid(row=6, column=0, sticky="w", pady=(0, 2))
        vars_["bf_result"] = tk.StringVar(value="")
        vars_["bf_attempts"] = tk.StringVar(value="")
        vars_["bf_time"] = tk.StringVar(value="")
        for i, (label, key) in enumerate(
            [("Found:", "bf_result"), ("Attempts:", "bf_attempts"), ("Real time:", "bf_time")]
        ):
            ttk.Label(parent, text=label).grid(row=7 + i, column=0, sticky="w")
            ttk.Entry(parent, textvariable=vars_[key], state="readonly").grid(
                row=7 + i, column=0, sticky="ew"
            )

        # --- Dictionary controls ---
        ttk.Separator(parent, orient="horizontal").grid(row=10, column=0, sticky="ew", pady=8)
        ttk.Label(parent, text="Dictionary attack", font=("", 10, "bold")).grid(
            row=11, column=0, sticky="w"
        )
        vars_["dict_size"] = tk.StringVar(value="")
        ttk.Label(parent, textvariable=vars_["dict_size"], foreground="#52616f").grid(
            row=12, column=0, sticky="w"
        )
        vars_["dict_estimate"] = tk.StringVar(value="")
        ttk.Label(parent, textvariable=vars_["dict_estimate"], foreground="#52616f").grid(
            row=13, column=0, sticky="w", pady=(0, 4)
        )
        vars_["dict_button"] = ttk.Button(
            parent, text="Run dictionary", command=lambda: self._start_attack(side_id, "dictionary")
        )
        vars_["dict_button"].grid(row=14, column=0, sticky="w", pady=(2, 2))
        vars_["dict_status"] = tk.StringVar(value="")
        vars_["dict_status_label"] = ttk.Label(
            parent, textvariable=vars_["dict_status"], foreground="#0f5132"
        )
        vars_["dict_status_label"].grid(row=15, column=0, sticky="w", pady=(0, 2))
        vars_["dict_result"] = tk.StringVar(value="")
        vars_["dict_attempts"] = tk.StringVar(value="")
        vars_["dict_time"] = tk.StringVar(value="")
        for i, (label, key) in enumerate(
            [("Found:", "dict_result"), ("Attempts:", "dict_attempts"), ("Real time:", "dict_time")]
        ):
            ttk.Label(parent, text=label).grid(row=16 + i, column=0, sticky="w")
            ttk.Entry(parent, textvariable=vars_[key], state="readonly").grid(
                row=16 + i, column=0, sticky="ew"
            )

        return vars_

    # --- checkers ---------------------------------------------------------

    def _build_raw_checkers(self, record: dict, password: str | None):
        """Return (plain_check, encrypted_check_no_lockout).

        Both are safe to benchmark: no sleeping, no Lockout involved.
        """
        plain_check = make_plain_checker(password) if password else None
        encrypted_check = make_checker(record)
        return plain_check, encrypted_check

    def _make_live_protected_check(self, record: dict) -> Callable[[str], bool]:
        """Build a FRESH protected checker (encryption + real Lockout) for an
        actual live run. A new Lockout is created each time so previous runs
        don't leave the account locked.
        """
        enc_check = make_checker(record)
        lockout = Lockout()

        def check(candidate: str) -> bool:
            ok = enc_check(candidate)
            try:
                return lockout.record(ok)
            except ValueError:
                time.sleep(lockout.remaining())
                ok = enc_check(candidate)
                return lockout.record(ok)

        return check

    # --- target handling ------------------------------------------------

    def _refresh_target(self) -> None:
        shared = self._shared()
        use_case = shared.get("use_case")
        record = shared.get("record")
        password = shared.get("password")  # plain-text password, if the app kept it

        if use_case is None or record is None:
            self.target_var.set(
                "No target yet. Go to the Passwords page, store a password, "
                "then click \"Send to Attacks\"."
            )
            for side in (self.unprot, self.prot):
                side["bf_button"].configure(state="disabled")
                side["dict_button"].configure(state="disabled")
            return

        spec = generators.USE_CASES[use_case]
        alphabet = str(spec["alphabet"])
        length = int(spec["length"])
        total = len(alphabet) ** length
        cipher = record.get("cipher", "cipher")
        ciphertext = record.get("ciphertext", "")

        self.target_var.set(
            f"Use case {use_case}: {length} characters from an alphabet of "
            f"{len(alphabet)} symbols -> {total:,} possible passwords.\n"
            f"Protected ciphertext ({cipher}): {ciphertext}"
        )
        if password is None:
            self.target_var.set(
                self.target_var.get()
                + "\nNote: plain-text password not available - the 'without "
                "protection' column cannot run. Pass it in shared['password']."
            )

        plain_check, encrypted_check = self._build_raw_checkers(record, password)
        words = [
            w for w in COMMON_PASSWORDS.get(use_case, [])
            if len(w) == length and all(c in alphabet for c in w)
        ]

        self._current = {
            "use_case": use_case,
            "alphabet": alphabet,
            "length": length,
            "total": total,
            "record": record,
            "plain_check": plain_check,
            "words_count": len(words),
        }

        # --- unprotected side ---
        self.unprot["space"].set(f"{total:,} possible passwords")
        self.unprot["dict_size"].set(f"Dictionary: {len(words)} words")
        if plain_check is None:
            self.unprot["bf_estimate"].set("n/a (no plain password)")
            self.unprot["dict_estimate"].set("n/a (no plain password)")
            self.unprot["bf_button"].configure(state="disabled")
            self.unprot["dict_button"].configure(state="disabled")
        else:
            rate = _benchmark_rate(plain_check, alphabet, length)
            bf_seconds = total / rate
            dict_seconds = len(words) / rate if words else 0.0
            self.unprot["bf_estimate"].set(_format_duration(bf_seconds))
            self.unprot["dict_estimate"].set(_format_duration(dict_seconds))
            self.unprot["bf_button"].configure(
                state="normal" if bf_seconds <= LIVE_CAP_SECONDS else "disabled"
            )
            self.unprot["dict_button"].configure(
                state="normal" if dict_seconds <= LIVE_CAP_SECONDS else "disabled"
            )

        # --- protected side ---
        self.prot["space"].set(f"{total:,} possible passwords")
        self.prot["dict_size"].set(f"Dictionary: {len(words)} words")
        bf_lockout_seconds = _lockout_time_estimate(total)
        dict_lockout_seconds = _lockout_time_estimate(len(words))
        self.prot["bf_estimate"].set(
            f"{_format_duration(bf_lockout_seconds)} (lockout-limited)"
        )
        self.prot["dict_estimate"].set(
            f"{_format_duration(dict_lockout_seconds)} (lockout-limited)"
        )
        self.prot["bf_button"].configure(
            state="normal" if bf_lockout_seconds <= LIVE_CAP_SECONDS else "disabled"
        )
        self.prot["dict_button"].configure(
            state="normal" if dict_lockout_seconds <= LIVE_CAP_SECONDS else "disabled"
        )

    # --- running the attacks --------------------------------------------

    def _start_attack(self, side_id: str, method: str) -> None:
        if self._running or not hasattr(self, "_current"):
            return

        side = self.unprot if side_id == "unprotected" else self.prot
        if side_id == "unprotected":
            check = self._current["plain_check"]
        else:
            check = self._make_live_protected_check(self._current["record"])
        if check is None:
            return

        use_case = self._current["use_case"]
        status_key = "bf_status" if method == "brute" else "dict_status"
        self._set_status(side, status_key, f"Running {method}...")

        self._running = True
        for s in (self.unprot, self.prot):
            s["bf_button"].configure(state="disabled")
            s["dict_button"].configure(state="disabled")
        self.refresh_button.configure(state="disabled")

        thread = threading.Thread(
            target=self._run_attack_thread, args=(use_case, check, method, side_id), daemon=True
        )
        thread.start()

    def _run_attack_thread(self, use_case: int, check, method: str, side_id: str) -> None:
        try:
            start = time.perf_counter()
            if method == "brute":
                found, attempts = force_brute(use_case, check)
            else:
                found, attempts = dictionary_attack(use_case, check)
            elapsed = time.perf_counter() - start
        except Exception as exc:  # noqa: BLE001 - surface errors to the GUI
            self.after(0, self._attack_failed, side_id, method, str(exc))
            return
        self.after(0, self._attack_done, side_id, method, found, attempts, elapsed)

    def _attack_done(self, side_id: str, method: str, found, attempts: int, elapsed: float) -> None:
        self._running = False
        side = self.unprot if side_id == "unprotected" else self.prot
        prefix = "bf" if method == "brute" else "dict"
        side[f"{prefix}_attempts"].set(f"{attempts:,}")
        side[f"{prefix}_time"].set(_format_duration(elapsed))
        if found:
            side[f"{prefix}_result"].set(found)
            self._set_status(
                side, f"{prefix}_status", f"Found in {attempts:,} attempts ({elapsed:.3f} s)."
            )
        else:
            side[f"{prefix}_result"].set("(not found)")
            self._set_status(side, f"{prefix}_status", f"Not found ({attempts:,} tried).", is_error=True)
        self._reenable_buttons()

    def _attack_failed(self, side_id: str, method: str, message: str) -> None:
        self._running = False
        side = self.unprot if side_id == "unprotected" else self.prot
        key = "bf_status" if method == "brute" else "dict_status"
        self._set_status(side, key, f"Failed: {message}", is_error=True)
        self._reenable_buttons()

    def _reenable_buttons(self) -> None:
        self._refresh_target()
        self.refresh_button.configure(state="normal")

    def _set_status(self, side: dict[str, Any], key: str, message: str, is_error: bool = False) -> None:
        side[key].set(message)
        side[f"{key}_label"].configure(foreground="#c92a2a" if is_error else "#0f5132")
"""Attacks page: brute-force and dictionary attacks side by side, for comparison."""

from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui.pages.base_page import BasePage
from passwords import generators
from passwords.brute_force import force_brute
from passwords.dictionary import COMMON_PASSWORDS, dictionary_attack
from passwords.protection import hash_protected, make_checker, verify_protected

# Above this many candidates, running the attack live would freeze the GUI
# for too long, so the button is disabled (the time estimate is still shown).
MAX_FAST_SPACE = 50_000_000
MAX_PROTECTED_SPACE = 100_000  # protected checks are ~100k times slower (PBKDF2)


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


class AttacksPage(BasePage):
    """Attacker-side page: brute-force vs. dictionary, against the stored target."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, "Attacks", "")

        for child in self.winfo_children():
            if child.winfo_class() == "Label" and child.cget("text") == "":
                child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.target_var = tk.StringVar(value="")

        # Brute force side
        self.bf_space_var = tk.StringVar(value="")
        self.bf_est_fast_var = tk.StringVar(value="")
        self.bf_est_protected_var = tk.StringVar(value="")
        self.bf_result_var = tk.StringVar(value="")
        self.bf_attempts_var = tk.StringVar(value="")
        self.bf_time_var = tk.StringVar(value="")
        self.bf_status_var = tk.StringVar(value="")

        # Dictionary side
        self.dict_size_var = tk.StringVar(value="")
        self.dict_result_var = tk.StringVar(value="")
        self.dict_attempts_var = tk.StringVar(value="")
        self.dict_time_var = tk.StringVar(value="")
        self.dict_status_var = tk.StringVar(value="")

        self._running = False

        # One-time benchmark of how fast each kind of check runs on this
        # machine, used to turn "N possible passwords" into an estimated time.
        self._fast_rate = self._estimate_rate_fast()
        self._protected_rate = self._estimate_rate_protected()

        self.page_frame = ttk.Frame(self, padding=(10, 6))
        self.page_frame.grid(row=1, column=0, sticky="nsew")
        self.page_frame.columnconfigure(0, weight=1)
        self.page_frame.rowconfigure(2, weight=1)

        self._build_intro_section()
        self._build_target_section()
        self._build_comparison_section()
        self._refresh_target()

    # --- one-time speed benchmark ---------------------------------------

    @staticmethod
    def _estimate_rate_fast() -> float:
        """Measure how many fast (SHA-256) checks this machine can do per second."""
        sample = 2000
        start = time.perf_counter()
        for i in range(sample):
            generators.hash_fast(str(i))
        elapsed = time.perf_counter() - start
        return sample / elapsed if elapsed > 0 else float("inf")

    @staticmethod
    def _estimate_rate_protected() -> float:
        """Measure how many protected (PBKDF2) checks this machine can do per second."""
        sample = 5
        password = "benchmark"
        record = hash_protected(password)
        start = time.perf_counter()
        for _ in range(sample):
            verify_protected(password, record)
        elapsed = time.perf_counter() - start
        return sample / elapsed if elapsed > 0 else float("inf")

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
            "Brute force tries every possible password in the search space, one by "
            "one, until it finds a match - it always succeeds eventually, but can "
            "take an impractical amount of time when the search space is large.\n"
            "Dictionary attack only tries a short list of common/predictable "
            "passwords - it is much faster, but only succeeds if the real password "
            "happens to be in that list."
        )
        ttk.Label(
            intro,
            text=text,
            wraplength=900,
            justify="left",
            foreground="#52616f",
        ).grid(row=0, column=0, sticky="w")

    # --- layout: target ---------------------------------------------------

    def _build_target_section(self) -> None:
        frame = ttk.LabelFrame(self.page_frame, text="Target", padding=(10, 8))
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame, textvariable=self.target_var, wraplength=900, justify="left"
        ).grid(row=0, column=0, sticky="w")

        self.refresh_button = ttk.Button(
            frame, text="Refresh target", command=self._refresh_target
        )
        self.refresh_button.grid(row=1, column=0, sticky="w", pady=(8, 0))

    # --- layout: brute force vs dictionary, side by side -------------------

    def _build_comparison_section(self) -> None:
        main = ttk.Frame(self.page_frame)
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1, uniform="attack_sides")
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=1, uniform="attack_sides")
        main.rowconfigure(0, weight=1)

        bf_frame = ttk.LabelFrame(main, text="Brute force", padding=(10, 8))
        bf_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        bf_frame.columnconfigure(0, weight=1)

        ttk.Separator(main, orient="vertical").grid(row=0, column=1, sticky="ns", padx=(0, 6))

        dict_frame = ttk.LabelFrame(main, text="Dictionary attack", padding=(10, 8))
        dict_frame.grid(row=0, column=2, sticky="nsew")
        dict_frame.columnconfigure(0, weight=1)

        self._build_brute_force_side(bf_frame)
        self._build_dictionary_side(dict_frame)

    def _build_brute_force_side(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(parent, text="Search space:").grid(row=0, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.bf_space_var, state="readonly").grid(
            row=1, column=0, sticky="ew", pady=(0, 8)
        )

        ttk.Label(parent, text="Estimated time (fast hash):").grid(row=2, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.bf_est_fast_var, state="readonly").grid(
            row=3, column=0, sticky="ew", pady=(0, 4)
        )

        ttk.Label(parent, text="Estimated time (protected record):").grid(
            row=4, column=0, sticky="w"
        )
        ttk.Entry(parent, textvariable=self.bf_est_protected_var, state="readonly").grid(
            row=5, column=0, sticky="ew", pady=(0, 8)
        )

        btn_row = ttk.Frame(parent)
        btn_row.grid(row=6, column=0, sticky="ew", pady=(0, 6))
        self.bf_fast_button = ttk.Button(
            btn_row, text="Run (fast hash)", command=lambda: self._start_attack("fast", "brute")
        )
        self.bf_fast_button.pack(side="left")
        self.bf_protected_button = ttk.Button(
            btn_row,
            text="Run (protected record)",
            command=lambda: self._start_attack("protected", "brute"),
        )
        self.bf_protected_button.pack(side="left", padx=(8, 0))

        self.bf_status_label = ttk.Label(parent, textvariable=self.bf_status_var, foreground="#0f5132")
        self.bf_status_label.grid(row=7, column=0, sticky="w", pady=(0, 8))

        rows = [
            ("Password found:", self.bf_result_var),
            ("Attempts:", self.bf_attempts_var),
            ("Elapsed time:", self.bf_time_var),
        ]
        for i, (label_text, var) in enumerate(rows):
            ttk.Label(parent, text=label_text).grid(row=8 + i, column=0, sticky="w", pady=(0, 2))
            ttk.Entry(parent, textvariable=var, state="readonly").grid(
                row=8 + i, column=0, sticky="ew"
            )
        # (labels and entries share rows visually above; keep a clean stack)

    def _build_dictionary_side(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(parent, text="Dictionary size:").grid(row=0, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.dict_size_var, state="readonly").grid(
            row=1, column=0, sticky="ew", pady=(0, 8)
        )

        # Spacer rows so both columns' buttons line up visually.
        ttk.Label(parent, text="").grid(row=2, column=0)
        ttk.Label(parent, text="").grid(row=3, column=0)
        ttk.Label(parent, text="").grid(row=4, column=0)
        ttk.Label(parent, text="").grid(row=5, column=0, pady=(0, 8))

        btn_row = ttk.Frame(parent)
        btn_row.grid(row=6, column=0, sticky="ew", pady=(0, 6))
        self.dict_fast_button = ttk.Button(
            btn_row, text="Run (fast hash)", command=lambda: self._start_attack("fast", "dictionary")
        )
        self.dict_fast_button.pack(side="left")
        self.dict_protected_button = ttk.Button(
            btn_row,
            text="Run (protected record)",
            command=lambda: self._start_attack("protected", "dictionary"),
        )
        self.dict_protected_button.pack(side="left", padx=(8, 0))

        self.dict_status_label = ttk.Label(
            parent, textvariable=self.dict_status_var, foreground="#0f5132"
        )
        self.dict_status_label.grid(row=7, column=0, sticky="w", pady=(0, 8))

        rows = [
            ("Password found:", self.dict_result_var),
            ("Attempts:", self.dict_attempts_var),
            ("Elapsed time:", self.dict_time_var),
        ]
        for i, (label_text, var) in enumerate(rows):
            ttk.Label(parent, text=label_text).grid(row=8 + i, column=0, sticky="w", pady=(0, 2))
            ttk.Entry(parent, textvariable=var, state="readonly").grid(
                row=8 + i, column=0, sticky="ew"
            )

    # --- target handling ------------------------------------------------

    def _refresh_target(self) -> None:
        shared = self._shared()
        use_case = shared.get("use_case")
        fast_hash = shared.get("fast_hash")
        record = shared.get("record")

        if use_case is None or fast_hash is None or record is None:
            self.target_var.set(
                "No target yet. Go to the Passwords page, store a password, "
                "then click \"Send to Attacks\"."
            )
            self.bf_fast_button.configure(state="disabled")
            self.bf_protected_button.configure(state="disabled")
            self.dict_fast_button.configure(state="disabled")
            self.dict_protected_button.configure(state="disabled")
            self.bf_space_var.set("")
            self.bf_est_fast_var.set("")
            self.bf_est_protected_var.set("")
            self.dict_size_var.set("")
            return

        spec = generators.USE_CASES[use_case]
        alphabet = str(spec["alphabet"])
        length = int(spec["length"])
        total = len(alphabet) ** length

        self.target_var.set(
            f"Use case {use_case}: {length} characters from an alphabet of "
            f"{len(alphabet)} symbols -> {total:,} possible passwords.\n"
            f"Stolen fast hash: {fast_hash}"
        )

        # --- brute force side ---
        self.bf_space_var.set(f"{total:,} possible passwords")
        self.bf_est_fast_var.set(_format_duration(total / self._fast_rate))
        self.bf_est_protected_var.set(_format_duration(total / self._protected_rate))

        self.bf_fast_button.configure(state="normal" if total <= MAX_FAST_SPACE else "disabled")
        self.bf_protected_button.configure(
            state="normal" if total <= MAX_PROTECTED_SPACE else "disabled"
        )

        if total > MAX_FAST_SPACE:
            self._set_bf_status(
                "Search space too large to run live - see the estimated time above.", is_error=True
            )
        else:
            self._set_bf_status("Target ready.")

        # --- dictionary side ---
        words = COMMON_PASSWORDS.get(use_case, [])
        coverage = (len(words) / total * 100) if total else 0.0
        self.dict_size_var.set(f"{len(words)} words ({coverage:.4f}% of the search space)")
        self.dict_fast_button.configure(state="normal")
        self.dict_protected_button.configure(state="normal")
        self._set_dict_status("Target ready.")

    # --- running the attacks --------------------------------------------

    def _start_attack(self, kind: str, method: str) -> None:
        if self._running:
            return

        shared = self._shared()
        use_case = shared.get("use_case")
        fast_hash = shared.get("fast_hash")
        record = shared.get("record")
        if use_case is None or fast_hash is None or record is None:
            self._set_error_both("No target. Store a password on the Passwords page first.")
            return

        target = fast_hash if kind == "fast" else record
        target_label = "fast hash" if kind == "fast" else "protected record"

        self._running = True
        self.bf_fast_button.configure(state="disabled")
        self.bf_protected_button.configure(state="disabled")
        self.dict_fast_button.configure(state="disabled")
        self.dict_protected_button.configure(state="disabled")
        self.refresh_button.configure(state="disabled")

        if method == "brute":
            self._set_bf_status(f"Running brute force against the {target_label}...")
            self.bf_result_var.set("")
            self.bf_attempts_var.set("")
            self.bf_time_var.set("")
        else:
            self._set_dict_status(f"Running dictionary attack against the {target_label}...")
            self.dict_result_var.set("")
            self.dict_attempts_var.set("")
            self.dict_time_var.set("")

        thread = threading.Thread(
            target=self._run_attack_thread, args=(use_case, target, method), daemon=True
        )
        thread.start()

    def _run_attack_thread(
        self, use_case: int, target: str | dict[str, Any], method: str
    ) -> None:
        try:
            check = make_checker(target)
            start = time.perf_counter()
            if method == "brute":
                found, attempts = force_brute(use_case, check)
            else:
                found, attempts = dictionary_attack(use_case, check)
            elapsed = time.perf_counter() - start
        except Exception as exc:  # noqa: BLE001 - surface any error to the GUI
            self.after(0, self._attack_failed, str(exc), method)
            return
        self.after(0, self._attack_done, found, attempts, elapsed, method)

    def _attack_done(
        self, found: str | None, attempts: int, elapsed: float, method: str
    ) -> None:
        self._running = False
        self._refresh_target()

        if method == "brute":
            self.bf_attempts_var.set(f"{attempts:,}")
            self.bf_time_var.set(_format_duration(elapsed))
            if found:
                self.bf_result_var.set(found)
                self._set_bf_status(f"Password recovered in {attempts:,} attempts ({elapsed:.3f} s).")
            else:
                self.bf_result_var.set("(not found)")
                self._set_bf_status(f"Not found after {attempts:,} attempts.", is_error=True)
        else:
            self.dict_attempts_var.set(f"{attempts:,}")
            self.dict_time_var.set(_format_duration(elapsed))
            if found:
                self.dict_result_var.set(found)
                self._set_dict_status(
                    f"Password recovered in {attempts:,} attempts ({elapsed:.3f} s)."
                )
            else:
                self.dict_result_var.set("(not found)")
                self._set_dict_status(
                    f"Not in the dictionary ({attempts:,} words tried).", is_error=True
                )

    def _attack_failed(self, message: str, method: str) -> None:
        self._running = False
        self._refresh_target()
        if method == "brute":
            self._set_bf_status(f"Attack failed: {message}", is_error=True)
        else:
            self._set_dict_status(f"Attack failed: {message}", is_error=True)

    # --- status -----------------------------------------------------------

    def _set_bf_status(self, message: str, is_error: bool = False) -> None:
        self.bf_status_var.set(message)
        self.bf_status_label.configure(foreground="#c92a2a" if is_error else "#0f5132")

    def _set_dict_status(self, message: str, is_error: bool = False) -> None:
        self.dict_status_var.set(message)
        self.dict_status_label.configure(foreground="#c92a2a" if is_error else "#0f5132")

    def _set_error_both(self, message: str) -> None:
        self._set_bf_status(message, is_error=True)
        self._set_dict_status(message, is_error=True)
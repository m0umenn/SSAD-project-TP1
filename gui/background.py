"""Background execution helper for Tkinter callbacks."""

from __future__ import annotations

import threading
from typing import Any, Callable


def run_in_background(task: Callable[[], Any], on_done: Callable[[Any], None], on_error: Callable[[BaseException], None] | None = None, root: Any = None) -> threading.Thread:
    """Run a task in a background thread and return its result to Tkinter safely.

    This is meant for long brute-force attacks so the window does not freeze.
    """

    if root is None:
        import tkinter as tk

        root = tk._get_default_root()
        if root is None:
            raise RuntimeError("A Tk root window is required.")

    def worker() -> None:
        try:
            result = task()
        except BaseException as exc:  # noqa: BLE001
            if on_error is not None:
                root.after(0, on_error, exc)
            else:
                raise
        else:
            root.after(0, on_done, result)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread
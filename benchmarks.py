"""Timing helper for SSAD Toolkit ciphers."""

from __future__ import annotations

import time
from typing import Any, Callable

from crypto import caesar, hill, playfair


def time_it(func: Callable[..., Any], *args: Any, repeat: int = 3) -> tuple[Any, float]:
    """Run a function several times and return the last result plus average runtime."""

    last_result: Any = None
    durations: list[float] = []

    for _ in range(repeat):
        start = time.perf_counter()
        last_result = func(*args)
        durations.append(time.perf_counter() - start)

    average_seconds = sum(durations) / len(durations) if durations else 0.0
    return last_result, average_seconds


def _benchmark_entry(label: str, func: Callable[..., Any], *args: Any) -> tuple[str, str] | None:
    try:
        _, avg_seconds = time_it(func, *args)
    except NotImplementedError:
        return None
    return label, f"{avg_seconds:.6f}s"


def main() -> None:
    """Print a small benchmark table for implemented cipher functions."""

    entries = [
        ("Caesar encrypt", caesar.encrypt, "HELLO", 3),
        ("Caesar decrypt", caesar.decrypt, "KHOOR", 3),
        ("Playfair encrypt", playfair.encrypt, "HELLO", "MONARCHY"),
        ("Playfair decrypt", playfair.decrypt, "CFSUPM", "MONARCHY"),
        ("Hill encrypt", hill.encrypt, "HELLO", [[1, 0], [0, 1]]),
        ("Hill decrypt", hill.decrypt, "HELLOX", [[1, 0], [0, 1]]),
    ]

    # Password workloads in passwords/brute_force.py and passwords/dictionary.py will be benchmarked here later.
    rows = [row for row in (_benchmark_entry(label, func, *args) for label, func, *args in entries) if row is not None]

    if not rows:
        print("No implemented cipher functions available yet.")
        return

    print(f"{'Function':<20} | Result")
    print(f"{'-' * 20}-+-{'-' * 14}")
    for label, result in rows:
        print(f"{label:<20} | {result}")


if __name__ == "__main__":
    main()
"""Shared base class for all toolkit pages."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class BasePage(ttk.Frame):
    """Simple page container with a consistent title area."""

    def __init__(self, parent: tk.Widget, title: str, placeholder_text: str) -> None:
        super().__init__(parent, style="Content.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        title_label = ttk.Label(self, text=title, style="PageTitle.TLabel")
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 14))

        body = ttk.Label(
            self,
            text=placeholder_text,
            style="PageBody.TLabel",
            wraplength=650,
            justify="left",
        )
        body.grid(row=1, column=0, sticky="nw")
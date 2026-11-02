"""Reusable scrollable containers for Tkinter pages."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """A frame whose contents can scroll vertically and horizontally."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, style="Content.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        background = ttk.Style(self).lookup("Content.TFrame", "background") or "#f3f5fa"
        self.canvas = tk.Canvas(
            self,
            background=background,
            borderwidth=0,
            highlightthickness=0,
            xscrollincrement=24,
            yscrollincrement=24,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.vertical_scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        self.horizontal_scrollbar = ttk.Scrollbar(
            self, orient="horizontal", command=self.canvas.xview
        )
        self.horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        self.horizontal_scrollbar.grid_remove()
        self._horizontal_visible = False
        self.canvas.configure(
            xscrollcommand=self.horizontal_scrollbar.set,
            yscrollcommand=self.vertical_scrollbar.set,
        )

        self.inner = ttk.Frame(self.canvas, style="Content.TFrame")
        self.inner.columnconfigure(0, weight=1)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner._scroll_canvas = self.canvas
        self.canvas._scroll_canvas = self.canvas

        self.inner.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_inner)

    def _update_scroll_region(self, _event: tk.Event | None = None) -> None:
        width = max(self.canvas.winfo_width(), self.inner.winfo_reqwidth())
        self.canvas.itemconfigure(self.inner_id, width=width)
        bounds = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=bounds)
        needs_horizontal_scroll = bool(
            bounds and bounds[2] - bounds[0] > self.canvas.winfo_width() + 1
        )
        if needs_horizontal_scroll != self._horizontal_visible:
            if needs_horizontal_scroll:
                self.horizontal_scrollbar.grid()
            else:
                self.horizontal_scrollbar.grid_remove()
            self._horizontal_visible = needs_horizontal_scroll

    def _resize_inner(self, event: tk.Event) -> None:
        width = max(event.width, self.inner.winfo_reqwidth())
        self.canvas.itemconfigure(self.inner_id, width=width)
        self._update_scroll_region()

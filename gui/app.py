"""Main window and page switching logic for SSAD Toolkit."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui.pages.attacks_page import AttacksPage
from gui.pages.encryption_page import EncryptionPage
from gui.pages.integrity_page import IntegrityPage
from gui.pages.passwords_page import PasswordsPage


PAGE_DEFINITIONS = [
    ("Encryption / Decryption", EncryptionPage),
    ("Passwords", PasswordsPage),
    ("Attacks", AttacksPage),
    ("Authenticity / Integrity", IntegrityPage),
]


class SSADToolkitApp(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title("SSAD Toolkit")
        self.geometry("1000x650")
        self.resizable(True, True)

        self._setup_style()

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=(12, 14))
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ttk.Frame(self, style="Content.TFrame", padding=(10, 6))
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self._pages: dict[str, ttk.Frame] = {}
        self._buttons: dict[str, ttk.Button] = {}
        self._active_page_name: str | None = None

        self._build_sidebar()
        self._build_pages()
        self._size_window_to_content()
        self.show_page(PAGE_DEFINITIONS[0][0])

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background="#f4f6f8")
        style.configure("Sidebar.TFrame", background="#243447")
        style.configure("Content.TFrame", background="#f4f6f8")

        style.configure(
            "Sidebar.TButton",
            background="#243447",
            foreground="#e8eef5",
            padding=(14, 11),
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10),
            anchor="w",
        )
        style.map(
            "Sidebar.TButton",
            background=[("active", "#31475f")],
            foreground=[("disabled", "#b4c0cc")],
        )

        style.configure(
            "SidebarActive.TButton",
            background="#3b5c7a",
            foreground="#ffffff",
            padding=(14, 11),
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        style.map(
            "SidebarActive.TButton",
            background=[("active", "#4b6d8f")],
            foreground=[("disabled", "#e6edf3")],
        )

        style.configure(
            "PageTitle.TLabel",
            background="#f4f6f8",
            foreground="#1f2933",
            font=("Segoe UI", 17, "bold"),
        )
        style.configure(
            "PageBody.TLabel",
            background="#f4f6f8",
            foreground="#52616f",
            font=("Segoe UI", 10),
        )

    def _size_window_to_content(self) -> None:
        self.update_idletasks()
        page_widths = [page.winfo_reqwidth() for page in self._pages.values()]
        page_heights = [page.winfo_reqheight() for page in self._pages.values()]
        required_width = max(page_widths) + self.sidebar.winfo_reqwidth() + 28
        required_height = max(page_heights) + 24

        max_width = max(0, self.winfo_screenwidth() - 40)
        max_height = max(0, self.winfo_screenheight() - 80)

        required_width = min(max(1000, required_width), max_width)
        required_height = min(max(650, required_height), max_height)

        self.geometry(f"{required_width}x{required_height}")
        self.minsize(required_width, required_height)

        x_pos = max((self.winfo_screenwidth() - required_width) // 2, 0)
        y_pos = max((self.winfo_screenheight() - required_height) // 2, 0)
        self.geometry(f"{required_width}x{required_height}+{x_pos}+{y_pos}")

    def _build_sidebar(self) -> None:
        title = ttk.Label(
            self.sidebar,
            text="SSAD Toolkit",
            background="#243447",
            foreground="#ffffff",
            font=("Segoe UI", 16, "bold"),
            padding=(2, 4, 2, 18),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            self.sidebar,
            text="Practical work shell",
            background="#243447",
            foreground="#b7c6d6",
            font=("Segoe UI", 9),
            padding=(2, 0, 2, 18),
        )
        subtitle.pack(anchor="w")

        for page_name, _page_class in PAGE_DEFINITIONS:
            button = ttk.Button(
                self.sidebar,
                text=page_name,
                style="Sidebar.TButton",
                command=lambda name=page_name: self.show_page(name),
            )
            button.pack(fill="x", pady=(0, 8))
            self._buttons[page_name] = button

    def _build_pages(self) -> None:
        for page_name, page_class in PAGE_DEFINITIONS:
            page = page_class(self.content)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[page_name] = page

    def show_page(self, page_name: str) -> None:
        """Show one page and hide the others."""
        if page_name not in self._pages:
            raise KeyError(f"Unknown page: {page_name}")

        for name, page in self._pages.items():
            if name == page_name:
                page.tkraise()

        self._update_sidebar_state(page_name)
        self._active_page_name = page_name

    def _update_sidebar_state(self, active_page_name: str) -> None:
        for page_name, button in self._buttons.items():
            button.configure(
                style="SidebarActive.TButton" if page_name == active_page_name else "Sidebar.TButton"
            )


def run_app() -> None:
    """Start the SSAD Toolkit application."""
    app = SSADToolkitApp()
    app.mainloop()
"""Main window and page switching logic for SSAD Toolkit."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui.pages.attacks_page import AttacksPage
from gui.pages.decryption_page import DecryptionPage, DecryptionToplevel
from gui.pages.encryption_page import EncryptionPage
from gui.pages.integrity_page import IntegrityPage
from gui.pages.passwords_page import PasswordsPage
from gui.scrollable import ScrollableFrame


PAGE_DEFINITIONS = [
    ("Encryption", EncryptionPage),
    ("Decryption", DecryptionPage),
    ("Passwords", PasswordsPage),
    ("Attacks", AttacksPage),
    ("Authenticity / Integrity", IntegrityPage),
]


class SSADToolkitApp(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title("SSAD Toolkit")
        self.geometry("1000x640")
        self.resizable(True, True)

        self._setup_style()

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=(16, 14))
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(8, 0), pady=8)

        self.content = ttk.Frame(self, style="Content.TFrame", padding=(16, 12))
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)

        self._pages: dict[str, ttk.Frame] = {}
        self._page_scroll_areas: dict[str, ScrollableFrame] = {}
        self._buttons: dict[str, ttk.Button] = {}
        self._active_page_name: str | None = None
        self._decryption_popup: DecryptionToplevel | None = None

        self.shared = {"use_case": None, "cipher": None, "record": None}
        self._build_sidebar()
        self._build_header()
        self._lock_sidebar_width()
        self._build_pages()
        self._size_window_to_content()
        self._bind_scroll_events()
        self.show_page(PAGE_DEFINITIONS[0][0])

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        background = "#f3f5fa"
        surface = "#ffffff"
        surface_muted = "#f7f8fc"
        text = "#172033"
        muted = "#697586"
        accent = "#4f46e5"
        accent_hover = "#4338ca"
        border = "#e3e8f1"

        self.configure(background=background)
        style.configure(".", font=("Segoe UI", 9))
        style.configure("TFrame", background=surface)
        style.configure("App.TFrame", background=background)
        style.configure("Sidebar.TFrame", background="#111827")
        style.configure("Content.TFrame", background=background)
        style.configure(
            "Page.TFrame",
            background=surface,
            borderwidth=1,
            relief="solid",
        )
        style.configure("Topbar.TFrame", background=background)

        style.configure(
            "TLabel",
            background=surface,
            foreground=text,
            font=("Segoe UI", 9),
        )
        style.configure(
            "HeaderTitle.TLabel",
            background=background,
            foreground=text,
            font=("Segoe UI", 15, "bold"),
        )
        style.configure(
            "HeaderSubtitle.TLabel",
            background=background,
            foreground=muted,
            font=("Segoe UI", 8),
        )
        style.configure(
            "WorkspaceBadge.TLabel",
            background="#e9f8ef",
            foreground="#18794e",
            padding=(8, 5),
            font=("Segoe UI", 8, "bold"),
        )
        style.configure(
            "SidebarBrand.TLabel",
            background="#111827",
            foreground="#ffffff",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "SidebarSubtitle.TLabel",
            background="#111827",
            foreground="#9aa6bb",
            font=("Segoe UI", 8),
        )
        style.configure(
            "SidebarSection.TLabel",
            background="#111827",
            foreground="#7f8ba2",
            font=("Segoe UI", 8, "bold"),
        )
        style.configure(
            "SidebarFooter.TLabel",
            background="#111827",
            foreground="#7f8ba2",
            font=("Segoe UI", 8),
        )

        style.configure(
            "Sidebar.TButton",
            background="#111827",
            foreground="#c5cede",
            padding=(10, 8),
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 9),
            anchor="w",
        )
        style.map(
            "Sidebar.TButton",
            background=[("active", "#202a3a")],
            foreground=[("disabled", "#7f8ba2")],
        )

        style.configure(
            "SidebarActive.TButton",
            background="#3730a3",
            foreground="#ffffff",
            padding=(10, 8),
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        style.map(
            "SidebarActive.TButton",
            background=[("active", "#4338ca")],
            foreground=[("disabled", "#e6e8ff")],
        )

        style.configure(
            "TButton",
            background=accent,
            foreground="#ffffff",
            padding=(10, 6),
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 9),
        )
        style.map(
            "TButton",
            background=[
                ("disabled", "#c7c9dc"),
                ("pressed", "#3730a3"),
                ("active", accent_hover),
            ],
            foreground=[("disabled", "#f7f7fb")],
        )

        style.configure(
            "TEntry",
            fieldbackground=surface_muted,
            foreground=text,
            insertcolor=text,
            padding=(6, 4),
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            font=("Segoe UI", 9),
        )
        style.map(
            "TEntry",
            fieldbackground=[("disabled", "#eef1f6"), ("readonly", surface_muted)],
            bordercolor=[("focus", accent)],
            lightcolor=[("focus", accent)],
            darkcolor=[("focus", accent)],
        )
        style.configure(
            "TCombobox",
            fieldbackground=surface_muted,
            background=surface_muted,
            foreground=text,
            arrowcolor=muted,
            padding=(6, 4),
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            font=("Segoe UI", 9),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", surface_muted)],
            selectbackground=[("readonly", surface_muted)],
            selectforeground=[("readonly", text)],
            bordercolor=[("focus", accent)],
        )

        style.configure(
            "TLabelFrame",
            background=surface,
            foreground=text,
            bordercolor=border,
            borderwidth=1,
            relief="solid",
            padding=(9, 7),
        )
        style.configure(
            "TLabelFrame.Label",
            background=surface,
            foreground="#344054",
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "TCheckbutton",
            background=surface,
            foreground=text,
            font=("Segoe UI", 8),
        )
        style.map(
            "TCheckbutton",
            background=[("active", surface)],
            foreground=[("disabled", muted)],
        )
        style.configure("TSeparator", background=border)
        style.configure(
            "TNotebook",
            background=surface,
            borderwidth=0,
            tabmargins=(0, 0, 8, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=surface_muted,
            foreground="#526078",
            padding=(10, 6),
            borderwidth=0,
            font=("Segoe UI", 8, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", accent), ("active", "#ecebff")],
            foreground=[("selected", "#ffffff"), ("active", text)],
        )
        style.configure(
            "TScrollbar",
            background="#d9deea",
            troughcolor=surface,
            borderwidth=0,
            arrowsize=12,
        )

        style.configure(
            "PageTitle.TLabel",
            background=surface,
            foreground=text,
            font=("Segoe UI", 15, "bold"),
        )
        style.configure(
            "PageBody.TLabel",
            background=surface,
            foreground=muted,
            font=("Segoe UI", 9),
        )

        self.option_add("*Text.background", surface_muted)
        self.option_add("*Text.foreground", text)
        self.option_add("*Text.insertBackground", text)
        self.option_add("*Text.selectBackground", "#dcdafe")
        self.option_add("*Text.selectForeground", text)
        self.option_add("*Text.relief", "solid")
        self.option_add("*Text.borderWidth", 1)
        self.option_add("*Text.highlightThickness", 0)
        self.option_add("*Text.padX", 6)
        self.option_add("*Text.padY", 4)
        self.option_add("*Text.font", ("Segoe UI", 9))
        self.option_add("*Canvas.background", surface)

    def _size_window_to_content(self) -> None:
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = min(1000, max(760, screen_width - 40))
        height = min(650, max(520, screen_height - 80))

        self.minsize(min(760, width), min(520, height))
        x_pos = max((screen_width - width) // 2, 0)
        y_pos = max((screen_height - height) // 2, 0)
        self.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

    def _build_sidebar(self) -> None:
        title = ttk.Label(
            self.sidebar,
            text="SSAD Toolkit",
            style="SidebarBrand.TLabel",
            padding=(2, 2, 2, 5),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            self.sidebar,
            text="CRYPTOGRAPHY LAB",
            style="SidebarSubtitle.TLabel",
            padding=(2, 0, 2, 20),
        )
        subtitle.pack(anchor="w")

        ttk.Label(
            self.sidebar,
            text="WORKSPACE",
            style="SidebarSection.TLabel",
            padding=(2, 0, 2, 8),
        ).pack(anchor="w")

        for page_name, _page_class in PAGE_DEFINITIONS:
            button = ttk.Button(
                self.sidebar,
                text=page_name,
                style="Sidebar.TButton",
                command=lambda name=page_name: self.show_page(name),
            )
            button.pack(fill="x", pady=(0, 8))
            self._buttons[page_name] = button

        ttk.Label(
            self.sidebar,
            text="SECURE LEARNING ENVIRONMENT",
            style="SidebarFooter.TLabel",
            padding=(2, 0, 2, 2),
        ).pack(side="bottom", anchor="w")

    def _build_header(self) -> None:
        self.header = ttk.Frame(self.content, style="Topbar.TFrame")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.header.columnconfigure(0, weight=1)

        heading = ttk.Frame(self.header, style="Topbar.TFrame")
        heading.grid(row=0, column=0, sticky="w")
        ttk.Label(
            heading,
            text="Security workspace",
            style="HeaderTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            heading,
            text="Explore cryptography, password protection and data integrity.",
            style="HeaderSubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        ttk.Label(
            self.header,
            text="READY  |  LOCAL",
            style="WorkspaceBadge.TLabel",
        ).grid(row=0, column=1, sticky="e", padx=(16, 0))

    def _lock_sidebar_width(self) -> None:
        """Reserve the width of the widest (bold) label so the pages never shift."""
        widest = 0
        for button in self._buttons.values():
            button.configure(style="SidebarActive.TButton")
            self.update_idletasks()
            widest = max(widest, self.sidebar.winfo_reqwidth())
            button.configure(style="Sidebar.TButton")
        self.update_idletasks()
        self.columnconfigure(0, minsize=widest)
        self.sidebar.grid_configure(sticky="nsew")

    def _build_pages(self) -> None:
        for page_name, page_class in PAGE_DEFINITIONS:
            scroll_area = ScrollableFrame(self.content)
            scroll_area.grid(row=1, column=0, sticky="nsew")
            page = page_class(scroll_area.inner)
            page.grid(row=0, column=0, sticky="nsew")
            scroll_area.inner.rowconfigure(0, weight=1)
            self._pages[page_name] = page
            self._page_scroll_areas[page_name] = scroll_area

    def _bind_scroll_events(self) -> None:
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind_all("<Button-4>", lambda event: self._scroll_from_event(event, -1), add="+")
        self.bind_all("<Button-5>", lambda event: self._scroll_from_event(event, 1), add="+")

    def _on_mousewheel(self, event: tk.Event, horizontal: bool = False) -> str | None:
        steps = int(-event.delta / 120)
        if steps == 0 and event.delta:
            steps = -1 if event.delta > 0 else 1
        horizontal = horizontal or bool(event.state & 0x0001)
        return self._scroll_from_event(event, steps, horizontal)

    def _scroll_from_event(
        self,
        event: tk.Event,
        steps: int,
        horizontal: bool = False,
    ) -> str | None:
        widget = self.winfo_containing(event.x_root, event.y_root) or event.widget
        while widget is not None:
            canvas = getattr(widget, "_scroll_canvas", None)
            if canvas is not None and canvas.winfo_exists():
                view = canvas.xview() if horizontal else canvas.yview()
                if len(view) == 2 and view[1] - view[0] < 1:
                    if horizontal:
                        canvas.xview_scroll(steps, "units")
                    else:
                        canvas.yview_scroll(steps, "units")
                    return "break"
                return None
            widget = getattr(widget, "master", None)
        return None

    def show_page(self, page_name: str) -> None:
        """Show one page and hide the others."""
        if page_name not in self._pages:
            raise KeyError(f"Unknown page: {page_name}")

        for name, scroll_area in self._page_scroll_areas.items():
            if name == page_name:
                scroll_area.tkraise()

        self._update_sidebar_state(page_name)
        self._active_page_name = page_name

    def _update_sidebar_state(self, active_page_name: str) -> None:
        for page_name, button in self._buttons.items():
            button.configure(
                style="SidebarActive.TButton" if page_name == active_page_name else "Sidebar.TButton"
            )

    def send_ciphertext_to_decryption(
        self, ciphertext: str, padding: str = "", algorithm: str = ""
    ) -> None:
        """Transmit ciphertext from Entity A (Encryption) to Entity B (Decryption)."""
        self.shared["pending_ciphertext"] = ciphertext
        self.shared["pending_padding"] = padding

        dec_page = self._pages.get("Decryption")
        if dec_page is not None and hasattr(dec_page, "set_incoming_ciphertext"):
            dec_page.set_incoming_ciphertext(ciphertext, padding, algorithm)

        if (
            hasattr(self, "_decryption_popup")
            and self._decryption_popup is not None
            and self._decryption_popup.winfo_exists()
        ):
            self._decryption_popup.set_incoming_ciphertext(ciphertext, padding, algorithm)

    def open_separate_decryption_window(self) -> None:
        """Open or focus a standalone OS window for Entity B (Decryption)."""
        if (
            hasattr(self, "_decryption_popup")
            and self._decryption_popup is not None
            and self._decryption_popup.winfo_exists()
        ):
            self._decryption_popup.lift()
            self._decryption_popup.focus_force()
            return
        self._decryption_popup = DecryptionToplevel(self)


def run_app() -> None:
    """Start the SSAD Toolkit application."""
    app = SSADToolkitApp()
    app.mainloop()
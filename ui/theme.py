import sys
from tkinter import ttk

_PALETTES = {
    "dark": {
        "BG": "#11141C",
        "SURFACE": "#191E29",
        "SURFACE_LIGHT": "#242B39",
        "SURFACE_HOVER": "#30394A",
        "ENTRY_BG": "#141923",
        "BORDER": "#2B3444",
        "BORDER_FOCUS": "#9B8CFF",
        "ACCENT": "#7967F2",
        "ACCENT_LIGHT": "#B6A9FF",
        "ACCENT_HOVER": "#6857D8",
        "ACCENT_MUTED": "#302A4A",
        "ACCENT_GRADIENT": "#9B8CFF",
        "TEXT": "#F1F3F8",
        "SUBTEXT": "#A1AABD",
        "MUTED": "#727D90",
        "SUCCESS": "#42C99A",
        "SUCCESS_HOVER": "#2DAB7F",
        "WARNING": "#F2B861",
        "ERROR": "#F07883",
        "DANGER_HOVER": "#D45C69",
        "TAB_BG": "#151923",
        "TAB_ACTIVE": "#302A4A",
        "TAB_HOVER": "#222837",
    },
    "light": {
        "BG": "#F4F6FA",
        "SURFACE": "#FFFFFF",
        "SURFACE_LIGHT": "#F1F4F9",
        "SURFACE_HOVER": "#E8EDF5",
        "ENTRY_BG": "#F8FAFC",
        "BORDER": "#E2E7EF",
        "BORDER_FOCUS": "#7774E8",
        "ACCENT": "#5B59D6",
        "ACCENT_LIGHT": "#514FC7",
        "ACCENT_HOVER": "#4846B8",
        "ACCENT_MUTED": "#EFEEFF",
        "ACCENT_GRADIENT": "#7774E8",
        "TEXT": "#202938",
        "SUBTEXT": "#667085",
        "MUTED": "#98A2B3",
        "SUCCESS": "#16835D",
        "SUCCESS_HOVER": "#116B4B",
        "WARNING": "#A96C12",
        "ERROR": "#D04452",
        "DANGER_HOVER": "#B83240",
        "TAB_BG": "#FFFFFF",
        "TAB_ACTIVE": "#EFEEFF",
        "TAB_HOVER": "#F5F5FF",
    },
}

_PALETTE_NAMES = tuple(_PALETTES["dark"])
for _name, _value in _PALETTES["dark"].items():
    globals()[_name] = _value

FONT_HERO = ("Segoe UI", 22, "bold")
FONT_TITLE = ("Segoe UI", 15, "bold")
FONT_SUBTITLE = ("Segoe UI", 12, "bold")
FONT_REGULAR = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_SMALL_BOLD = ("Segoe UI", 9, "bold")
FONT_STAT = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 9)


def apply_theme(root, mode="dark"):
    """Apply a palette to custom Tk widgets and native ttk controls."""
    if mode not in _PALETTES:
        mode = "dark"
    palette = _PALETTES[mode]
    globals().update(palette)
    for module_name, module in tuple(sys.modules.items()):
        if module_name == "ui" or module_name.startswith("ui."):
            namespace = getattr(module, "__dict__", {})
            for name, value in palette.items():
                if name in namespace:
                    namespace[name] = value
    root.configure(bg=palette["BG"])

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT, font=FONT_REGULAR)

    style.configure(
        "Custom.Horizontal.TProgressbar",
        troughcolor=SURFACE_LIGHT,
        background=ACCENT,
        thickness=8,
        borderwidth=0,
    )
    style.configure(
        "Vertical.TScrollbar",
        background=SURFACE_LIGHT,
        troughcolor=BG,
        arrowcolor=SUBTEXT,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", SURFACE_HOVER), ("pressed", ACCENT)],
    )

    style.configure(
        "TCombobox",
        fieldbackground=ENTRY_BG,
        background=SURFACE_LIGHT,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        arrowcolor=ACCENT,
        padding=(9, 7),
        relief="flat",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", ENTRY_BG), ("disabled", SURFACE_LIGHT)],
        foreground=[("readonly", TEXT), ("disabled", MUTED)],
        selectbackground=[("readonly", ENTRY_BG)],
        selectforeground=[("readonly", TEXT)],
    )
    root.option_add("*TCombobox*Listbox.background", SURFACE)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT_MUTED)
    root.option_add("*TCombobox*Listbox.selectForeground", ACCENT_LIGHT)
    root.option_add("*TCombobox*Listbox.font", FONT_REGULAR)

    style.configure(
        "Treeview",
        background=SURFACE,
        foreground=TEXT,
        fieldbackground=SURFACE,
        bordercolor=BORDER,
        borderwidth=0,
        font=FONT_REGULAR,
        rowheight=38,
    )
    style.configure(
        "Treeview.Heading",
        background=SURFACE_LIGHT,
        foreground=SUBTEXT,
        borderwidth=0,
        font=FONT_SMALL_BOLD,
        padding=(10, 9),
    )
    style.map(
        "Treeview",
        background=[("selected", ACCENT_MUTED)],
        foreground=[("selected", ACCENT_LIGHT)],
    )

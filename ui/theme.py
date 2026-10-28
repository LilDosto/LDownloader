import sys
import ctypes
from tkinter import ttk

_PALETTES = {
    "dark": {
        "BG": "#0D1017",
        "SURFACE": "#151923",
        "SURFACE_LIGHT": "#1E2433",
        "SURFACE_HOVER": "#283044",
        "ENTRY_BG": "#10141D",
        "BORDER": "#252D3D",
        "BORDER_FOCUS": "#8B7CFF",
        "ACCENT": "#6C5CE7",
        "ACCENT_LIGHT": "#B2A4FF",
        "ACCENT_HOVER": "#5A4AD1",
        "ACCENT_MUTED": "#23203F",
        "ACCENT_GRADIENT": "#8B7CFF",
        "TEXT": "#F3F5FA",
        "SUBTEXT": "#9BA5B8",
        "MUTED": "#667185",
        "SUCCESS": "#2ED573",
        "SUCCESS_HOVER": "#25B360",
        "WARNING": "#FFA502",
        "ERROR": "#FF5252",
        "DANGER_HOVER": "#E04040",
        "TAB_BG": "#11151E",
        "TAB_ACTIVE": "#23203F",
        "TAB_HOVER": "#1B2130",
    },
    "light": {
        "BG": "#F1F4F9",
        "SURFACE": "#FFFFFF",
        "SURFACE_LIGHT": "#E9EEF6",
        "SURFACE_HOVER": "#DCE4F0",
        "ENTRY_BG": "#F7F9FC",
        "BORDER": "#D8E0EC",
        "BORDER_FOCUS": "#635BFF",
        "ACCENT": "#5850EC",
        "ACCENT_LIGHT": "#4338CA",
        "ACCENT_HOVER": "#463FD4",
        "ACCENT_MUTED": "#ECEBFF",
        "ACCENT_GRADIENT": "#635BFF",
        "TEXT": "#111827",
        "SUBTEXT": "#4B5563",
        "MUTED": "#8E99AB",
        "SUCCESS": "#10B981",
        "SUCCESS_HOVER": "#059669",
        "WARNING": "#D97706",
        "ERROR": "#EF4444",
        "DANGER_HOVER": "#DC2626",
        "TAB_BG": "#FFFFFF",
        "TAB_ACTIVE": "#ECEBFF",
        "TAB_HOVER": "#F3F4FF",
    },
}

_PALETTE_NAMES = tuple(_PALETTES["dark"])
for _name, _value in _PALETTES["dark"].items():
    globals()[_name] = _value

FONT_HERO = ("Segoe UI", 20, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUBTITLE = ("Segoe UI", 11, "bold")
FONT_REGULAR = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_SMALL_BOLD = ("Segoe UI", 9, "bold")
FONT_STAT = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 9)


def apply_windows_titlebar(root, is_dark=True):
    """Windows 10/11 pencere başlık çubuğunu karanlık/aydınlık temaya uyarlar."""
    if sys.platform != "win32":
        return
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1 if is_dark else 0)
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 11 & Win10 20H1+), 19 (Win10 1809-1909)
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
        )
        if hr != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 19, ctypes.byref(value), ctypes.sizeof(value)
            )
    except Exception:
        pass


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
    apply_windows_titlebar(root, is_dark=(mode == "dark"))

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT, font=FONT_REGULAR)

    style.configure(
        "Custom.Horizontal.TProgressbar",
        troughcolor=SURFACE_LIGHT,
        background=ACCENT,
        lightcolor=ACCENT_GRADIENT,
        darkcolor=ACCENT,
        bordercolor=SURFACE_LIGHT,
        thickness=10,
        borderwidth=0,
    )
    style.configure(
        "Vertical.TScrollbar",
        background=SURFACE_LIGHT,
        troughcolor=BG,
        arrowcolor=SUBTEXT,
        borderwidth=0,
        relief="flat",
        width=10,
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
        arrowcolor=ACCENT_LIGHT,
        padding=(10, 7),
        relief="flat",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", ENTRY_BG), ("disabled", SURFACE_LIGHT)],
        foreground=[("readonly", TEXT), ("disabled", MUTED)],
        selectbackground=[("readonly", ENTRY_BG)],
        selectforeground=[("readonly", TEXT)],
        bordercolor=[("focus", BORDER_FOCUS)],
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
        rowheight=40,
    )
    style.configure(
        "Treeview.Heading",
        background=SURFACE_LIGHT,
        foreground=SUBTEXT,
        borderwidth=0,
        font=FONT_SMALL_BOLD,
        padding=(12, 10),
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", SURFACE_HOVER)],
        foreground=[("active", TEXT)],
    )
    style.map(
        "Treeview",
        background=[("selected", ACCENT_MUTED)],
        foreground=[("selected", ACCENT_LIGHT)],
    )

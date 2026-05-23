import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import sys
import re
import ctypes
from datetime import datetime

# ── Windows görev çubuğu ikonu için AppUserModelID ──────────────
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ytdlp.gui.downloader.1")
    except Exception:
        pass

# ── Renkler & Stil ──────────────────────────────────────────────
BG       = "#06060c"  # Deep space dark background
SURFACE  = "#111122"  # Layered card/panel background
SURFACE2 = "#1d1d36"  # Interactive items
ENTRY_BG = "#0b0b14"  # Recessed entry fields
ACCENT   = "#8b5cf6"  # Premium soft violet
ACCENT2  = "#a78bfa"  # Lighter purple for hover
TEXT     = "#f8fafc"  # Clean white/slate text
SUBTEXT  = "#64748b"  # Muted slate gray for labels
SUCCESS  = "#4ade80"  # Vibrant soft green
ERROR    = "#f87171"  # Vibrant soft red
WARN     = "#fbbf24"  # Vibrant soft amber
FONT     = ("Segoe UI", 10)
FONT_B   = ("Segoe UI", 10, "bold")
FONT_H   = ("Segoe UI", 16, "bold")
FONT_S   = ("Segoe UI", 9)
FONT_STAT = ("Segoe UI", 11, "bold")

def _get_app_dir():
    """PyInstaller ile paketlendiğinde kaynak dosyaları bulmak için."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

_APP_DIR = _get_app_dir()

def _get_exe_dir():
    """EXE'nin bulunduğu dizin (cookies.txt gibi kullanıcı dosyaları için)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

_EXE_DIR = _get_exe_dir()
_TEMP_LOG = os.path.join(_EXE_DIR, "temp.txt")

def _temp_log(msg):
    """temp.txt dosyasına zaman damgalı detaylı log yazar. Maksimum 2MB limitlidir."""
    try:
        if os.path.exists(_TEMP_LOG) and os.path.getsize(_TEMP_LOG) > 2 * 1024 * 1024:
            with open(_TEMP_LOG, "w", encoding="utf-8") as f:
                f.write("[LOG SIFIRLANDI - 2MB BOYUT LİMİTİ AŞILDI]\n")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(_TEMP_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


class YTDLPGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LDownloader")
        self.geometry("760x750")
        self.minsize(680, 650)
        self.configure(bg=BG)

        _temp_log("="*60)
        _temp_log("UYGULAMA BAŞLATILDI")
        _temp_log(f"Python: {sys.version}")
        _temp_log(f"Platform: {sys.platform}")
        _temp_log(f"Frozen: {getattr(sys, 'frozen', False)}")
        _temp_log(f"APP_DIR: {_APP_DIR}")
        _temp_log(f"EXE_DIR: {_EXE_DIR}")
        _temp_log(f"Log dosyası: {_TEMP_LOG}")
        _temp_log("="*60)

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 760) // 2
        y = (self.winfo_screenheight() - 750) // 2
        self.geometry(f"760x750+{x}+{y}")

        self._download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self._proc    = None
        self._running = False
        self._cancelled = False
        self._cookies_path = None        # Manuel cookies dosyası
        self._cookies_browser = "firefox"  # Varsayılan: Firefox

        # ── İkon ayarla (görev çubuğu + pencere başlığı) ────────
        ico_path = os.path.join(_APP_DIR, "logo.ico")
        if os.path.isfile(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # ── Başlık logosu (PNG, arayüzde gösterilecek) ──────────
        self._logo_img = None
        logo_path = os.path.join(_APP_DIR, "logo.png")
        if os.path.isfile(logo_path):
            try:
                raw = tk.PhotoImage(file=logo_path)
                # 128px ise 3x küçült, 64px ise 2x
                factor = max(1, raw.width() // 40)
                self._logo_img = raw.subsample(factor, factor)
            except Exception:
                pass

        self._setup_styles()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Bağımlılık Kontrolü ─────────────────────────────────
        self._check_dependencies()

        # ── Cookies dosyası otomatik yükleme ────────────────────
        default_cookies = os.path.join(_EXE_DIR, "cookies.txt")
        if os.path.isfile(default_cookies):
            self._cookies_path = default_cookies
            self._cookies_file_var.set("✅ cookies.txt (Otomatik)")
            self._cookies_file_lbl.config(fg=SUCCESS)
            self._set_ck_mode("file")

    # ── Stiller ─────────────────────────────────────────────────
    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("TFrame",      background=BG)
        s.configure("TLabel",      background=BG,      foreground=TEXT,    font=FONT)
        s.configure("Sub.TLabel",  background=SURFACE,  foreground=SUBTEXT, font=FONT_S)
        s.configure("Card.TLabel", background=SURFACE,  foreground=TEXT,    font=FONT)

        s.configure("Custom.Horizontal.TProgressbar",
                    troughcolor=SURFACE2, background=ACCENT, thickness=16, borderwidth=0)

        s.configure("Vertical.TScrollbar",
                    background=SURFACE2, troughcolor=SURFACE, arrowcolor=SUBTEXT, borderwidth=0)

        s.configure("TCombobox",
                    fieldbackground=ENTRY_BG,
                    background=SURFACE2,
                    foreground=TEXT,
                    bordercolor="#22223a",
                    lightcolor="#22223a",
                    darkcolor="#22223a",
                    arrowcolor=TEXT)
        self.option_add("*TCombobox*Listbox.background", ENTRY_BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", TEXT)
        self.option_add("*TCombobox*Listbox.font", FONT)

    # ── Ana arayüz ──────────────────────────────────────────────
    def _build_ui(self):
        # Başlık satırı (logo + başlık)
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(14, 0))

        if self._logo_img:
            tk.Label(hdr, image=self._logo_img, bg=BG).pack(side="left", padx=(0, 10))

        title_frame = tk.Frame(hdr, bg=BG)
        title_frame.pack(side="left")
        tk.Label(title_frame, text="LDownloader",
                 bg=BG, fg=TEXT, font=FONT_H).pack(anchor="w")
        tk.Label(title_frame, text="Video & Ses İndirici — Playlist Destekli",
                 bg=BG, fg=SUBTEXT, font=FONT_S).pack(anchor="w")

        tk.Label(hdr, text="v2.0", bg=BG, fg=SUBTEXT, font=FONT_S
                 ).pack(side="right", anchor="s", pady=8)

        # Ayraç
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x", padx=28, pady=(10, 0))

        # ── Cookies paneli ────────────────────────────────────────
        cookies_card = self._card(self)
        cookies_card.pack(fill="x", padx=28, pady=(10, 0))

        ck_top = tk.Frame(cookies_card, bg=SURFACE)
        ck_top.pack(fill="x")
        tk.Label(ck_top, text="🍪 Cookies Kaynağı", bg=SURFACE, fg=SUBTEXT,
                 font=FONT_S).pack(side="left")

        # Segmented Control for Cookies Mode
        self._ck_mode_var = tk.StringVar(value="browser")
        ck_mode_row = tk.Frame(cookies_card, bg=SURFACE)
        ck_mode_row.pack(fill="x", pady=(8, 0))

        self._seg_ck = tk.Frame(ck_mode_row, bg=SURFACE2, padx=2, pady=2)
        self._seg_ck.pack(side="left")

        self._ck_btn_browser = tk.Button(
            self._seg_ck, text="🌐 Tarayıcıdan Çek", command=lambda: self._set_ck_mode("browser"),
            bg=ACCENT, fg="#ffffff", activebackground=ACCENT, activeforeground="#ffffff",
            font=FONT_B, relief="flat", bd=0, cursor="hand2", padx=14, pady=6)
        self._ck_btn_browser.pack(side="left")

        self._ck_btn_file = tk.Button(
            self._seg_ck, text="📄 Dosyadan Yükle", command=lambda: self._set_ck_mode("file"),
            bg=SURFACE2, fg=SUBTEXT, activebackground="#2d2d4a", activeforeground=TEXT,
            font=FONT_B, relief="flat", bd=0, cursor="hand2", padx=14, pady=6)
        self._ck_btn_file.pack(side="left", padx=(2, 0))

        # Tarayıcı seçimi satırı
        self._browser_frame = tk.Frame(cookies_card, bg=SURFACE)
        self._browser_frame.pack(fill="x", pady=(10, 0))
        tk.Label(self._browser_frame, text="Tarayıcı:", bg=SURFACE, fg=TEXT,
                 font=FONT).pack(side="left")
        self._browser_var = tk.StringVar(value="firefox")
        browser_cb = ttk.Combobox(self._browser_frame, textvariable=self._browser_var,
                                   values=["firefox", "chrome", "edge", "brave", "opera"],
                                   state="readonly", width=12, font=FONT)
        browser_cb.pack(side="left", padx=(6, 10))
        browser_cb.bind("<<ComboboxSelected>>", self._on_browser_change)
        self._ck_status_var = tk.StringVar(value="✅ Firefox seçili — her indirmede taze cookies çekilecek")
        self._ck_status_lbl = tk.Label(self._browser_frame, textvariable=self._ck_status_var,
                                        bg=SURFACE, fg=SUCCESS, font=FONT_S)
        self._ck_status_lbl.pack(side="left")

        # Dosya seçimi satırı (başlangıçta gizli)
        self._file_frame = tk.Frame(cookies_card, bg=SURFACE)
        self._cookies_file_var = tk.StringVar(value="Seçilmedi")
        self._cookies_file_lbl = tk.Label(self._file_frame, textvariable=self._cookies_file_var,
                                           bg=ENTRY_BG, fg=SUBTEXT, font=FONT,
                                           anchor="w", padx=12, pady=6,
                                           relief="flat", highlightthickness=1,
                                           highlightbackground="#22223a")
        self._cookies_file_lbl.pack(side="left", fill="x", expand=True)
        self._btn(self._file_frame, "📂 Seç", self._choose_cookies_file, small=True
                  ).pack(side="right", padx=(6, 0))
        self._btn(self._file_frame, "✕ Kaldır", self._clear_cookies_file, small=True
                  ).pack(side="right", padx=(6, 0))

        # Sekmeler Tab Bar (Segmented Look)
        self._tab_bar = tk.Frame(self, bg=BG)
        self._tab_bar.pack(fill="x", padx=28, pady=(14, 0))

        self._active_tab = "single"

        self._tab_seg_frame = tk.Frame(self._tab_bar, bg=SURFACE2, padx=2, pady=2)
        self._tab_seg_frame.pack(fill="x")

        self._btn_tab_single = tk.Button(
            self._tab_seg_frame, text="🎬  Tekil İndirme", command=lambda: self._switch_tab("single"),
            bg=ACCENT, fg="#ffffff", activebackground=ACCENT, activeforeground="#ffffff",
            font=FONT_B, relief="flat", bd=0, cursor="hand2", padx=20, pady=10)
        self._btn_tab_single.pack(side="left", fill="x", expand=True)

        self._btn_tab_playlist = tk.Button(
            self._tab_seg_frame, text="📋  Playlist İndirme", command=lambda: self._switch_tab("playlist"),
            bg=SURFACE2, fg=SUBTEXT, activebackground="#2d2d4a", activeforeground=TEXT,
            font=FONT_B, relief="flat", bd=0, cursor="hand2", padx=20, pady=10)
        self._btn_tab_playlist.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Sekme Containerları
        self._tab_container = tk.Frame(self, bg=BG)
        self._tab_container.pack(fill="both", expand=True, padx=28, pady=(4, 8))

        self._frame_single = tk.Frame(self._tab_container, bg=BG)
        self._frame_single.pack(fill="both", expand=True)

        self._frame_playlist = tk.Frame(self._tab_container, bg=BG)

        self._build_single_tab(self._frame_single)
        self._build_playlist_tab(self._frame_playlist)

        # ── İndirme istatistikleri paneli ────────────────────────
        stats_card = tk.Frame(self, bg=SURFACE, padx=20, pady=14)
        stats_card.pack(fill="x", padx=28, pady=(0, 4))

        # Progress bar label row (Durum + Yüzde)
        pbar_lbl_row = tk.Frame(stats_card, bg=SURFACE)
        pbar_lbl_row.pack(fill="x", pady=(0, 6))
        tk.Label(pbar_lbl_row, text="İndirme Durumu", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(side="left")
        self._pct_var = tk.StringVar(value="0%")
        tk.Label(pbar_lbl_row, textvariable=self._pct_var, bg=SURFACE, fg=ACCENT2, font=FONT_STAT).pack(side="right")

        self._progress = ttk.Progressbar(stats_card, style="Custom.Horizontal.TProgressbar",
                                          mode="determinate", maximum=100, value=0)
        self._progress.pack(fill="x", pady=(0, 10))

        # İstatistik satırı: Hız | İndirilen | Kalan
        stat_row = tk.Frame(stats_card, bg=SURFACE)
        stat_row.pack(fill="x")

        for i in range(3):
            stat_row.columnconfigure(i, weight=1)

        # Hız
        sf1 = tk.Frame(stat_row, bg=SURFACE)
        sf1.grid(row=0, column=0, sticky="w")
        tk.Label(sf1, text="⚡ Hız", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        self._speed_var = tk.StringVar(value="—")
        tk.Label(sf1, textvariable=self._speed_var, bg=SURFACE, fg=TEXT, font=FONT_STAT).pack(anchor="w")

        # İndirilen
        sf2 = tk.Frame(stat_row, bg=SURFACE)
        sf2.grid(row=0, column=1, sticky="w", padx=20)
        tk.Label(sf2, text="📥 İndirilen", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        self._downloaded_var = tk.StringVar(value="—")
        tk.Label(sf2, textvariable=self._downloaded_var, bg=SURFACE, fg=TEXT, font=FONT_STAT).pack(anchor="w")

        # Toplam / ETA
        sf3 = tk.Frame(stat_row, bg=SURFACE)
        sf3.grid(row=0, column=2, sticky="w")
        tk.Label(sf3, text="⏱ Kalan Süre", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        self._eta_var = tk.StringVar(value="—")
        tk.Label(sf3, textvariable=self._eta_var, bg=SURFACE, fg=TEXT, font=FONT_STAT).pack(anchor="w")

        # Log alanı
        log_wrap = tk.Frame(self, bg=SURFACE, padx=14, pady=10)
        log_wrap.pack(fill="both", expand=True, padx=28, pady=(0, 6))
        self._build_log(log_wrap)

        # Durum satırı
        self._status_var = tk.StringVar(value="Hazır")
        tk.Label(self, textvariable=self._status_var,
                 bg=BG, fg=SUBTEXT, font=FONT_S, anchor="w").pack(fill="x", padx=28, pady=(0, 10))

    # ── Tekil İndirme sekmesi ────────────────────────────────────
    def _build_single_tab(self, parent):
        c1 = self._card(parent)
        c1.pack(fill="x", pady=(4, 6))
        tk.Label(c1, text="Video / Ses URL'si", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        row = tk.Frame(c1, bg=SURFACE)
        row.pack(fill="x", pady=(6, 0))
        self._url_var   = tk.StringVar()
        self._url_entry = self._entry(row, self._url_var, ph="https://youtube.com/watch?v=...")
        self._url_entry.pack(side="left", fill="x", expand=True)
        self._btn(row, "✕", self._clear_url, small=True).pack(side="right", padx=(6, 0))

        c2 = self._card(parent)
        c2.pack(fill="x", pady=6)
        tk.Label(c2, text="Format", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        self._format_var = tk.StringVar(value="video")
        frow = tk.Frame(c2, bg=SURFACE)
        frow.pack(fill="x", pady=(8, 0))

        # Segmented Control for Single Format
        self._seg_fmt = tk.Frame(frow, bg=SURFACE2, padx=2, pady=2)
        self._seg_fmt.pack(side="left")

        self._fmt_btn_video = tk.Button(
            self._seg_fmt, text="🎬 Video (MP4)", command=lambda: self._set_fmt("video"),
            bg=ACCENT, fg="#ffffff", activebackground=ACCENT, activeforeground="#ffffff",
            font=FONT_B, relief="flat", bd=0, cursor="hand2", padx=14, pady=6)
        self._fmt_btn_video.pack(side="left")

        self._fmt_btn_audio = tk.Button(
            self._seg_fmt, text="🎵 Ses (MP3)", command=lambda: self._set_fmt("audio"),
            bg=SURFACE2, fg=SUBTEXT, activebackground="#2d2d4a", activeforeground=TEXT,
            font=FONT_B, relief="flat", bd=0, cursor="hand2", padx=14, pady=6)
        self._fmt_btn_audio.pack(side="left", padx=(2, 0))

        # Video çözünürlük alt paneli
        self._video_opts_frame = tk.Frame(c2, bg=SURFACE)
        self._video_opts_frame.pack(fill="x", pady=(10, 0))
        tk.Label(self._video_opts_frame, text="Çözünürlük Seçin:", bg=SURFACE, fg=TEXT, font=FONT).pack(side="left")
        self._res_var = tk.StringVar(value="Best Quality (En İyi)")
        res_cb = ttk.Combobox(self._video_opts_frame, textvariable=self._res_var,
                     values=["Best Quality (En İyi)", "4320p", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"],
                     state="readonly", width=22, font=FONT)
        res_cb.pack(side="left", padx=(10, 0))

        # Audio kalite alt paneli
        self._audio_opts_frame = tk.Frame(c2, bg=SURFACE)
        tk.Label(self._audio_opts_frame, text="Ses Kalitesi Seçin:", bg=SURFACE, fg=TEXT, font=FONT).pack(side="left")
        self._audio_qual_var = tk.StringVar(value="Best Quality (En İyi)")
        audio_cb = ttk.Combobox(self._audio_opts_frame, textvariable=self._audio_qual_var,
                     values=["Best Quality (En İyi)", "320 kbps", "256 kbps", "192 kbps", "128 kbps"],
                     state="readonly", width=22, font=FONT)
        audio_cb.pack(side="left", padx=(10, 0))
        self._audio_opts_frame.pack_forget()  # Start hidden

        c3 = self._card(parent)
        c3.pack(fill="x", pady=6)
        tk.Label(c3, text="Kayıt Klasörü", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        drow = tk.Frame(c3, bg=SURFACE)
        drow.pack(fill="x", pady=(6, 0))
        self._dir_var = tk.StringVar(value=self._download_dir)
        self._entry(drow, self._dir_var).pack(side="left", fill="x", expand=True)
        self._btn(drow, "📁 Seç", self._choose_dir_single, small=True).pack(side="right", padx=(6, 0))

        self._btn(parent, "⬇  İndir", self._start_single, accent=True
                  ).pack(pady=(12, 4), ipadx=24, ipady=8)

    # ── Playlist sekmesi ─────────────────────────────────────────
    def _build_playlist_tab(self, parent):
        c1 = self._card(parent)
        c1.pack(fill="x", pady=(4, 6))
        tk.Label(c1, text="Playlist URL'si", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        row = tk.Frame(c1, bg=SURFACE)
        row.pack(fill="x", pady=(6, 0))
        self._pl_url_var   = tk.StringVar()
        self._pl_url_entry = self._entry(row, self._pl_url_var,
                                          ph="https://youtube.com/playlist?list=...")
        self._pl_url_entry.pack(side="left", fill="x", expand=True)
        self._btn(row, "✕", self._clear_pl_url, small=True).pack(side="right", padx=(6, 0))

        c2 = self._card(parent)
        c2.pack(fill="x", pady=6)
        tk.Label(c2, text="Format", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        self._pl_format_var = tk.StringVar(value="video")
        frow = tk.Frame(c2, bg=SURFACE)
        frow.pack(fill="x", pady=(8, 0))

        # Segmented Control for Playlist Format
        self._seg_pl_fmt = tk.Frame(frow, bg=SURFACE2, padx=2, pady=2)
        self._pl_fmt_btn_video = tk.Button(
            self._seg_pl_fmt, text="🎬 Video (MP4)", command=lambda: self._set_pl_fmt("video"),
            bg=ACCENT, fg="#ffffff", activebackground=ACCENT, activeforeground="#ffffff",
            font=FONT_B, relief="flat", bd=0, cursor="hand2", padx=14, pady=6)
        self._pl_fmt_btn_video.pack(side="left")

        self._pl_fmt_btn_audio = tk.Button(
            self._seg_pl_fmt, text="🎵 Ses (MP3)", command=lambda: self._set_pl_fmt("audio"),
            bg=SURFACE2, fg=SUBTEXT, activebackground="#2d2d4a", activeforeground=TEXT,
            font=FONT_B, relief="flat", bd=0, cursor="hand2", padx=14, pady=6)
        self._pl_fmt_btn_audio.pack(side="left", padx=(2, 0))
        self._seg_pl_fmt.pack(side="left")

        # Video çözünürlük alt paneli
        self._pl_video_opts_frame = tk.Frame(c2, bg=SURFACE)
        self._pl_video_opts_frame.pack(fill="x", pady=(10, 0))
        tk.Label(self._pl_video_opts_frame, text="Çözünürlük Seçin:", bg=SURFACE, fg=TEXT, font=FONT).pack(side="left")
        self._pl_res_var = tk.StringVar(value="Best Quality (En İyi)")
        pl_res_cb = ttk.Combobox(self._pl_video_opts_frame, textvariable=self._pl_res_var,
                     values=["Best Quality (En İyi)", "4320p", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"],
                     state="readonly", width=22, font=FONT)
        pl_res_cb.pack(side="left", padx=(10, 0))

        # Audio kalite alt paneli
        self._pl_audio_opts_frame = tk.Frame(c2, bg=SURFACE)
        tk.Label(self._pl_audio_opts_frame, text="Ses Kalitesi Seçin:", bg=SURFACE, fg=TEXT, font=FONT).pack(side="left")
        self._pl_audio_qual_var = tk.StringVar(value="Best Quality (En İyi)")
        pl_audio_cb = ttk.Combobox(self._pl_audio_opts_frame, textvariable=self._pl_audio_qual_var,
                     values=["Best Quality (En İyi)", "320 kbps", "256 kbps", "192 kbps", "128 kbps"],
                     state="readonly", width=22, font=FONT)
        pl_audio_cb.pack(side="left", padx=(10, 0))
        self._pl_audio_opts_frame.pack_forget()  # Start hidden

        c3 = self._card(parent)
        c3.pack(fill="x", pady=6)
        tk.Label(c3, text="İndirme Aralığı  (boş = tamamını indir)",
                 bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        rrow = tk.Frame(c3, bg=SURFACE)
        rrow.pack(fill="x", pady=(8, 0))
        tk.Label(rrow, text="Başlangıç:", bg=SURFACE, fg=TEXT, font=FONT).pack(side="left")
        self._pl_start_var = tk.StringVar()
        self._entry(rrow, self._pl_start_var, width=6).pack(side="left", padx=(6, 18))
        tk.Label(rrow, text="Bitiş:", bg=SURFACE, fg=TEXT, font=FONT).pack(side="left")
        self._pl_end_var = tk.StringVar()
        self._entry(rrow, self._pl_end_var, width=6).pack(side="left", padx=(6, 0))

        c4 = self._card(parent)
        c4.pack(fill="x", pady=6)
        tk.Label(c4, text="Kayıt Klasörü", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(anchor="w")
        drow = tk.Frame(c4, bg=SURFACE)
        drow.pack(fill="x", pady=(6, 0))
        self._pl_dir_var = tk.StringVar(value=self._download_dir)
        self._entry(drow, self._pl_dir_var).pack(side="left", fill="x", expand=True)
        self._btn(drow, "📁 Seç",
                  lambda: self._choose_dir_for(self._pl_dir_var),
                  small=True).pack(side="right", padx=(6, 0))

        self._btn(parent, "⬇  Playlist'i İndir", self._start_playlist, accent=True
                  ).pack(pady=(12, 4), ipadx=24, ipady=8)

    # ── Log alanı ────────────────────────────────────────────────
    def _build_log(self, parent):
        top = tk.Frame(parent, bg=SURFACE)
        top.pack(fill="x")
        tk.Label(top, text="Çıktı", bg=SURFACE, fg=SUBTEXT, font=FONT_S).pack(side="left")
        self._btn(top, "🗑 Temizle", self._clear_log, small=True).pack(side="right")
        # İptal butonu (başlangıçta gizli, indirme sırasında gösterilir)
        self._cancel_btn = tk.Button(
            top, text="⛔ İptal Et", command=self._cancel_download,
            bg=ERROR, fg="#ffffff", activebackground="#dc2626", activeforeground="#ffffff",
            font=FONT_S, relief="flat", bd=0, cursor="hand2", padx=10, pady=2)
        # pack yapılmaz — _run() içinde gösterilir, bitince gizlenir

        wrap = tk.Frame(parent, bg=SURFACE)
        wrap.pack(fill="both", expand=True, pady=(6, 0))

        sb = ttk.Scrollbar(wrap, style="Vertical.TScrollbar")
        sb.pack(side="right", fill="y")

        self._log = tk.Text(wrap, bg=SURFACE2, fg=TEXT, font=("Consolas", 9),
                            insertbackground=TEXT, selectbackground=ACCENT,
                            relief="flat", bd=0, wrap="word",
                            yscrollcommand=sb.set, state="disabled", height=7)
        self._log.pack(fill="both", expand=True)
        sb.config(command=self._log.yview)

        self._log.tag_config("info",    foreground=TEXT)
        self._log.tag_config("success", foreground=SUCCESS)
        self._log.tag_config("error",   foreground=ERROR)
        self._log.tag_config("warn",    foreground=WARN)
        self._log.tag_config("accent",  foreground=ACCENT2)

    # ── Yardımcı widget üreticileri ──────────────────────────────
    def _card(self, parent):
        return tk.Frame(parent, bg=SURFACE, padx=20, pady=14)

    def _entry(self, parent, var, ph=None, width=None):
        kw = dict(textvariable=var, bg=ENTRY_BG, fg=TEXT,
                  insertbackground=TEXT, selectbackground=ACCENT,
                  relief="flat", bd=6, font=FONT,
                  highlightthickness=1, highlightbackground="#22223a",
                  highlightcolor=ACCENT)
        if width:
            kw["width"] = width
        e = tk.Entry(parent, **kw)
        if ph:
            e.insert(0, ph)
            e.config(fg=SUBTEXT)
            def _fi(ev, ent=e, p=ph):
                if ent.get() == p:
                    ent.delete(0, "end")
                    ent.config(fg=TEXT)
            def _fo(ev, ent=e, p=ph):
                if not ent.get():
                    ent.insert(0, p)
                    ent.config(fg=SUBTEXT)
            e.bind("<FocusIn>",  _fi)
            e.bind("<FocusOut>", _fo)
        return e

    def _btn(self, parent, text, cmd, accent=False, small=False):
        bg  = ACCENT   if accent else SURFACE2
        abg = ACCENT2  if accent else "#252540"
        fg  = "#ffffff" if accent else TEXT
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, activebackground=abg, activeforeground=fg,
                      font=(FONT if not small else FONT_S),
                      relief="flat", bd=0, cursor="hand2", padx=10, pady=4)
        b.bind("<Enter>", lambda e, _b=b, _abg=abg: _b.config(bg=_abg))
        b.bind("<Leave>", lambda e, _b=b, _bg=bg:   _b.config(bg=_bg))
        return b

    # ── Custom Segmented & Tab Bar Controller Methods ────────────
    def _set_ck_mode(self, mode):
        self._ck_mode_var.set(mode)
        if mode == "browser":
            self._ck_btn_browser.config(bg=ACCENT, fg="#ffffff")
            self._ck_btn_file.config(bg=SURFACE2, fg=SUBTEXT)
            self._file_frame.pack_forget()
            self._browser_frame.pack(fill="x", pady=(10, 0))
        else:
            self._ck_btn_file.config(bg=ACCENT, fg="#ffffff")
            self._ck_btn_browser.config(bg=SURFACE2, fg=SUBTEXT)
            self._browser_frame.pack_forget()
            self._file_frame.pack(fill="x", pady=(10, 0))

    def _switch_tab(self, tab):
        if self._active_tab == tab:
            return
        self._active_tab = tab
        if tab == "single":
            self._btn_tab_single.config(bg=ACCENT, fg="#ffffff")
            self._btn_tab_playlist.config(bg=SURFACE2, fg=SUBTEXT)
            self._frame_playlist.pack_forget()
            self._frame_single.pack(fill="both", expand=True)
        else:
            self._btn_tab_playlist.config(bg=ACCENT, fg="#ffffff")
            self._btn_tab_single.config(bg=SURFACE2, fg=SUBTEXT)
            self._frame_single.pack_forget()
            self._frame_playlist.pack(fill="both", expand=True)

    def _set_fmt(self, fmt):
        self._format_var.set(fmt)
        self._fmt_btn_video.config(bg=ACCENT if fmt == "video" else SURFACE2, fg="#ffffff" if fmt == "video" else SUBTEXT)
        self._fmt_btn_audio.config(bg=ACCENT if fmt == "audio" else SURFACE2, fg="#ffffff" if fmt == "audio" else SUBTEXT)
        
        if fmt == "video":
            self._audio_opts_frame.pack_forget()
            self._video_opts_frame.pack(fill="x", pady=(10, 0))
        else:
            self._video_opts_frame.pack_forget()
            self._audio_opts_frame.pack(fill="x", pady=(10, 0))

    def _set_pl_fmt(self, fmt):
        self._pl_format_var.set(fmt)
        self._pl_fmt_btn_video.config(bg=ACCENT if fmt == "video" else SURFACE2, fg="#ffffff" if fmt == "video" else SUBTEXT)
        self._pl_fmt_btn_audio.config(bg=ACCENT if fmt == "audio" else SURFACE2, fg="#ffffff" if fmt == "audio" else SUBTEXT)
        
        if fmt == "video":
            self._pl_audio_opts_frame.pack_forget()
            self._pl_video_opts_frame.pack(fill="x", pady=(10, 0))
        else:
            self._pl_video_opts_frame.pack_forget()
            self._pl_audio_opts_frame.pack(fill="x", pady=(10, 0))

    def _clear_url(self):
        self._url_var.set("")
        self._url_entry.config(fg=TEXT)

    def _clear_pl_url(self):
        self._pl_url_var.set("")
        self._pl_url_entry.config(fg=TEXT)

    def _clear_log(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    def _choose_dir_single(self):
        self._choose_dir_for(self._dir_var)

    def _choose_dir_for(self, var):
        d = filedialog.askdirectory(initialdir=var.get() or os.path.expanduser("~"))
        if d:
            var.set(d)

    def _on_ck_mode_change(self):
        if self._ck_mode_var.get() == "browser":
            self._file_frame.pack_forget()
            self._browser_frame.pack(fill="x", pady=(6, 0))
        else:
            self._browser_frame.pack_forget()
            self._file_frame.pack(fill="x", pady=(6, 0))

    def _on_browser_change(self, event=None):
        b = self._browser_var.get().capitalize()
        self._cookies_browser = self._browser_var.get()
        self._ck_status_var.set(f"✅ {b} seçili — her indirmede taze cookies çekilecek")
        _temp_log(f"Tarayıcı değiştirildi: {self._cookies_browser}")

    def _choose_cookies_file(self):
        f = filedialog.askopenfilename(
            title="Cookies dosyasını seçin",
            filetypes=[("Text dosyası", "*.txt"), ("Tüm dosyalar", "*.*")],
            initialdir=os.path.expanduser("~"))
        if f:
            self._cookies_path = f
            name = os.path.basename(f)
            self._cookies_file_var.set(f"✅ {name}")
            self._cookies_file_lbl.config(fg=SUCCESS)
            self._log_line(f"🍪 Cookies dosyası yüklendi: {f}", "success")

    def _clear_cookies_file(self):
        self._cookies_path = None
        self._cookies_file_var.set("Seçilmedi")
        self._cookies_file_lbl.config(fg=SUBTEXT)
        self._log_line("🍪 Cookies dosyası kaldırıldı.", "warn")

    def _get_cookies_args(self):
        """Aktif cookies modu için yt-dlp argümanlarını döndür."""
        if self._ck_mode_var.get() == "browser":
            return ["--cookies-from-browser", self._cookies_browser]
        elif self._cookies_path and os.path.isfile(self._cookies_path):
            return ["--cookies", self._cookies_path]
        return []

    # ── Bağımlılık Kontrolleri ──────────────────────────────────
    def _check_dependencies(self):
        """yt-dlp ve ffmpeg araçlarının sistemde kurulu olup olmadığını arka planda denetler."""
        threading.Thread(target=self._check_deps_thread, daemon=True).start()

    def _check_deps_thread(self):
        ytdlp_ok = False
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.run(["yt-dlp", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
            ytdlp_ok = True
        except Exception:
            pass

        ffmpeg_ok = False
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
            ffmpeg_ok = True
        except Exception:
            pass

        self.after(0, self._report_dependencies, ytdlp_ok, ffmpeg_ok)

    def _report_dependencies(self, ytdlp_ok, ffmpeg_ok):
        if not ytdlp_ok:
            self._log_line("❌ HATA: 'yt-dlp' sisteminizde kurulu veya PATH üzerinde bulunamadı! İndirmeler çalışmayacaktır.", "error")
            self._set_status("❌ Hata: yt-dlp bulunamadı!")
        else:
            self._log_line("✅ Sistem Kontrolü: 'yt-dlp' hazır.", "success")

        if not ffmpeg_ok:
            self._log_line("⚠️ UYARI: 'ffmpeg' sisteminizde bulunamadı! Yüksek çözünürlüklü (1080p ve üzeri) videoların birleştirilmesi ve MP3 ses dönüştürme işlemleri çalışmayabilir.", "warn")
        else:
            self._log_line("✅ Sistem Kontrolü: 'ffmpeg' (medya birleştirici/dönüştürücü) hazır.", "success")

    # ── İstatistik sıfırlama ─────────────────────────────────────
    def _reset_stats(self):
        self._progress["value"] = 0
        self._pct_var.set("0%")
        self._speed_var.set("—")
        self._downloaded_var.set("—")
        self._eta_var.set("—")

    # ── yt-dlp çıktı ayrıştırma ─────────────────────────────────
    # Son derece kararlı ve özel şablonumuz için regex
    _PROGRESS_RE = re.compile(
        r"\[PROGRESS\]\s*(?P<pct>[\d.]+)(?:%\s*)?\|\s*(?P<speed>.*?)\s*\|\s*(?P<total>.*?)\s*\|\s*(?P<eta>.*)"
    )
    # Örnek: [download]  45.2% of  150.32MiB at   5.23MiB/s ETA 00:15
    _DL_RE = re.compile(
        r"\[download\]\s+(?P<pct>[\d.]+)%\s+of\s+~?(?P<total>\S+)\s+"
        r"at\s+(?P<speed>.*?)\s+ETA\s+(?P<eta>\S+)"
    )
    # Tamamlanma: [download] 100% of 150.32MiB in 00:28
    _DL_DONE_RE = re.compile(
        r"\[download\]\s+100%\s+of\s+~?(?P<total>\S+)\s+in\s+(?P<time>\S+)"
    )
    # Playlist ilerlemesi: [download] Downloading video 1 of 10
    _PL_INDEX_RE = re.compile(
        r"\[download\]\s+Downloading\s+video\s+(?P<idx>\d+)\s+of\s+(?P<total>\d+)"
    )

    def _parse_progress(self, line):
        """yt-dlp çıktısından indirme istatistiklerini ayrıştır."""
        # 1. Özel şablonumuzu kontrol et (en kararlısı)
        m = self._PROGRESS_RE.search(line)
        if m:
            try:
                pct = float(m.group("pct").strip())
                speed = m.group("speed").strip()
                total = m.group("total").strip()
                eta = m.group("eta").strip()

                if not speed or "unknown" in speed.lower() or "na" in speed.lower() or speed == "—":
                    speed = "—"
                if not eta or "unknown" in eta.lower() or "na" in eta.lower() or eta == "—":
                    eta = "—"
                if not total or "unknown" in total.lower() or "na" in total.lower() or total == "—":
                    total = "—"

                self.after(0, self._update_stats, pct, speed, total, eta)
                return True
            except Exception as e:
                _temp_log(f"PROGRESS PARSE HATA: {e} - Satır: {line}")
                return False

        # 2. Standart çıktılar için yedek regex'ler
        m = self._DL_RE.search(line)
        if m:
            try:
                pct   = float(m.group("pct"))
                total = m.group("total")
                speed = m.group("speed").strip()
                eta   = m.group("eta").strip()
                
                if "unknown" in speed.lower():
                    speed = "—"
                if "unknown" in eta.lower():
                    eta = "—"
                    
                self.after(0, self._update_stats, pct, speed, total, eta)
                return True
            except Exception:
                pass

        m = self._DL_DONE_RE.search(line)
        if m:
            total = m.group("total")
            self.after(0, self._update_stats, 100.0, "—", total, "Bitti!")
            return True

        m = self._PL_INDEX_RE.search(line)
        if m:
            idx = m.group("idx")
            tot = m.group("total")
            self.after(0, self._set_status, f"⏳ Playlist: Video {idx} / {tot} indiriliyor…")
            return True
        return False

    def _update_stats(self, pct, speed, total, eta):
        self._progress["value"] = pct
        self._pct_var.set(f"{pct:.1f}%")
        self._speed_var.set(speed)
        self._downloaded_var.set(f"{pct:.1f}% / {total}")
        self._eta_var.set(eta)

    # ── İndirme mantığı ──────────────────────────────────────────
    def _clean_url(self, var, ph):
        url = var.get().strip()
        return "" if url == ph else url

    def _start_single(self):
        url = self._clean_url(self._url_var, "https://youtube.com/watch?v=...")
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir URL girin.", parent=self)
            return
        fmt = self._format_var.get()
        out = self._dir_var.get().strip() or self._download_dir

        # Hedef klasörün varlığı ve yazma izinlerinin kontrolü
        if not os.path.exists(out):
            try:
                os.makedirs(out, exist_ok=True)
                self._log_line(f"📁 İndirme klasörü oluşturuldu: {out}", "success")
            except Exception as e:
                messagebox.showerror("Hata", f"Kayıt klasörü oluşturulamadı:\n{e}", parent=self)
                return
        if not os.access(out, os.W_OK):
            messagebox.showerror("Hata", f"Seçilen klasöre yazma izniniz bulunmuyor:\n{out}\nLütfen başka bir klasör seçin.", parent=self)
            return

        cmd = ["yt-dlp", "--newline"]
        cmd += self._get_cookies_args()
        if fmt == "video":
            res = self._res_var.get()
            if "Best" in res:
                cmd += ["-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv+ba/b",
                        "--merge-output-format", "mp4"]
            else:
                num_res = res.replace("p", "")
                cmd += ["-f", f"bestvideo[height<={num_res}][ext=mp4]+bestaudio[ext=m4a]/best[height<={num_res}]",
                        "--merge-output-format", "mp4"]
        else: # audio
            qual = self._audio_qual_var.get()
            if "Best" in qual:
                cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
            else:
                num_qual = qual.replace(" kbps", "")
                cmd += ["-x", "--audio-format", "mp3", "--audio-quality", f"{num_qual}k"]
        cmd += ["--progress-template", "download:[PROGRESS] %(progress._percent_str)s | %(progress._speed_str)s | %(progress._total_bytes_str)s | %(progress._eta_str)s"]
        cmd += ["-o", os.path.join(out, "%(title)s.%(ext)s"), url]
        self._run(cmd, "Tekil indirme")

    def _start_playlist(self):
        url = self._clean_url(self._pl_url_var, "https://youtube.com/playlist?list=...")
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir playlist URL'si girin.", parent=self)
            return
        fmt   = self._pl_format_var.get()
        out   = self._pl_dir_var.get().strip() or self._download_dir
        start = self._pl_start_var.get().strip()
        end   = self._pl_end_var.get().strip()

        # Hedef klasörün varlığı ve yazma izinlerinin kontrolü
        if not os.path.exists(out):
            try:
                os.makedirs(out, exist_ok=True)
                self._log_line(f"📁 İndirme klasörü oluşturuldu: {out}", "success")
            except Exception as e:
                messagebox.showerror("Hata", f"Kayıt klasörü oluşturulamadı:\n{e}", parent=self)
                return
        if not os.access(out, os.W_OK):
            messagebox.showerror("Hata", f"Seçilen klasöre yazma izniniz bulunmuyor:\n{out}\nLütfen başka bir klasör seçin.", parent=self)
            return

        cmd = ["yt-dlp", "--newline"]
        cmd += self._get_cookies_args()
        if fmt == "video":
            res = self._pl_res_var.get()
            if "Best" in res:
                cmd += ["-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv+ba/b",
                        "--merge-output-format", "mp4"]
            else:
                num_res = res.replace("p", "")
                cmd += ["-f", f"bestvideo[height<={num_res}][ext=mp4]+bestaudio[ext=m4a]/best[height<={num_res}]",
                        "--merge-output-format", "mp4"]
        else: # audio
            qual = self._pl_audio_qual_var.get()
            if "Best" in qual:
                cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
            else:
                num_qual = qual.replace(" kbps", "")
                cmd += ["-x", "--audio-format", "mp3", "--audio-quality", f"{num_qual}k"]

        if start or end:
            s = start or "1"
            e = end   or ""
            cmd += ["--playlist-items", f"{s}:{e}" if e else f"{s}:"]

        cmd += ["--progress-template", "download:[PROGRESS] %(progress._percent_str)s | %(progress._speed_str)s | %(progress._total_bytes_str)s | %(progress._eta_str)s"]
        cmd += ["-o",
                os.path.join(out, "%(playlist_title)s",
                             "%(playlist_index)s - %(title)s.%(ext)s"),
                "--yes-playlist", url]
        self._run(cmd, "Playlist indirme")

    def _run(self, cmd, label):
        if self._running:
            _temp_log(f"UYARI: İndirme reddedildi - zaten devam eden bir indirme var")
            messagebox.showinfo("Bilgi", "Zaten bir indirme devam ediyor.", parent=self)
            return
        self._running = True
        self._cancelled = False
        self._reset_stats()
        self._cancel_btn.pack(side="right", padx=(6, 0))
        self._set_status(f"⏳  {label} başlatıldı…")
        self._log_line(f"▶  {label}: {' '.join(cmd)}", "accent")
        _temp_log(f"--- İNDİRME BAŞLATILDI ---")
        _temp_log(f"Tür: {label}")
        _temp_log(f"Komut: {' '.join(cmd)}")
        _temp_log(f"Cookies: {self._cookies_path or 'Yok'}")
        threading.Thread(target=self._run_proc, args=(cmd,), daemon=True).start()

    def _run_proc(self, cmd):
        try:
            # UTF-8 karakter kodlama güvencesi için ortam değişkenlerini kopyala ve zorla
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                creationflags=flags, bufsize=1, env=env)
            for line in iter(self._proc.stdout.readline, ''):
                line = line.rstrip()
                if not line:
                    continue

                # İstatistik satırlarını ayrıştır
                self._parse_progress(line)
                
                # Akıllı hata teşhisi yap
                self._diagnose_errors(line)

                tag = ("error"   if "ERROR"   in line else
                       "warn"    if "WARNING" in line else
                       "success" if ("[download] 100%" in line or "Destination:" in line)
                                 else "info")
                # Do not write standard high-frequency progress info lines to file to prevent log file bloat
                to_file = (tag in ["error", "warn", "success"])
                self.after(0, self._log_line, line, tag, to_file)

            self._proc.wait()
            rc = self._proc.returncode
            if self._cancelled:
                self.after(0, self._set_status, "⛔  İndirme iptal edildi.")
                self.after(0, self._log_line, "⛔  İndirme kullanıcı tarafından iptal edildi.", "warn")
            elif rc == 0:
                self.after(0, self._update_stats, 100.0, "—", "—", "Bitti!")
                self.after(0, self._set_status, "✅  İndirme tamamlandı!")
                self.after(0, self._log_line, "✅  Tamamlandı!", "success")
            else:
                self.after(0, self._set_status, f"❌  Hata (çıkış kodu {rc})")
                self.after(0, self._log_line, f"❌  Hata (kod {rc})", "error")
        except FileNotFoundError:
            self.after(0, self._set_status, "❌  yt-dlp bulunamadı!")
            self.after(0, self._log_line,
                       "❌  'yt-dlp' komutu bulunamadı. PATH'e eklendiğinden emin olun.", "error")
        except Exception as ex:
            self.after(0, self._set_status, f"❌  Beklenmeyen hata!")
            self.after(0, self._log_line, f"❌  Hata: {ex}", "error")
        finally:
            self._proc = None
            self._running = False
            self.after(0, self._cancel_btn.pack_forget)

    def _cancel_download(self):
        """Devam eden indirmeyi iptal et."""
        if not self._running:
            return
        _temp_log("⛔ İPTAL: Kullanıcı indirmeyi manuel olarak iptal etti")
        self._cancelled = True
        proc = self._proc
        if proc:
            try:
                if sys.platform == "win32":
                    # Windows'ta yt-dlp ile birlikte ffmpeg gibi alt süreçlerin de sızıntı yapmadan kapanması için
                    # taskkill ile süreç ağacını (/T) zorla (/F) kapatıyoruz.
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    proc.kill()
                _temp_log("PROC: Süreç ağacı başarıyla sonlandırıldı.")
            except Exception as ex:
                _temp_log(f"PROC HATA: Süreç sonlandırılamadı - {ex}")

    def _log_line(self, text, tag="info", to_file=True):
        if to_file:
            _temp_log(f"[{tag.upper()}] {text}")
        self._log.config(state="normal")
        self._log.insert("end", text + "\n", tag)
        
        # Arayüz donmalarını engellemek için maksimum 2000 satır sınırı uyguluyoruz
        try:
            num_lines = int(self._log.index('end-1c').split('.')[0])
            if num_lines > 2000:
                self._log.delete("1.0", f"{num_lines - 2000}.0")
        except Exception:
            pass
            
        self._log.see("end")
        self._log.config(state="disabled")

    def _set_status(self, msg):
        self._status_var.set(msg)

    def _diagnose_errors(self, line):
        """yt-dlp çıktılarındaki yaygın hata mesajlarını yakalayıp Türkçe akıllı çözüm önerileri sunar."""
        lower_line = line.lower()
        if "confirm your age" in lower_line or "sign in to confirm your age" in lower_line or "age-restricted" in lower_line:
            self.after(0, self._log_line, "💡 ÇÖZÜM ÖNERİSİ: Bu video yaş kısıtlamalıdır. Çerez (Cookies) kaynağını aktif edip tarayıcı seçerek veya cookies.txt yükleyerek tekrar indirmeyi deneyin.", "accent")
        elif "private video" in lower_line:
            self.after(0, self._log_line, "💡 ÇÖZÜM ÖNERİSİ: Bu video gizlidir (özel). İndirebilmek için geçerli çerezler (cookies) kullanmalısınız.", "accent")
        elif "ffmpeg" in lower_line and ("not found" in lower_line or "not recognized" in lower_line or "missing" in lower_line):
            self.after(0, self._log_line, "💡 ÇÖZÜM ÖNERİSİ: Sisteminizde 'ffmpeg' bulunamadı! Lütfen ffmpeg yükleyin ve sistem PATH ortam değişkenine ekleyin.", "accent")
        elif "permission denied" in lower_line or "permissionerror" in lower_line:
            self.after(0, self._log_line, "💡 ÇÖZÜM ÖNERİSİ: Kayıt klasörüne erişim izni reddedildi! Klasör izinlerini denetleyin veya yönetici olarak çalıştırmayı deneyin.", "accent")
        elif "http error 403" in lower_line or "forbidden" in lower_line:
            self.after(0, self._log_line, "💡 ÇÖZÜM ÖNERİSİ: YouTube sunucuları erişimi engelledi (403 Forbidden). Lütfen tarayıcınızdan cookies çekerek kimlik doğrulamasını tazeleyin.", "accent")

    def _on_close(self):
        """Pencere kapatıldığında arka plan sürecini güvenle sonlandırır."""
        if self._running:
            if messagebox.askokcancel("Çıkış", "Devam eden bir indirme işlemi var. Çıkmak istiyor musunuz? İndirme iptal edilecektir.", parent=self):
                self._cancel_download()
                self.destroy()
        else:
            self.destroy()


if __name__ == "__main__":
    app = YTDLPGui()
    app.mainloop()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER, ACCENT, ACCENT_LIGHT, TEXT, SUBTEXT,
    FONT_HERO, FONT_TITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD
)
from ui.components import Card, PillButton, PillChip, ModernEntry, SegmentedPill
from core.config import config

class PlaylistTab(tk.Frame):
    def __init__(self, parent, on_download_requested=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.on_download_requested = on_download_requested
        self._build_ui()

    def _build_ui(self):
        # ── Başlık ───────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 22))

        tk.Label(hdr, text="Oynatma listesi", bg=BG, fg=TEXT, font=FONT_HERO).pack(anchor="w")
        tk.Label(hdr, text="İndirmek istediğiniz aralığı seçin; videolar liste düzeninde kaydedilsin.",
                 bg=BG, fg=SUBTEXT, font=FONT_REGULAR).pack(anchor="w", pady=(6, 0))

        # ── 1. Playlist URL ─────────────────────────────────────────
        c_url = Card(self)
        c_url.pack(fill="x", padx=32, pady=(0, 16))

        tk.Label(c_url, text="OYNATMA LİSTESİ BAĞLANTISI", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w")

        row = tk.Frame(c_url, bg=SURFACE)
        row.pack(fill="x", pady=(8, 0))

        self.url_var = tk.StringVar()
        self.url_entry = ModernEntry(row, textvariable=self.url_var, placeholder="https://youtube.com/playlist?list=...")
        self.url_entry.pack(side="left", fill="x", expand=True)

        PillButton(row, text="Yapıştır", command=self._paste_clipboard, small=True, style="secondary").pack(side="left", padx=(10, 0))
        PillButton(row, text="Temizle", command=self._clear_url, small=True, style="ghost").pack(side="left", padx=(6, 0))

        # ── 2. Format ve Kalite ─────────────────────────────────────
        c_fmt = Card(self)
        c_fmt.pack(fill="x", padx=32, pady=(0, 16))

        tk.Label(c_fmt, text="FORMAT VE KALİTE", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w")

        frow = tk.Frame(c_fmt, bg=SURFACE)
        frow.pack(fill="x", pady=(10, 0))

        self.media_seg = SegmentedPill(
            frow,
            items=[("video", "Video"), ("audio", "Ses")],
            default_val="video",
            on_change=self._on_media_type_changed
        )
        self.media_seg.pack(side="left")

        self.video_opts_frame = tk.Frame(frow, bg=SURFACE)
        self.video_opts_frame.pack(side="left", padx=(20, 0))

        tk.Label(self.video_opts_frame, text="Çözünürlük:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.res_var = tk.StringVar(value=config.get("video_quality", "Best Quality (En İyi)"))
        self.res_cb = ttk.Combobox(
            self.video_opts_frame, textvariable=self.res_var,
            values=["Best Quality (En İyi)", "4320p (8K)", "2160p (4K)", "1440p (2K)", "1080p (FHD)", "720p (HD)", "480p", "360p"],
            state="readonly", width=20, font=FONT_REGULAR
        )
        self.res_cb.pack(side="left", padx=(6, 0))
        self.res_cb.bind("<<ComboboxSelected>>", lambda e: config.set("video_quality", self.res_var.get()))

        self.audio_opts_frame = tk.Frame(frow, bg=SURFACE)
        tk.Label(self.audio_opts_frame, text="Kalite:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.audio_qual_var = tk.StringVar(value=config.get("audio_quality", "Best Quality (En İyi)"))
        self.audio_qual_cb = ttk.Combobox(
            self.audio_opts_frame, textvariable=self.audio_qual_var,
            values=["Best Quality (En İyi)", "320 kbps", "256 kbps", "192 kbps", "128 kbps"],
            state="readonly", width=20, font=FONT_REGULAR
        )
        self.audio_qual_cb.pack(side="left", padx=(6, 0))
        self.audio_qual_cb.bind("<<ComboboxSelected>>", lambda e: config.set("audio_quality", self.audio_qual_var.get()))

        # ── 3. Aralık ve Seçenekler ─────────────────────────────────
        c_range = Card(self)
        c_range.pack(fill="x", padx=32, pady=(0, 16))

        tk.Label(c_range, text="İNDİRME ARALIĞI VE SEÇENEKLER", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w")

        rrow = tk.Frame(c_range, bg=SURFACE)
        rrow.pack(fill="x", pady=(10, 0))

        tk.Label(rrow, text="Başlangıç:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.start_var = tk.StringVar()
        ModernEntry(rrow, textvariable=self.start_var, width=5, placeholder="1").pack(side="left", padx=(6, 20))

        tk.Label(rrow, text="Bitiş:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.end_var = tk.StringVar()
        ModernEntry(rrow, textvariable=self.end_var, width=5, placeholder="Son").pack(side="left", padx=(6, 24))

        self.chip_ignore = PillChip(rrow, text="Hatalı öğeleri atla", initial_value=True)
        self.chip_ignore.pack(side="left", padx=(0, 10))

        self.chip_turbo = PillChip(rrow, text="Çok parçalı indirme", initial_value=True)
        self.chip_turbo.pack(side="left")

        # ── 4. Kayıt Klasörü ────────────────────────────────────────
        c_dir = Card(self)
        c_dir.pack(fill="x", padx=32, pady=(0, 18))

        tk.Label(c_dir, text="KAYIT KLASÖRÜ · LİSTE ADIYLA ALT KLASÖR OLUŞTURULUR",
                 bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w")
        drow = tk.Frame(c_dir, bg=SURFACE)
        drow.pack(fill="x", pady=(8, 0))

        self.dir_var = tk.StringVar(value=config.get("download_dir"))
        ModernEntry(drow, textvariable=self.dir_var).pack(side="left", fill="x", expand=True)

        PillButton(drow, text="Klasör seç", command=self._choose_dir, small=True).pack(side="left", padx=(10, 0))

        # ── 5. İndirme Butonu ────────────────────────────────────────
        PillButton(
            self,
            text="Listeyi indirmeye başla",
            command=self._on_start_click,
            style="primary"
        ).pack(fill="x", padx=32, pady=(0, 24), ipady=3)

    def _on_media_type_changed(self, media_type):
        if media_type == "video":
            self.audio_opts_frame.pack_forget()
            self.video_opts_frame.pack(side="left", padx=(20, 0))
        else:
            self.video_opts_frame.pack_forget()
            self.audio_opts_frame.pack(side="left", padx=(20, 0))

    def _paste_clipboard(self):
        try:
            clip = self.clipboard_get().strip()
            if clip:
                self.url_entry.set_text(clip)
        except Exception:
            pass

    def _clear_url(self):
        self.url_entry.delete(0, "end")
        self.url_entry._apply_placeholder()

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get() or config.get("download_dir"))
        if d:
            self.dir_var.set(d)

    def _on_start_click(self):
        url = self.url_entry.get_clean_text()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir playlist URL'si girin.", parent=self)
            return

        out_dir = self.dir_var.get().strip() or config.get("download_dir")
        media_type = self.media_seg.get()

        options = {
            "mode": "playlist",
            "media_type": media_type,
            "format": config.get("video_format", "mp4") if media_type == "video" else config.get("audio_format", "mp3"),
            "quality": self.res_var.get() if media_type == "video" else self.audio_qual_var.get(),
            "playlist_start": self.start_var.get().strip(),
            "playlist_end": self.end_var.get().strip(),
            "ignore_errors": self.chip_ignore.get(),
            "embed_thumbnail": config.get("embed_thumbnail", True),
            "embed_subtitles": config.get("embed_subtitles", False),
            "subtitle_lang": config.get("subtitle_lang", "tr,en"),
            "add_metadata": config.get("add_metadata", True),
            "speed_limit": config.get("speed_limit", ""),
            "concurrent_fragments": config.get("concurrent_fragments", 4) if self.chip_turbo.get() else 1
        }

        if self.on_download_requested:
            self.on_download_requested(url, out_dir, options)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER, ACCENT, ACCENT_LIGHT, TEXT, SUBTEXT,
    FONT_HERO, FONT_TITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD
)
from ui.components import Card, PillButton, PillChip, ModernEntry, SegmentedPill, ScrollableFrame
from core.config import config


class PlaylistTab(tk.Frame):
    def __init__(self, parent, on_download_requested=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.on_download_requested = on_download_requested
        self._build_ui()

    def _build_ui(self):
        self.scroll_container = ScrollableFrame(self)
        self.scroll_container.pack(fill="both", expand=True)
        scroll_frame = self.scroll_container.inner

        # ── Ana Çalışma Kartı ────────────────────────────────────────
        main_card = Card(scroll_frame, padx=24, pady=20)
        main_card.pack(fill="x", padx=32, pady=(24, 14))

        # 1. URL Satırı
        tk.Label(main_card, text="Oynatma Listesi Bağlantısı", bg=SURFACE, fg=TEXT, font=FONT_BOLD).pack(anchor="w")

        url_row = tk.Frame(main_card, bg=SURFACE)
        url_row.pack(fill="x", pady=(8, 16))

        self.url_var = tk.StringVar()
        self.url_entry = ModernEntry(url_row, textvariable=self.url_var, placeholder="https://www.youtube.com/playlist?list=... bağlantısını yapıştırın")
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=6)

        PillButton(url_row, text="Yapıştır", command=self._paste_clipboard, small=True, style="secondary").pack(side="left", padx=(8, 0))
        PillButton(url_row, text="✕", command=self._clear_url, small=True, style="ghost").pack(side="left", padx=(6, 0))

        tk.Frame(main_card, bg=BORDER, height=1).pack(fill="x", pady=(0, 16))

        # 2. Format ve Kalite Satırı
        frow = tk.Frame(main_card, bg=SURFACE)
        frow.pack(fill="x", pady=(0, 16))

        self.media_seg = SegmentedPill(
            frow,
            items=[("video", "🎬 Video"), ("audio", "🎵 Ses")],
            default_val="video",
            on_change=self._on_media_type_changed
        )
        self.media_seg.pack(side="left")

        self.video_opts_frame = tk.Frame(frow, bg=SURFACE)
        self.video_opts_frame.pack(side="left", padx=(18, 0))

        tk.Label(self.video_opts_frame, text="Format:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.video_ext_var = tk.StringVar(value=config.get("video_format", "mp4"))
        self.video_ext_cb = ttk.Combobox(
            self.video_opts_frame, textvariable=self.video_ext_var,
            values=["mp4", "mkv", "webm"], state="readonly", width=7, font=FONT_REGULAR
        )
        self.video_ext_cb.pack(side="left", padx=(6, 16))
        self.video_ext_cb.bind("<<ComboboxSelected>>", lambda e: config.set("video_format", self.video_ext_var.get()))

        tk.Label(self.video_opts_frame, text="Kalite:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.res_var = tk.StringVar(value=config.get("video_quality", "Best Quality (En İyi)"))
        self.res_cb = ttk.Combobox(
            self.video_opts_frame, textvariable=self.res_var,
            values=["Best Quality (En İyi)", "4320p (8K)", "2160p (4K)", "1440p (2K)", "1080p (FHD)", "720p (HD)", "480p", "360p"],
            state="readonly", width=20, font=FONT_REGULAR
        )
        self.res_cb.pack(side="left", padx=(6, 0))
        self.res_cb.bind("<<ComboboxSelected>>", lambda e: config.set("video_quality", self.res_var.get()))

        self.audio_opts_frame = tk.Frame(frow, bg=SURFACE)
        tk.Label(self.audio_opts_frame, text="Format:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.audio_ext_var = tk.StringVar(value=config.get("audio_format", "mp3"))
        self.audio_ext_cb = ttk.Combobox(
            self.audio_opts_frame, textvariable=self.audio_ext_var,
            values=["mp3", "m4a", "flac", "wav", "opus"], state="readonly", width=7, font=FONT_REGULAR
        )
        self.audio_ext_cb.pack(side="left", padx=(6, 16))
        self.audio_ext_cb.bind("<<ComboboxSelected>>", lambda e: config.set("audio_format", self.audio_ext_var.get()))

        tk.Label(self.audio_opts_frame, text="Kalite:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.audio_qual_var = tk.StringVar(value=config.get("audio_quality", "Best Quality (En İyi)"))
        self.audio_qual_cb = ttk.Combobox(
            self.audio_opts_frame, textvariable=self.audio_qual_var,
            values=["Best Quality (En İyi)", "320 kbps", "256 kbps", "192 kbps", "128 kbps"],
            state="readonly", width=20, font=FONT_REGULAR
        )
        self.audio_qual_cb.pack(side="left", padx=(6, 0))
        self.audio_qual_cb.bind("<<ComboboxSelected>>", lambda e: config.set("audio_quality", self.audio_qual_var.get()))

        # 3. Sıra Aralığı ve Çipler
        rrow = tk.Frame(main_card, bg=SURFACE)
        rrow.pack(fill="x", pady=(0, 16))

        tk.Label(rrow, text="Sıra Aralığı:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.start_var = tk.StringVar()
        self.start_entry = ModernEntry(rrow, textvariable=self.start_var, width=5, placeholder="1")
        self.start_entry.pack(side="left", padx=(8, 4), ipady=3)

        tk.Label(rrow, text="—", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.end_var = tk.StringVar()
        self.end_entry = ModernEntry(rrow, textvariable=self.end_var, width=5, placeholder="Son")
        self.end_entry.pack(side="left", padx=(4, 18), ipady=3)

        self.chip_ignore = PillChip(
            rrow, text="Hatalıları atla",
            initial_value=config.get("ignore_errors", True),
            on_toggle=lambda v: config.set("ignore_errors", v)
        )
        self.chip_ignore.pack(side="left", padx=(0, 8))

        self.chip_archive = PillChip(
            rrow, text="İndirilenleri atla (Arşiv)",
            initial_value=config.get("use_download_archive", False),
            on_toggle=lambda v: config.set("use_download_archive", v)
        )
        self.chip_archive.pack(side="left", padx=(0, 8))

        self.chip_turbo = PillChip(
            rrow, text="Hızlı indirme",
            initial_value=(config.get("concurrent_fragments", 4) > 1),
            on_toggle=lambda v: config.set("concurrent_fragments", 4 if v else 1)
        )
        self.chip_turbo.pack(side="left", padx=(0, 8))

        self.chip_sb = PillChip(
            rrow, text="SponsorBlock",
            initial_value=config.get("sponsorblock_remove", False),
            on_toggle=lambda v: config.set("sponsorblock_remove", v)
        )
        self.chip_sb.pack(side="left")

        # 4. Kayıt Klasörü
        drow = tk.Frame(main_card, bg=SURFACE)
        drow.pack(fill="x")

        tk.Label(drow, text="Kayıt Yeri:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left", padx=(0, 10))
        self.dir_var = tk.StringVar(value=config.get("download_dir"))
        ModernEntry(drow, textvariable=self.dir_var).pack(side="left", fill="x", expand=True, ipady=4)
        PillButton(drow, text="📂 Değiştir", command=self._choose_dir, small=True).pack(side="left", padx=(8, 0))

        # ── İndirme Butonu ───────────────────────────────────────────
        PillButton(
            scroll_frame,
            text="⬇ Listeyi İndirmeye Başla",
            command=self._on_start_click,
            style="primary"
        ).pack(fill="x", padx=32, pady=(0, 20), ipady=4)

    def _on_media_type_changed(self, media_type):
        if media_type == "video":
            self.audio_opts_frame.pack_forget()
            self.video_opts_frame.pack(side="left", padx=(18, 0))
        else:
            self.video_opts_frame.pack_forget()
            self.audio_opts_frame.pack(side="left", padx=(18, 0))

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
            config.set("download_dir", d)

    def _on_start_click(self):
        url = self.url_entry.get_clean_text()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir playlist URL'si girin.", parent=self)
            return

        out_dir = self.dir_var.get().strip() or config.get("download_dir")
        config.set("download_dir", out_dir)
        media_type = self.media_seg.get()

        options = {
            "mode": "playlist",
            "media_type": media_type,
            "format": self.video_ext_var.get() if media_type == "video" else self.audio_ext_var.get(),
            "quality": self.res_var.get() if media_type == "video" else self.audio_qual_var.get(),
            "playlist_start": self.start_entry.get_clean_text(),
            "playlist_end": self.end_entry.get_clean_text(),
            "ignore_errors": self.chip_ignore.get(),
            "use_download_archive": self.chip_archive.get(),
            "sponsorblock_remove": self.chip_sb.get(),
            "sponsorblock_cats": config.get("sponsorblock_cats", "sponsor,intro,outro,selfpromo,interaction"),
            "embed_thumbnail": config.get("embed_thumbnail", True),
            "embed_subtitles": config.get("embed_subtitles", False),
            "subtitle_lang": config.get("subtitle_lang", "tr,en"),
            "add_metadata": config.get("add_metadata", True),
            "speed_limit": config.get("speed_limit", ""),
            "concurrent_fragments": max(2, config.get("concurrent_fragments", 4)) if self.chip_turbo.get() else 1
        }

        if self.on_download_requested:
            self.on_download_requested(url, out_dir, options)

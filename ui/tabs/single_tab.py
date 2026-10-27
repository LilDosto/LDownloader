import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER, ACCENT, ACCENT_LIGHT, TEXT, SUBTEXT, MUTED,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD
)
from ui.components import Card, PillButton, PillChip, ModernEntry, SegmentedPill, VideoPreviewCard
from core.config import config
from core.metadata import fetch_video_metadata

class SingleTab(tk.Frame):
    def __init__(self, parent, on_download_requested=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.on_download_requested = on_download_requested
        self.current_metadata = None
        self._metadata_url = ""
        self._metadata_request_id = 0
        self._metadata_after_id = None
        self._build_ui()

    def _build_ui(self):
        # Scrollable alan
        scroll_frame = tk.Frame(self, bg=BG)
        scroll_frame.pack(fill="both", expand=True)

        # ── Başlık Alanı ─────────────────────────────────────────────
        hdr = tk.Frame(scroll_frame, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 22))

        tk.Label(hdr, text="Medya indir", bg=BG, fg=TEXT, font=FONT_HERO).pack(anchor="w")
        tk.Label(hdr, text="Bir bağlantı yapıştırın; video veya ses olarak kaydedin.",
                 bg=BG, fg=SUBTEXT, font=FONT_REGULAR).pack(anchor="w", pady=(6, 0))

        # ── 1. URL Giriş Kartı ──────────────────────────────────────
        c_url = Card(scroll_frame)
        c_url.pack(fill="x", padx=32, pady=(0, 16))

        tk.Label(c_url, text="MEDYA BAĞLANTISI", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w")

        row = tk.Frame(c_url, bg=SURFACE)
        row.pack(fill="x", pady=(8, 0))

        self.url_var = tk.StringVar()
        self.url_entry = ModernEntry(
            row, textvariable=self.url_var,
            placeholder="https://youtube.com/watch?v=... veya desteklenen bir link",
            on_change=self._on_url_typed
        )
        self.url_entry.pack(side="left", fill="x", expand=True)

        PillButton(row, text="Yapıştır", command=self._paste_clipboard, small=True, style="secondary").pack(side="left", padx=(10, 0))
        PillButton(row, text="Temizle", command=self._clear_url, small=True, style="ghost").pack(side="left", padx=(6, 0))

        # ── 2. Video Önizleme (Başlangıçta Gizli) ───────────────────
        self.preview_card = VideoPreviewCard(scroll_frame)

        # ── 3. Format ve Kalite ──────────────────────────────────────
        c_fmt = Card(scroll_frame)
        c_fmt.pack(fill="x", padx=32, pady=(0, 16))
        self.format_card = c_fmt

        tk.Label(c_fmt, text="FORMAT VE KALİTE", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w")

        fmt_controls = tk.Frame(c_fmt, bg=SURFACE)
        fmt_controls.pack(fill="x", pady=(10, 0))

        # Medya Tipi
        self.media_seg = SegmentedPill(
            fmt_controls,
            items=[("video", "Video"), ("audio", "Ses")],
            default_val="video",
            on_change=self._on_media_type_changed
        )
        self.media_seg.pack(side="left")

        # Video Seçenekleri
        self.video_opts_frame = tk.Frame(fmt_controls, bg=SURFACE)
        self.video_opts_frame.pack(side="left", padx=(20, 0))

        tk.Label(self.video_opts_frame, text="Format:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.video_ext_var = tk.StringVar(value=config.get("video_format", "mp4"))
        self.video_ext_cb = ttk.Combobox(
            self.video_opts_frame, textvariable=self.video_ext_var,
            values=["mp4", "mkv", "webm"], state="readonly", width=7, font=FONT_REGULAR
        )
        self.video_ext_cb.pack(side="left", padx=(6, 16))
        self.video_ext_cb.bind(
            "<<ComboboxSelected>>",
            lambda e: config.set("video_format", self.video_ext_var.get())
        )

        tk.Label(self.video_opts_frame, text="Çözünürlük:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.res_var = tk.StringVar(value=config.get("video_quality", "Best Quality (En İyi)"))
        self.res_cb = ttk.Combobox(
            self.video_opts_frame, textvariable=self.res_var,
            values=["Best Quality (En İyi)", "4320p (8K)", "2160p (4K)", "1440p (2K)", "1080p (FHD)", "720p (HD)", "480p", "360p"],
            state="readonly", width=20, font=FONT_REGULAR
        )
        self.res_cb.pack(side="left", padx=(6, 0))
        self.res_cb.bind(
            "<<ComboboxSelected>>",
            lambda e: config.set("video_quality", self.res_var.get())
        )

        # Ses Seçenekleri (Başlangıçta Gizli)
        self.audio_opts_frame = tk.Frame(fmt_controls, bg=SURFACE)
        tk.Label(self.audio_opts_frame, text="Format:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.audio_ext_var = tk.StringVar(value=config.get("audio_format", "mp3"))
        self.audio_ext_cb = ttk.Combobox(
            self.audio_opts_frame, textvariable=self.audio_ext_var,
            values=["mp3", "m4a", "flac", "wav", "opus"], state="readonly", width=7, font=FONT_REGULAR
        )
        self.audio_ext_cb.pack(side="left", padx=(6, 16))
        self.audio_ext_cb.bind(
            "<<ComboboxSelected>>",
            lambda e: config.set("audio_format", self.audio_ext_var.get())
        )

        tk.Label(self.audio_opts_frame, text="Kalite:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.audio_qual_var = tk.StringVar(value=config.get("audio_quality", "Best Quality (En İyi)"))
        self.audio_qual_cb = ttk.Combobox(
            self.audio_opts_frame, textvariable=self.audio_qual_var,
            values=["Best Quality (En İyi)", "320 kbps", "256 kbps", "192 kbps", "128 kbps"],
            state="readonly", width=20, font=FONT_REGULAR
        )
        self.audio_qual_cb.pack(side="left", padx=(6, 0))
        self.audio_qual_cb.bind(
            "<<ComboboxSelected>>",
            lambda e: config.set("audio_quality", self.audio_qual_var.get())
        )

        # Ayar Çipleri
        chips_row = tk.Frame(c_fmt, bg=SURFACE)
        chips_row.pack(fill="x", pady=(14, 2))

        self.chip_sub = PillChip(chips_row, text="Altyazıyı ekle", initial_value=config.get("embed_subtitles", False))
        self.chip_sub.pack(side="left", padx=(0, 10))

        self.chip_thumb = PillChip(chips_row, text="Kapak görseli", initial_value=config.get("embed_thumbnail", True))
        self.chip_thumb.pack(side="left", padx=(0, 10))

        self.chip_turbo = PillChip(chips_row, text="Çok parçalı indirme", initial_value=(config.get("concurrent_fragments", 4) > 1))
        self.chip_turbo.pack(side="left")

        # ── 4. Kayıt Klasörü ────────────────────────────────────────
        c_dir = Card(scroll_frame)
        c_dir.pack(fill="x", padx=32, pady=(0, 18))

        tk.Label(c_dir, text="KAYIT KLASÖRÜ", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w")
        drow = tk.Frame(c_dir, bg=SURFACE)
        drow.pack(fill="x", pady=(8, 0))

        self.dir_var = tk.StringVar(value=config.get("download_dir"))
        ModernEntry(drow, textvariable=self.dir_var).pack(side="left", fill="x", expand=True)
        PillButton(drow, text="Klasör seç", command=self._choose_dir, small=True).pack(side="left", padx=(10, 0))

        # ── 5. İndirme Butonu ────────────────────────────────────────
        self.btn_download = PillButton(
            scroll_frame,
            text="İndirmeyi başlat",
            command=self._on_start_click,
            style="primary"
        )
        self.btn_download.pack(fill="x", padx=32, pady=(0, 24), ipady=3)

    def _on_media_type_changed(self, media_type):
        if media_type == "video":
            self.audio_opts_frame.pack_forget()
            self.video_opts_frame.pack(side="left", padx=(20, 0))
            self.btn_download.config(text="İndirmeyi başlat")
        else:
            self.video_opts_frame.pack_forget()
            self.audio_opts_frame.pack(side="left", padx=(20, 0))
            self.btn_download.config(text="İndirmeyi başlat")

    def _paste_clipboard(self):
        try:
            clip = self.clipboard_get().strip()
            if clip and clip.startswith("http"):
                self.url_entry.set_text(clip)
        except Exception:
            pass

    def _on_url_typed(self, text):
        if text == self._metadata_url:
            return

        self._metadata_url = text
        self._metadata_request_id += 1
        request_id = self._metadata_request_id
        self.current_metadata = None
        self.preview_card.pack_forget()
        self.res_cb.config(values=[
            "Best Quality (En İyi)", "4320p (8K)", "2160p (4K)",
            "1440p (2K)", "1080p (FHD)", "720p (HD)", "480p", "360p"
        ])
        self.res_var.set("Best Quality (En İyi)")
        self._set_download_button_ready()

        if self._metadata_after_id:
            self.after_cancel(self._metadata_after_id)
            self._metadata_after_id = None

        if (
            config.get("auto_fetch_metadata", True)
            and len(text) > 15
            and (text.startswith("http://") or text.startswith("https://"))
        ):
            self._metadata_after_id = self.after(
                500, self._auto_fetch_metadata, text, request_id
            )

    def _auto_fetch_metadata(self, url, request_id):
        self._metadata_after_id = None
        self.btn_download.config(state="disabled", text="⏳ Video Bilgileri Alınıyor...")
        fetch_video_metadata(
            url,
            callback=lambda metadata: self._on_metadata_loaded(metadata, request_id, url),
            error_callback=lambda err: self._on_metadata_error(err, request_id, url)
        )

    def _on_metadata_loaded(self, metadata, request_id, url):
        self.after(0, self._apply_metadata, metadata, request_id, url)

    def _apply_metadata(self, metadata, request_id, url):
        if request_id != self._metadata_request_id or url != self.url_entry.get_clean_text():
            return
        self.current_metadata = metadata
        self.preview_card.update_metadata(metadata)
        self.preview_card.pack(fill="x", padx=32, pady=(0, 16), before=self.format_card)

        if metadata.get("resolutions"):
            self.res_cb.config(values=metadata["resolutions"])
            self.res_var.set(metadata["resolutions"][0])

        self._set_download_button_ready()

    def _on_metadata_error(self, err, request_id, url):
        self.after(0, self._restore_download_button, request_id, url)

    def _restore_download_button(self, request_id, url):
        if request_id == self._metadata_request_id and url == self.url_entry.get_clean_text():
            self._set_download_button_ready()

    def _set_download_button_ready(self):
        self.btn_download.config(state="normal", text="İndirmeyi başlat")

    def _clear_url(self):
        self.url_entry.delete(0, "end")
        self.url_entry._apply_placeholder()
        self.preview_card.pack_forget()
        self.current_metadata = None
        self._metadata_url = ""
        self._metadata_request_id += 1
        self._set_download_button_ready()
        if self._metadata_after_id:
            self.after_cancel(self._metadata_after_id)
            self._metadata_after_id = None

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get() or config.get("download_dir"))
        if d:
            self.dir_var.set(d)
            config.set("download_dir", d)

    def _on_start_click(self):
        url = self.url_entry.get_clean_text()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir video veya ses URL'si girin.", parent=self)
            return

        out_dir = self.dir_var.get().strip() or config.get("download_dir")
        media_type = self.media_seg.get()

        options = {
            "mode": "single",
            "media_type": media_type,
            "format": self.video_ext_var.get() if media_type == "video" else self.audio_ext_var.get(),
            "quality": self.res_var.get() if media_type == "video" else self.audio_qual_var.get(),
            "embed_subtitles": self.chip_sub.get(),
            "embed_thumbnail": self.chip_thumb.get(),
            "concurrent_fragments": config.get("concurrent_fragments", 4) if self.chip_turbo.get() else 1,
            "add_metadata": config.get("add_metadata", True),
            "subtitle_lang": config.get("subtitle_lang", "tr,en"),
            "speed_limit": config.get("speed_limit", ""),
            "ignore_errors": config.get("ignore_errors", True),
            "title": self.current_metadata.get("title") if self.current_metadata else None
        }

        if self.on_download_requested:
            self.on_download_requested(url, out_dir, options)

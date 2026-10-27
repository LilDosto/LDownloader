import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER, ACCENT, ACCENT_LIGHT, TEXT, SUBTEXT, MUTED,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD
)
from ui.components import Card, PillButton, PillChip, ModernEntry, SegmentedPill, VideoPreviewCard, ScrollableFrame
from core.config import config
from core.metadata import fetch_video_metadata
from core.dependencies import resolve_cookies_args


class SingleTab(tk.Frame):
    def __init__(self, parent, on_download_requested=None, on_switch_to_playlist=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.on_download_requested = on_download_requested
        self.on_switch_to_playlist = on_switch_to_playlist
        self.current_metadata = None
        self._metadata_url = ""
        self._metadata_request_id = 0
        self._metadata_after_id = None
        self._adv_open = False
        self._build_ui()

    def _build_ui(self):
        self.scroll_container = ScrollableFrame(self)
        self.scroll_container.pack(fill="both", expand=True)
        scroll_frame = self.scroll_container.inner

        # ── Ana Çalışma Kartı ────────────────────────────────────────
        main_card = Card(scroll_frame, padx=24, pady=20)
        main_card.pack(fill="x", padx=32, pady=(24, 14))
        self.main_card = main_card

        # 1. URL Satırı
        url_hdr = tk.Frame(main_card, bg=SURFACE)
        url_hdr.pack(fill="x")
        tk.Label(url_hdr, text="Medya Bağlantısı", bg=SURFACE, fg=TEXT, font=FONT_BOLD).pack(side="left")
        self.lbl_meta_status = tk.Label(url_hdr, text="", bg=SURFACE, fg=ACCENT_LIGHT, font=FONT_SMALL)
        self.lbl_meta_status.pack(side="right")

        url_row = tk.Frame(main_card, bg=SURFACE)
        url_row.pack(fill="x", pady=(8, 16))

        self.url_var = tk.StringVar()
        self.url_entry = ModernEntry(
            url_row, textvariable=self.url_var,
            placeholder="https://www.youtube.com/watch?v=... bağlantısını yapıştırın",
            on_change=self._on_url_typed
        )
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=6)

        PillButton(url_row, text="Yapıştır", command=self._paste_clipboard, small=True, style="secondary").pack(side="left", padx=(8, 0))
        PillButton(url_row, text="✕", command=self._clear_url, small=True, style="ghost").pack(side="left", padx=(6, 0))

        # ── Önizleme Kartı (Dinamik olarak URL altına yerleşir) ──────
        self.preview_card = VideoPreviewCard(main_card)

        # İnce Ayraç
        self.divider = tk.Frame(main_card, bg=BORDER, height=1)
        self.divider.pack(fill="x", pady=(0, 16))

        # 2. Format ve Kalite Satırı
        fmt_row = tk.Frame(main_card, bg=SURFACE)
        fmt_row.pack(fill="x", pady=(0, 16))

        self.media_seg = SegmentedPill(
            fmt_row,
            items=[("video", "🎬 Video"), ("audio", "🎵 Ses")],
            default_val="video",
            on_change=self._on_media_type_changed
        )
        self.media_seg.pack(side="left")

        # Video Seçenekleri
        self.video_opts_frame = tk.Frame(fmt_row, bg=SURFACE)
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

        # Ses Seçenekleri (Başlangıçta Gizli)
        self.audio_opts_frame = tk.Frame(fmt_row, bg=SURFACE)
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

        # Sağda: Gelişmiş Seçenekler Aç/Kapa Butonu
        self.btn_adv = PillButton(
            fmt_row, text="⚙ Ek Seçenekler ▾", command=self._toggle_advanced, small=True, style="ghost"
        )
        self.btn_adv.pack(side="right")

        # 3. Gizlenebilir Gelişmiş Seçenekler Alanı (Başlangıçta Kapalı)
        self.adv_frame = tk.Frame(main_card, bg=SURFACE_LIGHT, padx=14, pady=12, highlightthickness=1, highlightbackground=BORDER)

        chips_row = tk.Frame(self.adv_frame, bg=SURFACE_LIGHT)
        chips_row.pack(fill="x")

        self.chip_sub = PillChip(
            chips_row, text="Altyazı göm",
            initial_value=config.get("embed_subtitles", False),
            on_toggle=lambda v: config.set("embed_subtitles", v)
        )
        self.chip_sub.pack(side="left", padx=(0, 8))

        self.chip_thumb = PillChip(
            chips_row, text="Kapak resmi",
            initial_value=config.get("embed_thumbnail", True),
            on_toggle=lambda v: config.set("embed_thumbnail", v)
        )
        self.chip_thumb.pack(side="left", padx=(0, 8))

        self.chip_turbo = PillChip(
            chips_row, text="Hızlı indirme",
            initial_value=(config.get("concurrent_fragments", 4) > 1),
            on_toggle=lambda v: config.set("concurrent_fragments", 4 if v else 1)
        )
        self.chip_turbo.pack(side="left", padx=(0, 8))

        self.chip_sb = PillChip(
            chips_row, text="SponsorBlock",
            initial_value=config.get("sponsorblock_remove", False),
            on_toggle=lambda v: config.set("sponsorblock_remove", v)
        )
        self.chip_sb.pack(side="left")

        clip_row = tk.Frame(self.adv_frame, bg=SURFACE_LIGHT)
        clip_row.pack(fill="x", pady=(10, 0))

        tk.Label(clip_row, text="✂️ Bölüm Kes:", bg=SURFACE_LIGHT, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(side="left")
        self.clip_start_var = tk.StringVar()
        self.clip_start_entry = ModernEntry(clip_row, textvariable=self.clip_start_var, width=8, placeholder="01:20")
        self.clip_start_entry.pack(side="left", padx=(8, 4), ipady=2)

        tk.Label(clip_row, text="—", bg=SURFACE_LIGHT, fg=SUBTEXT, font=FONT_SMALL).pack(side="left")
        self.clip_end_var = tk.StringVar()
        self.clip_end_entry = ModernEntry(clip_row, textvariable=self.clip_end_var, width=8, placeholder="03:45")
        self.clip_end_entry.pack(side="left", padx=(4, 8), ipady=2)

        PillButton(clip_row, text="Sıfırla", command=self._clear_clip, small=True, style="ghost").pack(side="left")

        # 4. Kayıt Klasörü Satırı
        self.dir_row = tk.Frame(main_card, bg=SURFACE)
        self.dir_row.pack(fill="x")

        tk.Label(self.dir_row, text="Kayıt Yeri:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left", padx=(0, 10))
        self.dir_var = tk.StringVar(value=config.get("download_dir"))
        ModernEntry(self.dir_row, textvariable=self.dir_var).pack(side="left", fill="x", expand=True, ipady=4)
        PillButton(self.dir_row, text="📂 Değiştir", command=self._choose_dir, small=True).pack(side="left", padx=(8, 0))

        # ── İndirme Butonu ───────────────────────────────────────────
        self.btn_download = PillButton(
            scroll_frame,
            text="⬇ İndirmeyi Başlat",
            command=self._on_start_click,
            style="primary"
        )
        self.btn_download.pack(fill="x", padx=32, pady=(0, 20), ipady=4)

    def _toggle_advanced(self):
        self._adv_open = not self._adv_open
        if self._adv_open:
            self.adv_frame.pack(fill="x", pady=(0, 16), before=self.dir_row)
            self.btn_adv.config(text="⚙ Ek Seçenekler ▴")
        else:
            self.adv_frame.pack_forget()
            self.btn_adv.config(text="⚙ Ek Seçenekler ▾")

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

    def _on_url_typed(self, text):
        if text == self._metadata_url:
            return

        self._metadata_url = text
        self._metadata_request_id += 1
        request_id = self._metadata_request_id
        self.current_metadata = None
        self.preview_card.pack_forget()
        self.lbl_meta_status.config(text="")
        self.res_cb.config(values=[
            "Best Quality (En İyi)", "4320p (8K)", "2160p (4K)",
            "1440p (2K)", "1080p (FHD)", "720p (HD)", "480p", "360p"
        ])
        self.res_var.set(config.get("video_quality", "Best Quality (En İyi)"))
        self._set_download_button_ready()

        if self._metadata_after_id:
            self.after_cancel(self._metadata_after_id)
            self._metadata_after_id = None

        if (
            config.get("auto_fetch_metadata", True)
            and len(text) > 12
            and (text.startswith("http://") or text.startswith("https://"))
        ):
            self._metadata_after_id = self.after(
                450, self._auto_fetch_metadata, text, request_id
            )

    def _get_safe_cookies_args(self):
        try:
            return resolve_cookies_args(
                config.get("cookies_mode", "none"),
                config.get("cookies_browser", "chrome"),
                config.get("cookies_path", "")
            )
        except Exception:
            return []

    def _auto_fetch_metadata(self, url, request_id):
        self._metadata_after_id = None
        self.lbl_meta_status.config(text="⏳ Önizleme yükleniyor...")
        fetch_video_metadata(
            url,
            cookies_args=self._get_safe_cookies_args(),
            proxy=config.get("proxy", ""),
            callback=lambda metadata: self._on_metadata_loaded(metadata, request_id, url),
            error_callback=lambda err: self._on_metadata_error(err, request_id, url)
        )

    def _on_metadata_loaded(self, metadata, request_id, url):
        self.after(0, self._apply_metadata, metadata, request_id, url)

    def _apply_metadata(self, metadata, request_id, url):
        if request_id != self._metadata_request_id or url != self.url_entry.get_clean_text():
            return
        self.current_metadata = metadata
        self.lbl_meta_status.config(text="")
        self.preview_card.update_metadata(
            metadata,
            on_playlist_switch=(lambda: self.on_switch_to_playlist(url)) if self.on_switch_to_playlist else None
        )
        self.preview_card.pack(fill="x", pady=(0, 16), before=self.divider)

        if metadata.get("resolutions"):
            self.res_cb.config(values=metadata["resolutions"])
            self.res_var.set(metadata["resolutions"][0])

        self._set_download_button_ready()

    def _on_metadata_error(self, err, request_id, url):
        self.after(0, self._restore_download_button, request_id, url)

    def _restore_download_button(self, request_id, url):
        if request_id == self._metadata_request_id and url == self.url_entry.get_clean_text():
            self.lbl_meta_status.config(text="")
            self._set_download_button_ready()

    def _set_download_button_ready(self):
        self.btn_download.config(state="normal", text="⬇ İndirmeyi Başlat")

    def _clear_clip(self):
        self.clip_start_entry.set_text("")
        self.clip_end_entry.set_text("")

    def _clear_url(self):
        self.url_entry.delete(0, "end")
        self.url_entry._apply_placeholder()
        self.preview_card.pack_forget()
        self.lbl_meta_status.config(text="")
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
        config.set("download_dir", out_dir)
        media_type = self.media_seg.get()

        options = {
            "mode": "single",
            "media_type": media_type,
            "format": self.video_ext_var.get() if media_type == "video" else self.audio_ext_var.get(),
            "quality": self.res_var.get() if media_type == "video" else self.audio_qual_var.get(),
            "embed_subtitles": self.chip_sub.get(),
            "embed_thumbnail": self.chip_thumb.get(),
            "concurrent_fragments": max(2, config.get("concurrent_fragments", 4)) if self.chip_turbo.get() else 1,
            "add_metadata": config.get("add_metadata", True),
            "subtitle_lang": config.get("subtitle_lang", "tr,en"),
            "speed_limit": config.get("speed_limit", ""),
            "ignore_errors": config.get("ignore_errors", True),
            "sponsorblock_remove": self.chip_sb.get(),
            "sponsorblock_cats": config.get("sponsorblock_cats", "sponsor,intro,outro,selfpromo,interaction"),
            "use_download_archive": config.get("use_download_archive", False),
            "clip_start": self.clip_start_entry.get_clean_text(),
            "clip_end": self.clip_end_entry.get_clean_text(),
            "title": self.current_metadata.get("title") if self.current_metadata else None
        }

        if self.on_download_requested:
            self.on_download_requested(url, out_dir, options)

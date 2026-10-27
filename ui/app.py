import os
import sys
import ctypes
import threading
import tkinter as tk
from tkinter import messagebox

from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER,
    ACCENT, ACCENT_LIGHT, ACCENT_MUTED, TEXT, SUBTEXT, MUTED, SUCCESS, WARNING, ERROR,
    TAB_BG,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD,
    apply_theme
)
from ui.components import TabButton, PillButton, ContextualDownloadDrawer
from ui.tabs.single_tab import SingleTab
from ui.tabs.playlist_tab import PlaylistTab
from ui.tabs.batch_tab import BatchTab
from ui.tabs.history_tab import HistoryTab
from ui.tabs.settings_tab import SettingsTab

from core.config import config, get_app_dir
from core.downloader import engine, build_command
from core.history import history
from core.dependencies import get_ytdlp_status, get_ffmpeg_status, get_js_status

class LDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LDownloader v3")
        self.geometry("980x660")
        self.minsize(880, 580)
        self.configure(bg=BG)

        # Windows Yüksek DPI ve AppUserModelID yapılandırması
        if sys.platform == "win32":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ldownloader.modern.gui.3")
            except Exception:
                pass

        # Ekranı ortala
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        width = min(980, sw - 80)
        height = min(660, sh - 100)
        x = max(0, (sw - width) // 2)
        y = max(0, (sh - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # İkon ve Logo
        self._load_icons()

        # Tema ve stiller
        apply_theme(self, config.get("theme", "dark"))

        # Durum değişkenleri
        self.active_tab_name = "single"
        self.current_download_file = None
        self._batch_running = False

        # Ana Düzen
        self._build_layout()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Sistem durumunu arka planda kontrol et
        self._update_system_status()

    def _load_icons(self):
        app_dir = get_app_dir()
        ico_path = os.path.join(app_dir, "assets", "logo.ico")
        if not os.path.isfile(ico_path):
            ico_path = os.path.join(app_dir, "logo.ico")
        if os.path.isfile(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        self.logo_img = None
        self.window_icon_img = None
        png_path = os.path.join(app_dir, "assets", "logo.png")
        if not os.path.isfile(png_path):
            png_path = os.path.join(app_dir, "logo.png")
        if os.path.isfile(png_path):
            try:
                raw = tk.PhotoImage(file=png_path)
                self.window_icon_img = raw
                self.iconphoto(True, raw)
                factor = max(1, raw.width() // 24)
                self.logo_img = raw.subsample(factor, factor)
            except Exception:
                pass

    def _build_layout(self):
        # ── Birleşik Üst Çubuk (Logo + Sekmeler + Durum) ────────────
        top_bar = tk.Frame(self, bg=TAB_BG, padx=24, pady=8)
        top_bar.pack(fill="x")

        # Sol: Logo + Başlık
        brand_frame = tk.Frame(top_bar, bg=TAB_BG)
        brand_frame.pack(side="left", padx=(0, 24))

        if self.logo_img:
            tk.Label(brand_frame, image=self.logo_img, bg=TAB_BG).pack(side="left", padx=(0, 8))

        tk.Label(brand_frame, text="LDownloader v3", font=FONT_TITLE, bg=TAB_BG, fg=TEXT).pack(side="left")

        # Orta: Sekmeler
        self.nav_buttons = {}
        nav_items = [
            ("single", "▶", "Tekli"),
            ("playlist", "≡", "Playlist"),
            ("batch", "+", "Toplu"),
            ("history", "↺", "Geçmiş"),
            ("settings", "⚙", "Ayarlar")
        ]

        for key, icon, label in nav_items:
            btn = TabButton(
                top_bar,
                icon=icon,
                text=label,
                command=lambda k=key: self.switch_tab(k),
                is_active=(key == "single")
            )
            btn.pack(side="left", padx=(0, 4))
            self.nav_buttons[key] = btn

        # Sağ: Sistem durumu + Tema
        self.lbl_sys_status = tk.Label(
            top_bar, text="● Kontrol ediliyor", bg=ACCENT_MUTED, fg=ACCENT_LIGHT,
            font=FONT_SMALL_BOLD, anchor="e", padx=10, pady=5, cursor="hand2",
            highlightthickness=1, highlightbackground=BORDER
        )
        self.lbl_sys_status.pack(side="right")
        self.lbl_sys_status.bind("<Button-1>", lambda e: self.switch_tab("settings"))

        self.btn_theme = PillButton(
            top_bar,
            text="☀" if config.get("theme", "dark") == "dark" else "🌙",
            command=self._toggle_theme,
            small=True,
            style="secondary",
        )
        self.btn_theme.pack(side="right", padx=(0, 8))

        # Alttaki ince ayraç
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Ana İçerik Alanı ─────────────────────────────────────────
        self.main_area = tk.Frame(self, bg=BG)
        self.main_area.pack(fill="both", expand=True)

        # İçerik Kapsayıcısı (Scrollable alan)
        self.content_container = tk.Frame(self.main_area, bg=BG)
        self.content_container.pack(fill="both", expand=True)

        # Alt İndirme Çekmecesi
        self.drawer = ContextualDownloadDrawer(
            self.main_area,
            on_cancel=self._on_cancel_download,
            on_open_file=self._open_downloaded_file
        )

        # Sekmeleri Başlat
        self.tabs = {
            "single": SingleTab(
                self.content_container,
                on_download_requested=self.start_single_download,
                on_switch_to_playlist=self._transfer_to_playlist
            ),
            "playlist": PlaylistTab(self.content_container, on_download_requested=self.start_playlist_download),
            "batch": BatchTab(self.content_container, on_batch_requested=self.start_batch_download),
            "history": HistoryTab(self.content_container),
            "settings": SettingsTab(self.content_container, on_dependency_updated=self._on_deps_updated)
        }

        self.switch_tab("single")

    def _transfer_to_playlist(self, url):
        playlist = self.tabs.get("playlist")
        if playlist and url:
            playlist.url_entry.set_text(url)
            self.switch_tab("playlist")

    def _capture_layout_state(self):
        state = {"active_tab": self.active_tab_name}
        single = self.tabs.get("single")
        if single:
            state["single"] = {
                "url": single.url_entry.get_clean_text(),
                "dir": single.dir_var.get(),
                "media": single.media_seg.get(),
                "video_format": single.video_ext_var.get(),
                "video_quality": single.res_var.get(),
                "audio_format": single.audio_ext_var.get(),
                "audio_quality": single.audio_qual_var.get(),
                "subtitles": single.chip_sub.get(),
                "thumbnail": single.chip_thumb.get(),
                "turbo": single.chip_turbo.get(),
                "sponsorblock": single.chip_sb.get(),
                "clip_start": single.clip_start_entry.get_clean_text(),
                "clip_end": single.clip_end_entry.get_clean_text(),
                "adv_open": single._adv_open,
                "metadata": single.current_metadata,
            }

        playlist = self.tabs.get("playlist")
        if playlist:
            state["playlist"] = {
                "url": playlist.url_entry.get_clean_text(),
                "dir": playlist.dir_var.get(),
                "media": playlist.media_seg.get(),
                "video_format": playlist.video_ext_var.get(),
                "video_quality": playlist.res_var.get(),
                "audio_format": playlist.audio_ext_var.get(),
                "audio_quality": playlist.audio_qual_var.get(),
                "start": playlist.start_entry.get_clean_text(),
                "end": playlist.end_entry.get_clean_text(),
                "ignore_errors": playlist.chip_ignore.get(),
                "turbo": playlist.chip_turbo.get(),
                "archive": playlist.chip_archive.get(),
                "sponsorblock": playlist.chip_sb.get(),
            }

        batch = self.tabs.get("batch")
        if batch:
            state["batch"] = {
                "input": batch.text_input.get("1.0", "end-1c"),
                "dir": batch.dir_var.get(),
                "media": batch.media_seg.get(),
                "queue": [dict(item) for item in batch.queue],
            }

        history_tab = self.tabs.get("history")
        if history_tab:
            state["history_search"] = history_tab.search_entry.get_clean_text()

        state["drawer"] = {
            "visible": bool(self.drawer.winfo_manager()),
            "title": self.drawer.lbl_title.cget("text"),
            "progress": self.drawer.pbar["value"],
            "logs": self.drawer.log_text.get("1.0", "end-1c"),
            "console_open": self.drawer.console_open,
            "completed": bool(self.drawer.btn_open.winfo_manager()),
            "cancelled": self.drawer.lbl_title.cget("text").startswith("⛔"),
            "failed": self.drawer.lbl_title.cget("text").startswith("❌"),
        }
        return state

    def _restore_layout_state(self, state):
        single_state = state.get("single", {})
        single = self.tabs["single"]
        single.dir_var.set(single_state.get("dir", single.dir_var.get()))
        single.media_seg.select(single_state.get("media", "video"))
        single.video_ext_var.set(single_state.get("video_format", single.video_ext_var.get()))
        single.res_var.set(single_state.get("video_quality", single.res_var.get()))
        single.audio_ext_var.set(single_state.get("audio_format", single.audio_ext_var.get()))
        single.audio_qual_var.set(single_state.get("audio_quality", single.audio_qual_var.get()))
        single.chip_sub.set(single_state.get("subtitles", single.chip_sub.get()))
        single.chip_thumb.set(single_state.get("thumbnail", single.chip_thumb.get()))
        single.chip_turbo.set(single_state.get("turbo", single.chip_turbo.get()))
        single.chip_sb.set(single_state.get("sponsorblock", single.chip_sb.get()))
        if single_state.get("clip_start"):
            single.clip_start_entry.set_text(single_state["clip_start"])
        if single_state.get("clip_end"):
            single.clip_end_entry.set_text(single_state["clip_end"])
        if single_state.get("adv_open") and not single._adv_open:
            single._toggle_advanced()
        if single_state.get("url"):
            single._metadata_url = single_state["url"]
            single.url_entry.set_text(single_state["url"])
        single.current_metadata = None

        playlist_state = state.get("playlist", {})
        playlist = self.tabs["playlist"]
        playlist.dir_var.set(playlist_state.get("dir", playlist.dir_var.get()))
        playlist.media_seg.select(playlist_state.get("media", "video"))
        playlist.video_ext_var.set(playlist_state.get("video_format", playlist.video_ext_var.get()))
        playlist.res_var.set(playlist_state.get("video_quality", playlist.res_var.get()))
        playlist.audio_ext_var.set(playlist_state.get("audio_format", playlist.audio_ext_var.get()))
        playlist.audio_qual_var.set(playlist_state.get("audio_quality", playlist.audio_qual_var.get()))
        if playlist_state.get("start"):
            playlist.start_entry.set_text(playlist_state["start"])
        if playlist_state.get("end"):
            playlist.end_entry.set_text(playlist_state["end"])
        playlist.chip_ignore.set(playlist_state.get("ignore_errors", True))
        playlist.chip_turbo.set(playlist_state.get("turbo", True))
        playlist.chip_archive.set(playlist_state.get("archive", playlist.chip_archive.get()))
        playlist.chip_sb.set(playlist_state.get("sponsorblock", playlist.chip_sb.get()))
        if playlist_state.get("url"):
            playlist.url_entry.set_text(playlist_state["url"])

        batch_state = state.get("batch", {})
        batch = self.tabs["batch"]
        batch.dir_var.set(batch_state.get("dir", batch.dir_var.get()))
        batch.media_seg.select(batch_state.get("media", "video"))
        batch.text_input.insert("1.0", batch_state.get("input", ""))
        batch.queue = [dict(item) for item in batch_state.get("queue", [])]
        for item in batch.queue:
            batch.tree.insert(
                "", "end", iid=str(item["idx"]),
                values=(item["idx"], item["url"], item["status"])
            )
        batch.lbl_queue_count.config(text=f"Kuyruk · {len(batch.queue)} öğe")

        self.switch_tab(state.get("active_tab", "single"))
        if single_state.get("metadata") and single_state.get("url"):
            single._metadata_url = single_state["url"]
            single.current_metadata = single_state["metadata"]
            single.preview_card.update_metadata(
                single_state["metadata"],
                on_playlist_switch=lambda u=single_state["url"]: self._transfer_to_playlist(u)
            )
            single.preview_card.pack(
                fill="x", pady=(0, 16), before=single.divider
            )
            resolutions = single_state["metadata"].get("resolutions")
            if resolutions:
                single.res_cb.config(values=resolutions)
                single.res_var.set(single_state.get("video_quality", resolutions[0]))

        history_state = state.get("history_search")
        if history_state:
            history_tab = self.tabs["history"]
            history_tab.search_entry.set_text(history_state)
            history_tab.search_query = history_state.lower().strip()
            history_tab.refresh()

        drawer_state = state.get("drawer", {})
        if drawer_state.get("visible"):
            title = drawer_state.get("title", "İndirme")
            if title.startswith("⏳ "):
                title = title[2:]
            self.drawer.show(title)
            self.drawer.pbar["value"] = drawer_state.get("progress", 0)
            self.drawer.pct_var.set(f"{float(drawer_state.get('progress', 0)):.1f}%")
            self.drawer.log_text.config(state="normal")
            self.drawer.log_text.insert("end", drawer_state.get("logs", ""))
            self.drawer.log_text.config(state="disabled")
            if engine.is_running or self._batch_running:
                if drawer_state.get("console_open"):
                    self.drawer._toggle_console()
            elif drawer_state.get("completed"):
                self.drawer.on_complete_status(True, self.current_download_file)
            elif drawer_state.get("cancelled"):
                self.drawer.on_complete_status(False, cancelled=True)
            elif drawer_state.get("failed"):
                self.drawer.on_complete_status(False, error_msg=title)

    def _toggle_theme(self):
        state = self._capture_layout_state()
        next_theme = "light" if config.get("theme", "dark") == "dark" else "dark"
        config.set("theme", next_theme)
        apply_theme(self, next_theme)
        for child in self.winfo_children():
            child.destroy()
        self._build_layout()
        self.btn_theme.config(text="☀" if next_theme == "dark" else "🌙")
        self._restore_layout_state(state)
        self._update_system_status()

    def switch_tab(self, key):
        self.active_tab_name = key
        for k, btn in self.nav_buttons.items():
            btn.set_active(k == key)

        for k, frame in self.tabs.items():
            if k == key:
                frame.pack(fill="both", expand=True)
                if hasattr(frame, "refresh"):
                    frame.refresh()
            else:
                frame.pack_forget()

    def _update_system_status(self):
        def _worker():
            yt_ok, _, _ = get_ytdlp_status()
            ff_ok, _, _ = get_ffmpeg_status()
            js_ok, _, _ = get_js_status()

            def _apply():
                if not self.lbl_sys_status.winfo_exists():
                    return
                if yt_ok and ff_ok and js_ok:
                    self.lbl_sys_status.config(text="● Sistem Hazır", fg=SUCCESS)
                elif yt_ok and ff_ok:
                    self.lbl_sys_status.config(text="● Hazır", fg=SUCCESS)
                elif yt_ok and not ff_ok:
                    self.lbl_sys_status.config(text="● FFmpeg Eksik", fg=WARNING)
                else:
                    self.lbl_sys_status.config(text="● yt-dlp Eksik", fg=ERROR)

            try:
                self.after(0, _apply)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _on_deps_updated(self):
        self._update_system_status()
        self.drawer.log_line("✅ Bağımlılıklar güncellendi ve hazır.", "success")

    # ── İndirme İşlemleri ───────────────────────────────────────────
    def start_single_download(self, url, out_dir, options):
        if engine.is_running:
            messagebox.showinfo("Bilgi", "Zaten devam eden bir indirme işlemi var.", parent=self)
            return

        cookies_args = self._get_download_cookies_args()
        if cookies_args is None:
            return

        if not self._ensure_output_dir(out_dir):
            return

        options["cookies_args"] = cookies_args
        options["proxy"] = config.get("proxy")

        try:
            cmd = build_command(url, out_dir, options)
        except ValueError as e:
            messagebox.showwarning("İndirme Ayarları", str(e), parent=self)
            return
        title = options.get("title") or url
        fmt_desc = f"{options['format']} ({options['quality']})"

        self.drawer.show(title=title)
        self.drawer.log_line(f"▶ Başlatıldı: {url}", "accent")

        self._start_engine(cmd, title=title, url=url, fmt_desc=fmt_desc)

    def start_playlist_download(self, url, out_dir, options):
        if engine.is_running:
            messagebox.showinfo("Bilgi", "Zaten devam eden bir indirme işlemi var.", parent=self)
            return

        cookies_args = self._get_download_cookies_args()
        if cookies_args is None:
            return

        if not self._ensure_output_dir(out_dir):
            return

        options["cookies_args"] = cookies_args
        options["proxy"] = config.get("proxy")

        try:
            cmd = build_command(url, out_dir, options)
        except ValueError as e:
            messagebox.showwarning("İndirme Ayarları", str(e), parent=self)
            return

        self.drawer.show(title="Playlist İndiriliyor...")
        self.drawer.log_line(f"▶ Playlist Başlatıldı: {url}", "accent")

        self._start_engine(cmd, title="Playlist", url=url, fmt_desc=f"{options['format']} ({options['quality']})")

    def _get_download_cookies_args(self):
        try:
            return self.tabs["settings"].get_cookies_args()
        except (OSError, ValueError) as e:
            messagebox.showerror("Çerez Ayarı Hatası", str(e), parent=self)
            return None

    def _ensure_output_dir(self, out_dir):
        try:
            os.makedirs(out_dir, exist_ok=True)
            if not os.path.isdir(out_dir):
                raise NotADirectoryError(f"Seçilen kayıt yolu bir klasör değil: {out_dir}")
            return True
        except OSError as e:
            messagebox.showerror("Hata", f"Hedef klasör kullanılamıyor:\n{e}", parent=self)
            return False

    def start_batch_download(self, items, out_dir, options, status_cb):
        if engine.is_running or self._batch_running:
            messagebox.showinfo("Bilgi", "Zaten devam eden bir indirme var.", parent=self)
            return

        cookies_args = self._get_download_cookies_args()
        if cookies_args is None:
            return

        if not self._ensure_output_dir(out_dir):
            return

        options = dict(options)
        options["cookies_args"] = cookies_args
        options["proxy"] = config.get("proxy")
        options["speed_limit"] = config.get("speed_limit")
        options["ignore_errors"] = config.get("ignore_errors", True)
        options["add_metadata"] = config.get("add_metadata", True)
        options["embed_subtitles"] = config.get("embed_subtitles", False)
        options["subtitle_lang"] = config.get("subtitle_lang", "tr,en")
        options["concurrent_fragments"] = config.get("concurrent_fragments", 4)
        options["use_download_archive"] = config.get("use_download_archive", False)
        options["sponsorblock_remove"] = config.get("sponsorblock_remove", False)
        options["sponsorblock_cats"] = config.get("sponsorblock_cats", "sponsor,intro,outro,selfpromo,interaction")

        normalized_items = [
            item if isinstance(item, dict) else {"idx": idx, "url": item}
            for idx, item in enumerate(items, 1)
        ]

        self._batch_running = True
        self.drawer.show(title=f"Toplu İndirme (0/{len(normalized_items)})")

        def _batch_worker():
            successes = 0
            failures = 0
            cancelled = False
            last_processed_pos = 0
            for pos, q_item in enumerate(normalized_items, 1):
                if not self._batch_running:
                    cancelled = True
                    break

                last_processed_pos = pos
                item_idx = q_item["idx"]
                u = q_item["url"]
                self.after(0, lambda i=item_idx: status_cb(i, "⏳ İndiriliyor..."))
                self.after(0, lambda p=pos: self.drawer.lbl_title.config(text=f"Toplu İndirme [{p}/{len(normalized_items)}]"))

                single_opts = dict(options)
                event = threading.Event()
                batch_success = False
                batch_dest = None
                batch_cancelled = False
                batch_error = None

                def _on_done(success, output_path, err, cancelled):
                    nonlocal batch_success, batch_dest, batch_cancelled, batch_error
                    batch_success = success
                    batch_dest = output_path
                    batch_cancelled = cancelled
                    batch_error = err
                    event.set()

                try:
                    cmd = build_command(u, out_dir, single_opts)
                except ValueError as e:
                    failures += 1
                    self.after(0, lambda i=item_idx: status_cb(i, "❌ Hatalı ayar"))
                    self.after(0, lambda error=str(e): self.drawer.log_line(error, "error"))
                    continue

                def _start_item(c=cmd):
                    if not self._batch_running:
                        _on_done(False, None, None, True)
                        return
                    if not self._start_engine_raw(c, done_callback=_on_done):
                        _on_done(False, None, "İndirme motoru başka bir işlemle meşgul.", False)

                self.after(0, _start_item)
                event.wait()

                if batch_success:
                    successes += 1
                    self.current_download_file = batch_dest
                    self.after(0, lambda i=item_idx: status_cb(i, "✅ Tamamlandı"))
                    history.add(os.path.basename(batch_dest or u), u, batch_dest, single_opts["format"])
                    if "history" in self.tabs:
                        self.after(0, self.tabs["history"].refresh)
                elif batch_cancelled:
                    cancelled = True
                    self.after(0, lambda i=item_idx: status_cb(i, "⛔ İptal edildi"))
                    break
                else:
                    failures += 1
                    self.after(0, lambda i=item_idx: status_cb(i, "❌ Hata"))
                    if batch_error:
                        self.after(0, lambda error=batch_error: self.drawer.log_line(error, "error"))

            if cancelled:
                for rem in normalized_items[last_processed_pos:]:
                    self.after(0, lambda i=rem["idx"]: status_cb(i, "⏭ Atlandı"))
            self._batch_running = False
            overall_success = successes == len(normalized_items) and not cancelled
            self.after(
                0,
                lambda: self.drawer.on_complete_status(
                    overall_success,
                    output_path=self.current_download_file,
                    error_msg=f"{successes} başarılı, {failures} hatalı." if failures else None,
                    cancelled=cancelled
                )
            )

        threading.Thread(target=_batch_worker, daemon=True).start()

    def _start_engine(self, cmd, title, url, fmt_desc):
        def _on_progress(pct, speed, total, eta):
            self.after(0, lambda: self.drawer.update_stats(pct, speed, total, eta))

        def _on_log(line, tag):
            self.after(0, lambda: self.drawer.log_line(line, tag))

        def _on_status(msg):
            self.after(0, lambda: self.drawer.set_phase(msg))

        def _on_complete(success, output_path, err, cancelled):
            self.current_download_file = output_path
            self.after(0, lambda: self.drawer.on_complete_status(success, output_path, err, cancelled))
            if success:
                history.add(title, url, output_path, fmt_desc, status="completed")
                if "history" in self.tabs:
                    self.after(0, self.tabs["history"].refresh)

        callbacks = {
            "on_progress": _on_progress,
            "on_log": _on_log,
            "on_status": _on_status,
            "on_complete": _on_complete
        }
        engine.start_download(cmd, callbacks)

    def _start_engine_raw(self, cmd, done_callback):
        def _on_progress(pct, speed, total, eta):
            self.after(0, lambda: self.drawer.update_stats(pct, speed, total, eta))

        def _on_log(line, tag):
            self.after(0, lambda: self.drawer.log_line(line, tag))

        def _on_status(msg):
            self.after(0, lambda: self.drawer.set_phase(msg))

        def _on_complete(success, output_path, err, cancelled):
            if done_callback:
                done_callback(success, output_path, err, cancelled)

        callbacks = {
            "on_progress": _on_progress,
            "on_log": _on_log,
            "on_status": _on_status,
            "on_complete": _on_complete
        }
        return engine.start_download(cmd, callbacks)

    def _on_cancel_download(self):
        if engine.is_running:
            self.drawer.log_line("⛔ İptal ediliyor...", "warn")
            engine.cancel()
        self._batch_running = False

    def _open_downloaded_file(self):
        if self.current_download_file:
            history.show_in_folder(self.current_download_file)

    def _on_close(self):
        if engine.is_running or self._batch_running:
            if messagebox.askokcancel("Çıkış", "Devam eden bir indirme işlemi var. İptal edip çıkmak istiyor musunuz?", parent=self):
                engine.cancel()
                self._batch_running = False
                self.destroy()
        else:
            self.destroy()

def main():
    app = LDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()

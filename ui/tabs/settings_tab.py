import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER, ACCENT, ACCENT_LIGHT, TEXT, SUBTEXT, SUCCESS, WARNING, ERROR,
    FONT_HERO, FONT_TITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD
)
from ui.components import Card, PillButton, PillChip, ModernEntry, SegmentedPill, ScrollableFrame
from core.config import config, get_data_dir
from core.dependencies import (
    get_ytdlp_status, get_ffmpeg_status, get_js_status,
    install_ytdlp, install_ffmpeg, install_deno,
    resolve_cookies_args, test_browser_cookies
)


class SettingsTab(tk.Frame):
    def __init__(self, parent, on_dependency_updated=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.on_dependency_updated = on_dependency_updated
        self._build_ui()
        self.check_dependencies()

    def _build_ui(self):
        self.scroll_container = ScrollableFrame(self)
        self.scroll_container.pack(fill="both", expand=True)
        scroll_frame = self.scroll_container.inner

        # ── 1. Sistem Araçları Kartı ─────────────────────────────────
        c_deps = Card(scroll_frame, padx=24, pady=16)
        c_deps.pack(fill="x", padx=32, pady=(24, 12))

        deps_top = tk.Frame(c_deps, bg=SURFACE)
        deps_top.pack(fill="x", pady=(0, 10))
        tk.Label(deps_top, text="Sistem Araçları", bg=SURFACE, fg=TEXT, font=FONT_BOLD).pack(side="left")
        PillButton(deps_top, text="↻ Kontrol Et", command=self.check_dependencies, small=True, style="ghost").pack(side="right")

        # yt-dlp
        r_yt = tk.Frame(c_deps, bg=SURFACE)
        r_yt.pack(fill="x", pady=4)
        tk.Label(r_yt, text="yt-dlp Çekirdeği:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR, width=18, anchor="w").pack(side="left")
        self.lbl_ytdlp_status = tk.Label(r_yt, text="Kontrol ediliyor...", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR)
        self.lbl_ytdlp_status.pack(side="left")
        self.btn_install_ytdlp = PillButton(r_yt, text="Güncelle", command=self._start_install_ytdlp, small=True, style="secondary")
        self.btn_install_ytdlp.pack(side="right")

        # FFmpeg
        r_ff = tk.Frame(c_deps, bg=SURFACE)
        r_ff.pack(fill="x", pady=4)
        tk.Label(r_ff, text="FFmpeg (1080p+/MP3):", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR, width=18, anchor="w").pack(side="left")
        self.lbl_ffmpeg_status = tk.Label(r_ff, text="Kontrol ediliyor...", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR)
        self.lbl_ffmpeg_status.pack(side="left")
        self.btn_install_ffmpeg = PillButton(r_ff, text="Kur", command=self._start_install_ffmpeg, small=True, style="primary")
        self.btn_install_ffmpeg.pack(side="right")

        # Deno JS
        r_js = tk.Frame(c_deps, bg=SURFACE)
        r_js.pack(fill="x", pady=4)
        tk.Label(r_js, text="JS Motoru (Deno):", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR, width=18, anchor="w").pack(side="left")
        self.lbl_js_status = tk.Label(r_js, text="Kontrol ediliyor...", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR)
        self.lbl_js_status.pack(side="left")
        self.btn_install_js = PillButton(r_js, text="Kur", command=self._start_install_deno, small=True, style="secondary")
        self.btn_install_js.pack(side="right")

        self.lbl_install_progress = tk.Label(c_deps, text="", bg=SURFACE, fg=ACCENT_LIGHT, font=FONT_SMALL)
        self.lbl_install_progress.pack(fill="x", pady=(4, 0))

        # ── 2. Çerez Kartı ──────────────────────────────────────────
        c_ck = Card(scroll_frame, padx=24, pady=16)
        c_ck.pack(fill="x", padx=32, pady=(0, 12))

        ck_row = tk.Frame(c_ck, bg=SURFACE)
        ck_row.pack(fill="x")

        tk.Label(ck_row, text="Oturum Çerezleri", bg=SURFACE, fg=TEXT, font=FONT_BOLD).pack(side="left")
        tk.Label(ck_row, text="(Yaş kısıtlı / özel videolar için)", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL).pack(side="left", padx=(8, 0))

        self.ck_seg = SegmentedPill(
            ck_row,
            items=[
                ("none", "Kapalı"),
                ("browser", "Tarayıcı"),
                ("file", "cookies.txt")
            ],
            default_val=config.get("cookies_mode", "none"),
            on_change=self._on_ck_mode_changed
        )
        self.ck_seg.pack(side="right")

        # Çerez Güvenlik ve Süre Uyarısı
        ck_notice = tk.Frame(c_ck, bg=ACCENT_MUTED, highlightthickness=1, highlightbackground=BORDER, padx=12, pady=10)
        ck_notice.pack(fill="x", pady=(12, 4))

        notice_header = tk.Frame(ck_notice, bg=ACCENT_MUTED)
        notice_header.pack(fill="x")
        tk.Label(notice_header, text="⚠️", bg=ACCENT_MUTED, font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        tk.Label(
            notice_header,
            text="Önemli Çerez & Güvenlik Koruması Bildirimi",
            bg=ACCENT_MUTED, fg=ACCENT_LIGHT, font=FONT_SMALL_BOLD
        ).pack(side="left")

        tk.Label(
            ck_notice,
            text="• YouTube oturum çerezleri güvenlik sebebiyle en fazla 30 dakikada bir yenilenmelidir.\n"
                 "• Windows App-Bound koruması sebebiyle Chromium tabanlı tarayıcılardan (Chrome, Edge, Brave, Opera vb.) otomatik çerez çekimi geçici olarak desteklenmemektedir.\n"
                 "• Çerezle indirme için Firefox, Zen Browser profillerini kullanabilir veya tarayıcınızdan 'Get cookies.txt locally' eklentisiyle aldığınız cookies.txt dosyasını yükleyebilirsiniz.",
            bg=ACCENT_MUTED, fg=TEXT, font=FONT_SMALL, justify="left", anchor="w"
        ).pack(fill="x", pady=(4, 0))

        # Tarayıcı alanı
        self.browser_frame = tk.Frame(c_ck, bg=SURFACE)
        b_sel_row = tk.Frame(self.browser_frame, bg=SURFACE)
        b_sel_row.pack(fill="x", pady=(12, 4))

        tk.Label(b_sel_row, text="Tarayıcı:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.browser_var = tk.StringVar(value=config.get("cookies_browser", "chrome"))
        browsers = ["zen", "firefox", "brave", "chrome", "edge", "opera", "vivaldi", "chromium"]
        self.browser_cb = ttk.Combobox(
            b_sel_row, textvariable=self.browser_var, values=browsers,
            state="readonly", width=12, font=FONT_REGULAR
        )
        self.browser_cb.pack(side="left", padx=(8, 12))
        self.browser_cb.bind("<<ComboboxSelected>>", lambda e: config.set("cookies_browser", self.browser_var.get()))

        self.btn_test_cookies = PillButton(b_sel_row, text="Test Et", command=self._test_cookies_click, small=True, style="secondary")
        self.btn_test_cookies.pack(side="left")

        self.lbl_cookie_test = tk.Label(
            self.browser_frame,
            text="Firefox, Zen veya cookies.txt en kararlı yöntemdir.",
            bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL, anchor="w", wraplength=680, justify="left"
        )
        self.lbl_cookie_test.pack(fill="x", pady=(4, 0))

        # Dosya alanı
        self.file_frame = tk.Frame(c_ck, bg=SURFACE)
        self.ck_file_var = tk.StringVar(value=config.get("cookies_path") or "Seçilmedi")
        self.lbl_ck_file = tk.Label(
            self.file_frame, textvariable=self.ck_file_var, bg=ENTRY_BG, fg=SUBTEXT,
            font=FONT_REGULAR, anchor="w", padx=10, pady=6, highlightthickness=1, highlightbackground=BORDER
        )
        self.lbl_ck_file.pack(side="left", fill="x", expand=True)
        PillButton(self.file_frame, text="📂 Seç", command=self._choose_ck_file, small=True).pack(side="left", padx=(8, 0))
        PillButton(self.file_frame, text="✕", command=self._clear_ck_file, small=True, style="ghost").pack(side="left", padx=(4, 0))

        current_mode = config.get("cookies_mode", "none")
        if current_mode == "browser":
            self.browser_frame.pack(fill="x")
        elif current_mode == "file":
            self.file_frame.pack(fill="x", pady=(12, 0))

        # ── 3. İndirme, SponsorBlock ve Ağ Tercihleri ────────────────
        c_prefs = Card(scroll_frame, padx=24, pady=16)
        c_prefs.pack(fill="x", padx=32, pady=(0, 20))

        tk.Label(c_prefs, text="Tercihler ve Ağ Ayarları", bg=SURFACE, fg=TEXT, font=FONT_BOLD).pack(anchor="w", pady=(0, 12))

        prow1 = tk.Frame(c_prefs, bg=SURFACE)
        prow1.pack(fill="x", pady=(0, 14))

        self.chip_auto_meta = PillChip(
            prow1, text="Otomatik önizleme",
            initial_value=config.get("auto_fetch_metadata", True),
            on_toggle=lambda v: config.set("auto_fetch_metadata", v)
        )
        self.chip_auto_meta.pack(side="left", padx=(0, 8))

        self.chip_add_meta = PillChip(
            prow1, text="Medya etiketleri (Metadata)",
            initial_value=config.get("add_metadata", True),
            on_toggle=lambda v: config.set("add_metadata", v)
        )
        self.chip_add_meta.pack(side="left", padx=(0, 8))

        self.chip_archive = PillChip(
            prow1, text="İndirme Arşivi",
            initial_value=config.get("use_download_archive", False),
            on_toggle=lambda v: config.set("use_download_archive", v)
        )
        self.chip_archive.pack(side="left", padx=(0, 8))

        self.chip_sb = PillChip(
            prow1, text="SponsorBlock",
            initial_value=config.get("sponsorblock_remove", False),
            on_toggle=lambda v: config.set("sponsorblock_remove", v)
        )
        self.chip_sb.pack(side="left", padx=(0, 8))

        PillButton(prow1, text="Arşivi Sıfırla", command=self._clear_archive_file, small=True, style="ghost").pack(side="right")

        # Altyazı & SponsorBlock Kategorileri Satırı
        prow2 = tk.Frame(c_prefs, bg=SURFACE)
        prow2.pack(fill="x", pady=(0, 12))

        tk.Label(prow2, text="Altyazı Dili:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.sub_lang_var = tk.StringVar(value=config.get("subtitle_lang", "tr,en"))
        self.sub_lang_entry = ModernEntry(
            prow2, textvariable=self.sub_lang_var, placeholder="tr,en", width=12,
            on_change=lambda val: config.set("subtitle_lang", val or "tr,en")
        )
        self.sub_lang_entry.pack(side="left", padx=(8, 24), ipady=3)

        tk.Label(prow2, text="SponsorBlock:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.sb_cats_var = tk.StringVar(value=config.get("sponsorblock_cats", "sponsor,intro,outro,selfpromo,interaction"))
        self.sb_cats_entry = ModernEntry(
            prow2, textvariable=self.sb_cats_var, placeholder="sponsor,intro,outro", width=28,
            on_change=lambda val: config.set("sponsorblock_cats", val or "sponsor,intro,outro")
        )
        self.sb_cats_entry.pack(side="left", padx=(8, 0), fill="x", expand=True, ipady=3)

        # Ağ ve Performans Satırı
        nrow = tk.Frame(c_prefs, bg=SURFACE)
        nrow.pack(fill="x")

        tk.Label(nrow, text="Parça Sayısı:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.frag_var = tk.StringVar(value=str(config.get("concurrent_fragments", 4)))
        self.frag_cb = ttk.Combobox(
            nrow, textvariable=self.frag_var, values=["1", "2", "4", "8", "16"],
            state="readonly", width=5, font=FONT_REGULAR
        )
        self.frag_cb.pack(side="left", padx=(8, 24))
        self.frag_cb.bind("<<ComboboxSelected>>", lambda e: config.set("concurrent_fragments", int(self.frag_var.get())))

        tk.Label(nrow, text="Hız Sınırı:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.speed_var = tk.StringVar(value=config.get("speed_limit", ""))
        self.speed_entry = ModernEntry(
            nrow, textvariable=self.speed_var, placeholder="Örn: 5M", width=10,
            on_change=lambda val: config.set("speed_limit", val)
        )
        self.speed_entry.pack(side="left", padx=(8, 24), ipady=3)

        tk.Label(nrow, text="Proxy:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.proxy_var = tk.StringVar(value=config.get("proxy", ""))
        self.proxy_entry = ModernEntry(
            nrow, textvariable=self.proxy_var, placeholder="http://127.0.0.1:7890", width=18,
            on_change=lambda val: config.set("proxy", val)
        )
        self.proxy_entry.pack(side="left", padx=(8, 8), fill="x", expand=True, ipady=3)
        PillButton(nrow, text="✓ Kaydet", command=self._save_net_settings, small=True, style="secondary").pack(side="left")

        self.lbl_net_saved = tk.Label(c_prefs, text="", bg=SURFACE, fg=SUCCESS, font=FONT_SMALL)
        self.lbl_net_saved.pack(anchor="w", pady=(4, 0))

    def _save_net_settings(self):
        config.set("speed_limit", self.speed_entry.get_clean_text())
        config.set("proxy", self.proxy_entry.get_clean_text())
        config.set("subtitle_lang", self.sub_lang_entry.get_clean_text() or "tr,en")
        config.set("sponsorblock_cats", self.sb_cats_entry.get_clean_text() or "sponsor,intro,outro")
        self.lbl_net_saved.config(text="✅ Ayarlar kaydedildi.")
        self.after(2500, lambda: self.lbl_net_saved.config(text="") if self.lbl_net_saved.winfo_exists() else None)

    def _clear_archive_file(self):
        archive_path = os.path.join(get_data_dir(), "archive.txt")
        if os.path.exists(archive_path):
            if messagebox.askyesno("Onay", "İndirme arşivi (archive.txt) sıfırlansın mı?", parent=self):
                try:
                    os.remove(archive_path)
                    messagebox.showinfo("Bilgi", "İndirme arşivi temizlendi.", parent=self)
                except OSError as e:
                    messagebox.showerror("Hata", f"Arşiv dosyası silinemedi:\n{e}", parent=self)
        else:
            messagebox.showinfo("Bilgi", "Henüz oluşturulmuş bir indirme arşivi bulunmuyor.", parent=self)

    def _on_ck_mode_changed(self, mode):
        config.set("cookies_mode", mode)
        if mode == "browser":
            self.file_frame.pack_forget()
            self.browser_frame.pack(fill="x")
        elif mode == "file":
            self.browser_frame.pack_forget()
            self.file_frame.pack(fill="x", pady=(12, 0))
        else:
            self.browser_frame.pack_forget()
            self.file_frame.pack_forget()

    def _test_cookies_click(self):
        b = self.browser_var.get()
        self.btn_test_cookies.config(state="disabled")
        self.lbl_cookie_test.config(text=f"⏳ {b.capitalize()} çerezleri test ediliyor...", fg=ACCENT_LIGHT)

        def _worker():
            success, msg = test_browser_cookies(b)
            def _apply():
                if not self.btn_test_cookies.winfo_exists():
                    return
                self.btn_test_cookies.config(state="normal")
                self.lbl_cookie_test.config(text=msg, fg=(SUCCESS if success else WARNING))
            try:
                self.after(0, _apply)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _choose_ck_file(self):
        f = filedialog.askopenfilename(
            title="cookies.txt Dosyası Seçin",
            filetypes=[("Metin Dosyası", "*.txt"), ("Tüm Dosyalar", "*.*")]
        )
        if f:
            self.ck_file_var.set(f)
            config.set("cookies_path", f)

    def _clear_ck_file(self):
        self.ck_file_var.set("Seçilmedi")
        config.set("cookies_path", "")

    def check_dependencies(self):
        def _check():
            yt_ok, yt_ver, _ = get_ytdlp_status()
            ff_ok, ff_ver, _ = get_ffmpeg_status()
            js_ok, js_ver, _ = get_js_status()

            def _update():
                if not self.lbl_ytdlp_status.winfo_exists():
                    return
                if yt_ok:
                    self.lbl_ytdlp_status.config(text=f"✅ Hazır ({yt_ver})", fg=SUCCESS)
                else:
                    self.lbl_ytdlp_status.config(text="❌ Bulunamadı", fg=ERROR)

                if ff_ok:
                    self.lbl_ffmpeg_status.config(text=f"✅ Hazır ({ff_ver})", fg=SUCCESS)
                    self.btn_install_ffmpeg.config(text="✓ Kurulu", style="secondary")
                else:
                    self.lbl_ffmpeg_status.config(text="⚠️ Bulunamadı", fg=WARNING)
                    self.btn_install_ffmpeg.config(text="⚡ Kur", style="primary")

                if js_ok:
                    self.lbl_js_status.config(text=f"✅ {js_ver}", fg=SUCCESS)
                    self.btn_install_js.config(text="✓ Hazır", style="secondary")
                else:
                    self.lbl_js_status.config(text="⚠️ Bulunamadı", fg=WARNING)
                    self.btn_install_js.config(text="⚡ Kur", style="primary")

            try:
                self.after(0, _update)
            except Exception:
                pass

        threading.Thread(target=_check, daemon=True).start()

    def _start_install_ytdlp(self):
        self.btn_install_ytdlp.config(state="disabled")
        self.lbl_install_progress.config(text="yt-dlp indiriliyor...", fg=ACCENT_LIGHT)

        def _prog(pct, dl, tot):
            self.after(0, lambda: self.lbl_install_progress.config(text=f"yt-dlp indiriliyor: %{pct:.1f}"))

        def _worker():
            try:
                install_ytdlp(progress_callback=_prog)
                self.after(0, lambda: self.lbl_install_progress.config(text="✅ yt-dlp güncellendi!", fg=SUCCESS))
                self.check_dependencies()
                if self.on_dependency_updated:
                    self.on_dependency_updated()
            except Exception as ex:
                self.after(0, lambda: self.lbl_install_progress.config(text=f"❌ Hata: {ex}", fg=ERROR))
            finally:
                self.after(0, lambda: self.btn_install_ytdlp.config(state="normal"))

        threading.Thread(target=_worker, daemon=True).start()

    def _start_install_ffmpeg(self):
        self.btn_install_ffmpeg.config(state="disabled")
        self.lbl_install_progress.config(text="FFmpeg indiriliyor...", fg=ACCENT_LIGHT)

        def _prog(pct, dl, tot):
            self.after(0, lambda: self.lbl_install_progress.config(text=f"FFmpeg indiriliyor: %{pct:.1f}"))

        def _worker():
            try:
                install_ffmpeg(progress_callback=_prog)
                self.after(0, lambda: self.lbl_install_progress.config(text="✅ FFmpeg kuruldu!", fg=SUCCESS))
                self.check_dependencies()
                if self.on_dependency_updated:
                    self.on_dependency_updated()
            except Exception as ex:
                self.after(0, lambda: self.lbl_install_progress.config(text=f"❌ Kurulum Hatası: {ex}", fg=ERROR))
            finally:
                self.after(0, lambda: self.btn_install_ffmpeg.config(state="normal"))

        threading.Thread(target=_worker, daemon=True).start()

    def _start_install_deno(self):
        self.btn_install_js.config(state="disabled")
        self.lbl_install_progress.config(text="Deno indiriliyor...", fg=ACCENT_LIGHT)

        def _prog(pct, dl, tot):
            self.after(0, lambda: self.lbl_install_progress.config(text=f"Deno indiriliyor: %{pct:.1f}"))

        def _worker():
            try:
                install_deno(progress_callback=_prog)
                self.after(0, lambda: self.lbl_install_progress.config(text="✅ Deno kuruldu!", fg=SUCCESS))
                self.check_dependencies()
                if self.on_dependency_updated:
                    self.on_dependency_updated()
            except Exception as ex:
                self.after(0, lambda: self.lbl_install_progress.config(text=f"❌ Deno Kurulum Hatası: {ex}", fg=ERROR))
            finally:
                self.after(0, lambda: self.btn_install_js.config(state="normal"))

        threading.Thread(target=_worker, daemon=True).start()

    def get_cookies_args(self):
        mode = self.ck_seg.get()
        b = self.browser_var.get()
        p = self.ck_file_var.get()
        return resolve_cookies_args(mode, b, p)

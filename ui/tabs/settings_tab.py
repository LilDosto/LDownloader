import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER, ACCENT, ACCENT_LIGHT, TEXT, SUBTEXT, SUCCESS, WARNING, ERROR,
    FONT_HERO, FONT_TITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD
)
from ui.components import Card, PillButton, PillChip, ModernEntry, SegmentedPill
from core.config import config
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
        # ── Başlık ───────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 22))

        tk.Label(hdr, text="Ayarlar", bg=BG, fg=TEXT, font=FONT_HERO).pack(anchor="w")
        tk.Label(hdr, text="İndirme tercihlerini, bağlantı ve sistem araçlarını yönetin.",
                 bg=BG, fg=SUBTEXT, font=FONT_REGULAR).pack(anchor="w", pady=(6, 0))

        # ── 1. Sistem Araçları Kartı ─────────────────────────────────
        c_deps = Card(self)
        c_deps.pack(fill="x", padx=32, pady=(0, 16))

        tk.Label(c_deps, text="SİSTEM ARAÇLARI", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w", pady=(0, 12))

        # yt-dlp
        r_yt = tk.Frame(c_deps, bg=SURFACE)
        r_yt.pack(fill="x", pady=6)
        tk.Label(r_yt, text="yt-dlp Çekirdeği:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR, width=16, anchor="w").pack(side="left")
        self.lbl_ytdlp_status = tk.Label(r_yt, text="Kontrol ediliyor...", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR)
        self.lbl_ytdlp_status.pack(side="left")

        self.btn_install_ytdlp = PillButton(r_yt, text="Güncelle", command=self._start_install_ytdlp, small=True, style="secondary")
        self.btn_install_ytdlp.pack(side="right")

        # FFmpeg
        r_ff = tk.Frame(c_deps, bg=SURFACE)
        r_ff.pack(fill="x", pady=6)
        tk.Label(r_ff, text="FFmpeg Medya:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR, width=16, anchor="w").pack(side="left")
        self.lbl_ffmpeg_status = tk.Label(r_ff, text="Kontrol ediliyor...", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR)
        self.lbl_ffmpeg_status.pack(side="left")

        self.btn_install_ffmpeg = PillButton(r_ff, text="FFmpeg kur", command=self._start_install_ffmpeg, small=True, style="primary")
        self.btn_install_ffmpeg.pack(side="right")

        # JavaScript EJS (Deno)
        r_js = tk.Frame(c_deps, bg=SURFACE)
        r_js.pack(fill="x", pady=6)
        tk.Label(r_js, text="JS Motoru (EJS):", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR, width=16, anchor="w").pack(side="left")
        self.lbl_js_status = tk.Label(r_js, text="Kontrol ediliyor...", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR)
        self.lbl_js_status.pack(side="left")

        self.btn_install_js = PillButton(r_js, text="Deno kur", command=self._start_install_deno, small=True, style="secondary")
        self.btn_install_js.pack(side="right")

        self.lbl_install_progress = tk.Label(c_deps, text="", bg=SURFACE, fg=ACCENT_LIGHT, font=FONT_SMALL)
        self.lbl_install_progress.pack(fill="x", pady=(6, 0))

        # ── 2. Çerez Kartı ──────────────────────────────────────────
        c_ck = Card(self)
        c_ck.pack(fill="x", padx=32, pady=(0, 16))

        tk.Label(c_ck, text="TARAYICI ÇEREZLERİ", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w")
        tk.Label(c_ck, text="Yalnızca erişim gerektiren içeriklerde kullanın. Çerezler hesabınıza erişim sağlayabilir.",
                 bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(anchor="w", pady=(6, 14))

        ck_row = tk.Frame(c_ck, bg=SURFACE)
        ck_row.pack(fill="x")

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
        self.ck_seg.pack(side="left")

        # Tarayıcı alanı
        self.browser_frame = tk.Frame(c_ck, bg=SURFACE)

        b_sel_row = tk.Frame(self.browser_frame, bg=SURFACE)
        b_sel_row.pack(fill="x", pady=(12, 4))

        tk.Label(b_sel_row, text="Tarayıcı:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.browser_var = tk.StringVar(value=config.get("cookies_browser", "brave"))
        browsers = ["zen", "brave", "chrome", "edge", "firefox", "opera", "vivaldi", "chromium"]
        self.browser_cb = ttk.Combobox(
            b_sel_row, textvariable=self.browser_var, values=browsers,
            state="readonly", width=12, font=FONT_REGULAR
        )
        self.browser_cb.pack(side="left", padx=(8, 14))
        self.browser_cb.bind("<<ComboboxSelected>>", lambda e: config.set("cookies_browser", self.browser_var.get()))

        self.btn_test_cookies = PillButton(b_sel_row, text="Çerezleri test et", command=self._test_cookies_click, small=True, style="secondary")
        self.btn_test_cookies.pack(side="left")

        self.lbl_cookie_test = tk.Label(
            self.browser_frame,
            text="Çoğu içerik için çerez gerekmez. Çerez dosyalarını kimseyle paylaşmayın.",
            bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL, anchor="w", wraplength=540, justify="left"
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

        # Başlangıçta görünürlük
        current_mode = config.get("cookies_mode", "none")
        if current_mode == "browser":
            self.browser_frame.pack(fill="x")
        elif current_mode == "file":
            self.file_frame.pack(fill="x", pady=(12, 0))

        # ── 3. Ağ ve Performans Kartı ────────────────────────────────
        c_net = Card(self)
        c_net.pack(fill="x", padx=32, pady=(0, 24))

        tk.Label(c_net, text="AĞ VE PERFORMANS", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(anchor="w", pady=(0, 12))

        nrow = tk.Frame(c_net, bg=SURFACE)
        nrow.pack(fill="x")

        tk.Label(nrow, text="Eşzamanlı parça sayısı:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.frag_var = tk.StringVar(value=str(config.get("concurrent_fragments", 4)))
        self.frag_cb = ttk.Combobox(
            nrow, textvariable=self.frag_var, values=["1", "2", "4", "8", "16"],
            state="readonly", width=5, font=FONT_REGULAR
        )
        self.frag_cb.pack(side="left", padx=(6, 28))
        self.frag_cb.bind("<<ComboboxSelected>>", lambda e: config.set("concurrent_fragments", int(self.frag_var.get())))

        tk.Label(nrow, text="Proxy:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.proxy_var = tk.StringVar(value=config.get("proxy", ""))
        self.proxy_entry = ModernEntry(nrow, textvariable=self.proxy_var, placeholder="http://127.0.0.1:7890", width=22)
        self.proxy_entry.pack(side="left", padx=(6, 10))
        PillButton(nrow, text="Kaydet", command=lambda: config.set("proxy", self.proxy_entry.get_clean_text()), small=True).pack(side="left")

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
                self.btn_test_cookies.config(state="normal")
                self.lbl_cookie_test.config(text=msg, fg=(SUCCESS if success else WARNING))
            self.after(0, _apply)

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
                if yt_ok:
                    self.lbl_ytdlp_status.config(text=f"✅ Hazır ({yt_ver})", fg=SUCCESS)
                else:
                    self.lbl_ytdlp_status.config(text="❌ Bulunamadı", fg=ERROR)

                if ff_ok:
                    self.lbl_ffmpeg_status.config(text=f"✅ Hazır ({ff_ver})", fg=SUCCESS)
                    self.btn_install_ffmpeg.config(text="✓ Kurulu", style="secondary")
                else:
                    self.lbl_ffmpeg_status.config(text="⚠️ Bulunamadı (MP3 için gerekli)", fg=WARNING)
                    self.btn_install_ffmpeg.config(text="⚡ 1-Tıkla FFmpeg Kur", style="primary")

                if js_ok:
                    self.lbl_js_status.config(text=f"✅ {js_ver}", fg=SUCCESS)
                    self.btn_install_js.config(text="✓ Hazır", style="secondary")
                else:
                    self.lbl_js_status.config(text="⚠️ Bulunamadı (YouTube EJS için)", fg=WARNING)
                    self.btn_install_js.config(text="⚡ Deno Kur", style="primary")

            self.after(0, _update)

        threading.Thread(target=_check, daemon=True).start()

    def _start_install_ytdlp(self):
        self.btn_install_ytdlp.config(state="disabled")
        self.lbl_install_progress.config(text="yt-dlp indiriliyor...", fg=ACCENT_LIGHT)

        def _prog(pct, dl, tot):
            self.after(0, lambda: self.lbl_install_progress.config(text=f"yt-dlp indiriliyor: %{pct:.1f}"))

        def _worker():
            try:
                install_ytdlp(progress_callback=_prog)
                self.after(0, lambda: self.lbl_install_progress.config(text="✅ yt-dlp başarıyla güncellendi!", fg=SUCCESS))
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
        self.lbl_install_progress.config(text="FFmpeg indiriliyor ve ayıklanıyor...", fg=ACCENT_LIGHT)

        def _prog(pct, dl, tot):
            self.after(0, lambda: self.lbl_install_progress.config(text=f"FFmpeg indiriliyor: %{pct:.1f}"))

        def _worker():
            try:
                install_ffmpeg(progress_callback=_prog)
                self.after(0, lambda: self.lbl_install_progress.config(text="✅ FFmpeg başarıyla kuruldu!", fg=SUCCESS))
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
        self.lbl_install_progress.config(text="Deno JavaScript motoru indiriliyor...", fg=ACCENT_LIGHT)

        def _prog(pct, dl, tot):
            self.after(0, lambda: self.lbl_install_progress.config(text=f"Deno indiriliyor: %{pct:.1f}"))

        def _worker():
            try:
                install_deno(progress_callback=_prog)
                self.after(0, lambda: self.lbl_install_progress.config(text="✅ Deno motoru başarıyla kuruldu!", fg=SUCCESS))
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

import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, SURFACE_HOVER, ENTRY_BG, BORDER, BORDER_FOCUS,
    ACCENT, ACCENT_LIGHT, ACCENT_HOVER, ACCENT_MUTED, ACCENT_GRADIENT,
    TAB_BG, TAB_ACTIVE, TAB_HOVER,
    TEXT, SUBTEXT, MUTED,
    SUCCESS, SUCCESS_HOVER, WARNING, ERROR, DANGER_HOVER,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_REGULAR, FONT_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_STAT, FONT_MONO
)


class Card(tk.Frame):
    """Quiet surface container with a thin, low-contrast edge."""
    def __init__(self, parent, padx=22, pady=16, **kwargs):
        super().__init__(
            parent,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            padx=padx,
            pady=pady,
            **kwargs
        )


class CookieNoticeBanner(tk.Frame):
    """
    Üst kısım bilgilendirme banner'ı:
    Oturum çerezlerinin geçerlilik süresi (maksimum 30 dk) ve Chromium güvenlik koruması uyarısını gösterir.
    """
    def __init__(self, parent, on_open_settings=None, dismissible=True, **kwargs):
        super().__init__(
            parent,
            bg=ACCENT_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            padx=14,
            pady=10,
            **kwargs
        )
        self.on_open_settings = on_open_settings

        # Sol: İkon
        lbl_icon = tk.Label(self, text="🍪", bg=ACCENT_MUTED, font=("Segoe UI", 12))
        lbl_icon.pack(side="left", padx=(0, 10))

        # Orta: Metin Alanı
        text_frame = tk.Frame(self, bg=ACCENT_MUTED)
        text_frame.pack(side="left", fill="both", expand=True)

        t_title = tk.Label(
            text_frame,
            text="Önemli Çerez & Oturum Bilgilendirmesi",
            bg=ACCENT_MUTED,
            fg=ACCENT_LIGHT,
            font=FONT_SMALL_BOLD,
            anchor="w"
        )
        t_title.pack(fill="x")

        t_desc = tk.Label(
            text_frame,
            text="YouTube oturum çerezleri en fazla 30 dakikada bir yenilenmelidir. Windows App-Bound güvenlik koruması sebebiyle Chromium tabanlı tarayıcılardan (Chrome, Edge, Brave vb.) otomatik çerez çekimi geçici olarak desteklenmemektedir. Sorunsuz indirme için Firefox, Zen Browser kullanmanız veya Ayarlar'dan 'cookies.txt' dosyasını yüklemeniz önerilir.",
            bg=ACCENT_MUTED,
            fg=SUBTEXT,
            font=FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=640
        )
        t_desc.pack(fill="x", pady=(2, 0))

        # Sağ: Eylem Butonları
        actions = tk.Frame(self, bg=ACCENT_MUTED)
        actions.pack(side="right", padx=(8, 0))

        if on_open_settings:
            btn_sett = PillButton(
                actions,
                text="⚙️ Çerez Ayarları",
                command=on_open_settings,
                small=True,
                style="secondary"
            )
            btn_sett.pack(side="left", padx=(0, 6))

        if dismissible:
            btn_close = PillButton(
                actions,
                text="✕",
                command=self.destroy,
                small=True,
                style="ghost"
            )
            btn_close.pack(side="left")


class PillButton(tk.Frame):
    """Flat, high-contrast button with a clear hover and disabled state."""
    def __init__(self, parent, text="", command=None, style="secondary", small=False, **kwargs):
        self.style_type = style
        self._disabled = False
        self.normal_bg, self.hover_bg, self.normal_fg, self.border_col = self._get_colors(style)

        font = FONT_SMALL_BOLD if small else FONT_BOLD
        padx = 14 if small else (22 if style in ("primary", "accent", "danger") else 16)
        pady = 6 if small else (10 if style in ("primary", "accent", "danger") else 8)

        super().__init__(
            parent,
            bg=self.normal_bg,
            highlightthickness=1,
            highlightbackground=self.border_col,
            **kwargs
        )
        self.command = command

        self.inner = tk.Label(
            self,
            text=text,
            bg=self.normal_bg,
            fg=self.normal_fg,
            font=font,
            padx=padx,
            pady=pady,
            cursor="hand2"
        )
        self.inner.pack(fill="both", expand=True)

        self.inner.bind("<Button-1>", self._on_click)
        self.inner.bind("<Enter>", self._on_enter)
        self.inner.bind("<Leave>", self._on_leave)

    def _get_colors(self, style):
        if style in ("primary", "accent"):
            return ACCENT, ACCENT_HOVER, "#ffffff", ACCENT_GRADIENT
        elif style == "danger":
            return ERROR, DANGER_HOVER, "#ffffff", ERROR
        elif style == "success":
            return SUCCESS, SUCCESS_HOVER, "#ffffff", SUCCESS
        elif style == "ghost":
            return SURFACE, SURFACE_HOVER, SUBTEXT, BORDER
        else:  # secondary
            return SURFACE_LIGHT, SURFACE_HOVER, TEXT, BORDER

    def _on_click(self, event=None):
        if not self._disabled and self.command:
            self.command()

    def _on_enter(self, event=None):
        if not self._disabled:
            self.inner.config(bg=self.hover_bg)
            self.config(bg=self.hover_bg)

    def _on_leave(self, event=None):
        if not self._disabled:
            self.inner.config(bg=self.normal_bg)
            self.config(bg=self.normal_bg)

    def config(self, **kw):
        if "text" in kw:
            self.inner.config(text=kw.pop("text"))
        if "state" in kw:
            state = kw.pop("state")
            self._disabled = (state == "disabled")
            if self._disabled:
                self.inner.config(fg=MUTED, bg=SURFACE_LIGHT, cursor="")
                super().config(bg=SURFACE_LIGHT)
            else:
                self.inner.config(fg=self.normal_fg, bg=self.normal_bg, cursor="hand2")
                super().config(bg=self.normal_bg)
        if "style" in kw:
            self.set_style(kw.pop("style"))
        if "command" in kw:
            self.command = kw.pop("command")
        if kw:
            super().config(**kw)

    def configure(self, **kw):
        self.config(**kw)

    def set_style(self, style):
        self.style_type = style
        self.normal_bg, self.hover_bg, self.normal_fg, self.border_col = self._get_colors(style)
        self.config(bg=self.normal_bg, highlightbackground=self.border_col)
        self.inner.config(bg=self.normal_bg, fg=self.normal_fg)


class PillChip(tk.Frame):
    """Modern tıklanabilir aç/kapa ayar etiketi (çip)."""
    def __init__(self, parent, text, initial_value=False, on_toggle=None, **kwargs):
        super().__init__(parent, bg=SURFACE_LIGHT, padx=12, pady=6, cursor="hand2", **kwargs)
        self.text = text
        self.value = initial_value
        self.on_toggle = on_toggle

        bg_col = ACCENT_MUTED if self.value else SURFACE_LIGHT
        bdr_col = ACCENT if self.value else BORDER

        self.config(
            highlightthickness=1,
            highlightbackground=bdr_col,
            bg=bg_col
        )

        self.label = tk.Label(
            self,
            text=f"{'✓ ' if self.value else ''}{self.text}",
            bg=bg_col,
            fg=(ACCENT_LIGHT if self.value else SUBTEXT),
            font=FONT_SMALL_BOLD,
            cursor="hand2"
        )
        self.label.pack()

        for w in (self, self.label):
            w.bind("<Button-1>", self._toggle)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _toggle(self, event=None):
        self.value = not self.value
        self._update_state()
        if self.on_toggle:
            self.on_toggle(self.value)

    def _update_state(self):
        bg_col = ACCENT_MUTED if self.value else SURFACE_LIGHT
        fg_col = ACCENT_LIGHT if self.value else SUBTEXT
        bdr_col = ACCENT if self.value else BORDER
        prefix = "✓ " if self.value else ""

        self.config(bg=bg_col, highlightbackground=bdr_col)
        self.label.config(bg=bg_col, fg=fg_col, text=f"{prefix}{self.text}")

    def _on_enter(self, event=None):
        if not self.value:
            self.config(bg=SURFACE_HOVER, highlightbackground=BORDER_FOCUS)
            self.label.config(bg=SURFACE_HOVER, fg=TEXT)

    def _on_leave(self, event=None):
        if not self.value:
            self.config(bg=SURFACE_LIGHT, highlightbackground=BORDER)
            self.label.config(bg=SURFACE_LIGHT, fg=SUBTEXT)

    def get(self):
        return self.value

    def set(self, val):
        self.value = bool(val)
        self._update_state()


class ModernEntry(tk.Entry):
    """Zarif gömülü derinlik ve odaklanma çerçevesine sahip girdi alanı."""
    def __init__(self, parent, textvariable=None, placeholder=None, on_change=None, **kwargs):
        self.placeholder = placeholder
        self.has_placeholder = False
        self.on_change = on_change

        kwargs.setdefault("bg", ENTRY_BG)
        kwargs.setdefault("fg", TEXT)
        kwargs.setdefault("insertbackground", ACCENT_LIGHT)
        kwargs.setdefault("selectbackground", ACCENT)
        kwargs.setdefault("selectforeground", "#ffffff")
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("bd", 0)
        kwargs.setdefault("font", FONT_REGULAR)
        kwargs.setdefault("highlightthickness", 1)
        kwargs.setdefault("highlightbackground", BORDER)
        kwargs.setdefault("highlightcolor", BORDER_FOCUS)

        super().__init__(parent, textvariable=textvariable, **kwargs)

        if placeholder:
            self._apply_placeholder()
            self.bind("<FocusIn>", self._on_focus_in)
            self.bind("<FocusOut>", self._on_focus_out)

        if on_change:
            self.bind("<KeyRelease>", lambda e: on_change(self.get_clean_text()))

    def _apply_placeholder(self):
        val = self.get()
        if not val or val == self.placeholder:
            self.delete(0, "end")
            self.insert(0, self.placeholder)
            self.config(fg=MUTED)
            self.has_placeholder = True

    def _on_focus_in(self, event):
        if self.has_placeholder:
            self.delete(0, "end")
            self.config(fg=TEXT)
            self.has_placeholder = False

    def _on_focus_out(self, event):
        if not self.get().strip():
            self._apply_placeholder()

    def get_clean_text(self):
        val = self.get().strip()
        if self.has_placeholder or val == self.placeholder:
            return ""
        return val

    def set_text(self, text):
        self.delete(0, "end")
        if text:
            self.insert(0, text)
            self.config(fg=TEXT)
            self.has_placeholder = False
        elif self.placeholder:
            self._apply_placeholder()
        if self.on_change:
            self.on_change(text or "")


class ScrollableFrame(tk.Frame):
    """Dikey kaydırma (fare tekerleği destekli) sağlayan akıcı ve optimize modern kapsayıcı çerçeve."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
        self.inner = tk.Frame(self.canvas, bg=BG)

        self._win_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self._on_scroll)

        self.canvas.pack(side="left", fill="both", expand=True)

        self._configure_after_id = None
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _on_scroll(self, first, last):
        if float(first) <= 0.0 and float(last) >= 1.0:
            if self.scrollbar.winfo_ismapped():
                self.scrollbar.pack_forget()
        else:
            if not self.scrollbar.winfo_ismapped():
                self.scrollbar.pack(side="right", fill="y")
        self.scrollbar.set(first, last)

    def _on_inner_configure(self, event=None):
        if self._configure_after_id:
            self.after_cancel(self._configure_after_id)
        self._configure_after_id = self.after(20, self._update_scroll_region)

    def _update_scroll_region(self):
        self._configure_after_id = None
        if self.canvas.winfo_exists():
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        if self.canvas.winfo_exists():
            self.canvas.itemconfig(self._win_id, width=event.width)

    def _bind_wheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _unbind_wheel(self, event=None):
        pass

    def _on_mousewheel(self, event):
        if not self.canvas.winfo_exists() or not self.winfo_ismapped():
            return
        try:
            x, y = self.winfo_pointerxy()
            wx = self.winfo_rootx()
            wy = self.winfo_rooty()
            ww = self.winfo_width()
            wh = self.winfo_height()
            if not (wx <= x <= wx + ww and wy <= y <= wy + wh):
                return
            first, last = self.canvas.yview()
            if float(first) <= 0.0 and float(last) >= 1.0:
                return
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass


class TabButton(tk.Frame):
    """Rounded-feel navigation item using a soft active-state surface."""
    def __init__(self, parent, icon, text, command=None, is_active=False):
        super().__init__(parent, bg=TAB_BG, cursor="hand2")
        self.command = command
        self.is_active = is_active

        active_bg = TAB_ACTIVE if is_active else TAB_BG
        active_fg = ACCENT_LIGHT if is_active else SUBTEXT

        self.content = tk.Frame(self, bg=active_bg, padx=15, pady=10)
        self.content.pack(fill="both", expand=True)

        self.lbl_icon = tk.Label(
            self.content, text=icon, font=("Segoe UI", 11),
            bg=active_bg, fg=active_fg
        )
        self.lbl_icon.pack(side="left", padx=(0, 6))

        self.lbl_text = tk.Label(
            self.content, text=text,
            font=FONT_BOLD if is_active else FONT_REGULAR,
            bg=active_bg,
            fg=(TEXT if is_active else SUBTEXT)
        )
        self.lbl_text.pack(side="left")

        self.indicator = tk.Frame(self, bg=(ACCENT if is_active else TAB_BG), height=2)
        self.indicator.pack(fill="x", side="bottom")

        for w in (self, self.content, self.lbl_icon, self.lbl_text):
            w.bind("<Button-1>", lambda e: self._click())
            w.bind("<Enter>", lambda e: self._enter())
            w.bind("<Leave>", lambda e: self._leave())

    def _click(self):
        if self.command:
            self.command()

    def set_active(self, active):
        self.is_active = active
        bg_col = TAB_ACTIVE if active else TAB_BG
        fg_col = TEXT if active else SUBTEXT
        icon_col = ACCENT_LIGHT if active else SUBTEXT
        ind_col = ACCENT if active else TAB_BG
        font = FONT_BOLD if active else FONT_REGULAR

        self.config(bg=TAB_BG)
        self.content.config(bg=bg_col)
        self.lbl_icon.config(bg=bg_col, fg=icon_col)
        self.lbl_text.config(bg=bg_col, fg=fg_col, font=font)
        self.indicator.config(bg=ind_col)

    def _enter(self):
        if not self.is_active:
            self.content.config(bg=TAB_HOVER)
            self.lbl_icon.config(bg=TAB_HOVER, fg=ACCENT_LIGHT)
            self.lbl_text.config(bg=TAB_HOVER, fg=TEXT)

    def _leave(self):
        if not self.is_active:
            self.content.config(bg=TAB_BG)
            self.lbl_icon.config(bg=TAB_BG, fg=SUBTEXT)
            self.lbl_text.config(bg=TAB_BG, fg=SUBTEXT)


class SegmentedPill(tk.Frame):
    """Modern segmented buton denetleyicisi."""
    def __init__(self, parent, items, default_val=None, on_change=None, **kwargs):
        super().__init__(
            parent,
            bg=SURFACE_LIGHT,
            padx=3,
            pady=3,
            highlightthickness=0,
            **kwargs
        )
        self.items = items
        self.on_change = on_change
        self.selected_key = default_val if default_val else items[0][0]
        self.buttons = {}

        for key, label in self.items:
            btn = tk.Label(
                self,
                text=label,
                font=FONT_SMALL_BOLD,
                padx=14,
                pady=7,
                cursor="hand2"
            )
            btn.pack(side="left", padx=1)
            btn.bind("<Button-1>", lambda e, k=key: self.select(k))
            btn.bind("<Enter>", lambda e, k=key: self._hover_on(k))
            btn.bind("<Leave>", lambda e, k=key: self._hover_off(k))
            self.buttons[key] = btn

        self._update_ui()

    def select(self, key):
        if self.selected_key != key:
            self.selected_key = key
            self._update_ui()
            if self.on_change:
                self.on_change(key)

    def _update_ui(self):
        for k, btn in self.buttons.items():
            if k == self.selected_key:
                btn.config(bg=ACCENT, fg="#ffffff")
            else:
                btn.config(bg=SURFACE_LIGHT, fg=SUBTEXT)

    def _hover_on(self, key):
        if key != self.selected_key:
            self.buttons[key].config(bg=SURFACE_HOVER, fg=TEXT)

    def _hover_off(self, key):
        if key != self.selected_key:
            self.buttons[key].config(bg=SURFACE_LIGHT, fg=SUBTEXT)

    def get(self):
        return self.selected_key


class VideoPreviewCard(Card):
    """Video önizleme kartı (Küçük resim, Başlık, Kanal, Süre)."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, padx=14, pady=10, **kwargs)
        self.thumb_photo = None
        self.on_playlist_switch = None

        # Sol: Thumbnail
        self.thumb_label = tk.Label(
            self,
            bg=SURFACE_LIGHT,
            width=160,
            height=90,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        self.thumb_label.pack(side="left", padx=(0, 14))

        # Sağ: Bilgiler
        info_frame = tk.Frame(self, bg=SURFACE)
        info_frame.pack(side="left", fill="both", expand=True)

        self.title_label = tk.Label(
            info_frame, text="", bg=SURFACE, fg=TEXT, font=FONT_BOLD,
            anchor="w", justify="left", wraplength=540
        )
        self.title_label.pack(fill="x", anchor="w")

        self.uploader_label = tk.Label(
            info_frame, text="", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL, anchor="w"
        )
        self.uploader_label.pack(fill="x", anchor="w", pady=(3, 6))

        badge_row = tk.Frame(info_frame, bg=SURFACE)
        badge_row.pack(fill="x", anchor="w")

        self.duration_badge = tk.Label(
            badge_row, text="", bg=ACCENT_MUTED, fg=ACCENT_LIGHT,
            font=FONT_SMALL_BOLD, padx=8, pady=2,
            highlightthickness=1, highlightbackground=BORDER
        )
        self.duration_badge.pack(side="left")

        self.res_count_badge = tk.Label(
            badge_row, text="", bg=ACCENT_MUTED, fg=SUCCESS,
            font=FONT_SMALL, padx=8, pady=2,
            highlightthickness=1, highlightbackground=BORDER
        )
        self.res_count_badge.pack(side="left", padx=(8, 0))

        self.playlist_badge = PillButton(
            badge_row, text="📋 Oynatma Listesine Aktar",
            command=self._on_playlist_click, small=True, style="secondary"
        )

    def _on_playlist_click(self):
        if self.on_playlist_switch:
            self.on_playlist_switch()

    def update_metadata(self, metadata, on_playlist_switch=None):
        self.on_playlist_switch = on_playlist_switch
        self.title_label.config(text=metadata.get("title", "—"))
        self.uploader_label.config(text=f"👤 {metadata.get('uploader', '—')}")
        self.duration_badge.config(text=f"⏱ {metadata.get('duration', '—')}")

        resolutions = metadata.get("resolutions", [])
        if resolutions and len(resolutions) > 1:
            self.res_count_badge.config(text=f"🎬 {len(resolutions)-1} Çözünürlük")
            self.res_count_badge.pack(side="left", padx=(8, 0))
        else:
            self.res_count_badge.pack_forget()

        if metadata.get("is_playlist") and on_playlist_switch:
            count = metadata.get("playlist_count", "")
            cnt_txt = f" ({count} video)" if count and count > 1 else ""
            self.playlist_badge.config(text=f"📋 Liste Algılandı{cnt_txt} · Listeye Geç")
            self.playlist_badge.pack(side="left", padx=(8, 0))
        else:
            self.playlist_badge.pack_forget()

        thumb_img = metadata.get("thumbnail_img")
        if thumb_img:
            self.thumb_photo = ImageTk.PhotoImage(thumb_img)
            self.thumb_label.config(image=self.thumb_photo, text="", width=160, height=90)
        else:
            self.thumb_photo = None
            self.thumb_label.config(image="", text="Görsel Yok", fg=SUBTEXT, width=20, height=5)


class ContextualDownloadDrawer(tk.Frame):
    """
    Akıllı alt indirme çekmecesi — sadece indirme sırasında görünür.
    Konsol akordeon şeklinde açılıp kapanabilir.
    """
    def __init__(self, parent, on_cancel=None, on_open_file=None, **kwargs):
        super().__init__(
            parent,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            padx=16,
            pady=10,
            **kwargs
        )
        self.on_cancel = on_cancel
        self.on_open_file = on_open_file
        self.console_open = False
        self._log_buffer = []
        self._log_flush_pending = False
        self._last_stats_update = 0.0
        self._pending_stats = None
        self._stats_after_id = None
        self._base_title = "İndirme"

        # Üst Bilgi Satırı
        top_row = tk.Frame(self, bg=SURFACE)
        top_row.pack(fill="x", pady=(0, 4))

        self.lbl_title = tk.Label(top_row, text="İndirme Başlatılıyor...", bg=SURFACE, fg=TEXT, font=FONT_BOLD, anchor="w")
        self.lbl_title.pack(side="left", fill="x", expand=True)

        self.pct_var = tk.StringVar(value="0%")
        self.lbl_pct = tk.Label(top_row, textvariable=self.pct_var, bg=SURFACE, fg=ACCENT_LIGHT, font=FONT_STAT)
        self.lbl_pct.pack(side="right", padx=(8, 0))

        # İlerleme Çubuğu
        self.pbar = ttk.Progressbar(self, style="Custom.Horizontal.TProgressbar", mode="determinate", maximum=100)
        self.pbar.pack(fill="x", pady=(3, 6))

        # İstatistikler ve Butonlar
        bot_row = tk.Frame(self, bg=SURFACE)
        bot_row.pack(fill="x")

        stat_frame = tk.Frame(bot_row, bg=SURFACE)
        stat_frame.pack(side="left")

        self.speed_var = tk.StringVar(value="⚡ —")
        self.lbl_speed = tk.Label(
            stat_frame, textvariable=self.speed_var, bg=ACCENT_MUTED, fg=ACCENT_LIGHT,
            font=FONT_SMALL, padx=8, pady=3,
            highlightthickness=1, highlightbackground=BORDER
        )
        self.lbl_speed.pack(side="left", padx=(0, 6))

        self.dl_var = tk.StringVar(value="📥 —")
        self.lbl_dl = tk.Label(
            stat_frame, textvariable=self.dl_var, bg=ACCENT_MUTED, fg=ACCENT_LIGHT,
            font=FONT_SMALL, padx=8, pady=3,
            highlightthickness=1, highlightbackground=BORDER
        )
        self.lbl_dl.pack(side="left", padx=(0, 6))

        self.eta_var = tk.StringVar(value="⏱ —")
        self.lbl_eta = tk.Label(
            stat_frame, textvariable=self.eta_var, bg=ACCENT_MUTED, fg=ACCENT_LIGHT,
            font=FONT_SMALL, padx=8, pady=3,
            highlightthickness=1, highlightbackground=BORDER
        )
        self.lbl_eta.pack(side="left")

        # Sağ Butonlar
        action_frame = tk.Frame(bot_row, bg=SURFACE)
        action_frame.pack(side="right")

        self.btn_open = PillButton(action_frame, text="📁 Klasörde Göster", command=self._open_file_click, small=True, style="success")
        self.btn_cancel = PillButton(action_frame, text="⛔ İptal Et", command=self._cancel_click, small=True, style="danger")
        self.btn_cancel.pack(side="left", padx=(0, 6))

        self.btn_console_toggle = PillButton(action_frame, text="▲ Konsol", command=self._toggle_console, small=True, style="secondary")
        self.btn_console_toggle.pack(side="left")

        self.btn_close = PillButton(action_frame, text="✕", command=self.hide, small=True, style="ghost")

        # Konsol Çekmecesi (Başlangıçta Gizli)
        self.console_frame = tk.Frame(self, bg=ENTRY_BG, highlightthickness=1, highlightbackground=BORDER)

        csb = ttk.Scrollbar(self.console_frame, style="Vertical.TScrollbar")
        csb.pack(side="right", fill="y")

        self.log_text = tk.Text(
            self.console_frame, bg=ENTRY_BG, fg=TEXT, font=FONT_MONO,
            insertbackground=TEXT, selectbackground=ACCENT, relief="flat", bd=0,
            wrap="word", height=6, yscrollcommand=csb.set, state="disabled"
        )
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)
        csb.config(command=self.log_text.yview)

        self.log_text.tag_config("info", foreground=TEXT)
        self.log_text.tag_config("success", foreground=SUCCESS)
        self.log_text.tag_config("warn", foreground=WARNING)
        self.log_text.tag_config("error", foreground=ERROR)
        self.log_text.tag_config("accent", foreground=ACCENT_LIGHT)

    def show(self, title="İndirme", clear_logs=True):
        self._base_title = title
        self.lbl_title.config(text=f"⏳ {title}")
        self.pbar["value"] = 0
        self.pct_var.set("0%")
        self.speed_var.set("⚡ —")
        self.dl_var.set("📥 —")
        self.eta_var.set("⏱ —")
        self._last_stats_update = 0.0
        self._pending_stats = None
        if self._stats_after_id:
            try:
                self.after_cancel(self._stats_after_id)
            except Exception:
                pass
            self._stats_after_id = None
        self._log_buffer.clear()
        self._log_flush_pending = False
        if clear_logs:
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.config(state="disabled")
        self.btn_open.pack_forget()
        self.btn_close.pack_forget()
        self.btn_cancel.pack(side="left", padx=(0, 6), before=self.btn_console_toggle)
        parent_container = getattr(self.master, "content_container", None)
        if parent_container and parent_container.winfo_ismapped():
            self.pack(fill="x", side="bottom", before=parent_container)
        else:
            self.pack(fill="x", side="bottom")

    def set_phase(self, phase_text):
        if not self.winfo_exists():
            return
        base = getattr(self, "_base_title", None)
        new_text = f"⏳ {base} · {phase_text}" if base else f"⏳ {phase_text}"
        if self.lbl_title.cget("text") != new_text:
            self.lbl_title.config(text=new_text)

    def hide(self):
        self.pack_forget()
        if self.console_open:
            self._toggle_console()

    def update_stats(self, pct, speed, total, eta):
        # 0% ve 100% gibi kritik sınırları hemen göster
        if pct <= 0 or pct >= 100:
            if self._stats_after_id:
                try:
                    self.after_cancel(self._stats_after_id)
                except Exception:
                    pass
                self._stats_after_id = None
            self._pending_stats = None
            self._apply_stats(pct, speed, total, eta)
            return

        now = time.monotonic()
        # 50ms (~20 FPS) altındaki sık çağrıları akıllıca kuyrukla (UI kilitlenmesini önler)
        if now - self._last_stats_update >= 0.05:
            self._last_stats_update = now
            self._apply_stats(pct, speed, total, eta)
        else:
            self._pending_stats = (pct, speed, total, eta)
            if not self._stats_after_id:
                try:
                    self._stats_after_id = self.after(50, self._apply_pending_stats)
                except Exception:
                    self._apply_stats(pct, speed, total, eta)

    def _apply_pending_stats(self):
        self._stats_after_id = None
        if self._pending_stats:
            p, s, t, e = self._pending_stats
            self._pending_stats = None
            self._last_stats_update = time.monotonic()
            self._apply_stats(p, s, t, e)

    def _apply_stats(self, pct, speed, total, eta):
        if not self.winfo_exists():
            return
        self.pbar["value"] = pct
        self.pct_var.set(f"{pct:.1f}%")
        self.speed_var.set(f"⚡ {speed}")
        self.dl_var.set(f"📥 {pct:.1f}% / {total}")
        self.eta_var.set(f"⏱ {eta}")

    def on_complete_status(self, success, output_path=None, error_msg=None, cancelled=False):
        if self._stats_after_id:
            try:
                self.after_cancel(self._stats_after_id)
            except Exception:
                pass
            self._stats_after_id = None
        if self._log_flush_pending:
            self._flush_logs()

        self.btn_cancel.pack_forget()
        if cancelled:
            self.lbl_title.config(text="⛔ İndirme kullanıcı tarafından iptal edildi.")
            self.btn_close.pack(side="left", padx=(6, 0))
        elif success:
            self.pbar["value"] = 100
            self.pct_var.set("100%")
            self.lbl_title.config(text="✅ İndirme başarıyla tamamlandı!")
            self.btn_open.pack(side="left", padx=(0, 6), before=self.btn_console_toggle)
            self.btn_close.pack(side="left", padx=(6, 0))
        else:
            self.lbl_title.config(text=f"❌ Hata: {error_msg or 'İndirme başarısız oldu'}")
            if not self.console_open:
                self._toggle_console()
            self.btn_close.pack(side="left", padx=(6, 0))

    def log_line(self, line, tag="info"):
        self._log_buffer.append((line, tag))
        if not self._log_flush_pending:
            self._log_flush_pending = True
            try:
                self.after_idle(self._flush_logs)
            except Exception:
                self._flush_logs()

    def _flush_logs(self):
        self._log_flush_pending = False
        if not self._log_buffer or not self.log_text.winfo_exists():
            return
        buffer = self._log_buffer
        self._log_buffer = []

        self.log_text.config(state="normal")
        for line, tag in buffer:
            self.log_text.insert("end", line + "\n", tag)
        try:
            num = int(self.log_text.index("end-1c").split(".")[0])
            if num > 1000:
                self.log_text.delete("1.0", f"{num - 1000}.0")
        except Exception:
            pass
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _toggle_console(self):
        if self.console_open:
            self.console_frame.pack_forget()
            self.btn_console_toggle.config(text="▲ Konsol")
            self.console_open = False
        else:
            self.console_frame.pack(fill="x", pady=(8, 0))
            self.btn_console_toggle.config(text="▼ Konsol")
            self.console_open = True

    def _cancel_click(self):
        if self.on_cancel:
            self.on_cancel()

    def _open_file_click(self):
        if self.on_open_file:
            self.on_open_file()

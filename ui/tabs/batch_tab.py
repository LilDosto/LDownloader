import tkinter as tk
from tkinter import ttk, messagebox
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER, ACCENT, ACCENT_LIGHT, TEXT, SUBTEXT, SUCCESS, ERROR, WARNING,
    FONT_HERO, FONT_TITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD
)
from ui.components import Card, PillButton, SegmentedPill
from core.config import config

class BatchTab(tk.Frame):
    def __init__(self, parent, on_batch_requested=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.on_batch_requested = on_batch_requested
        self.queue = []
        self._build_ui()

    def _build_ui(self):
        # ── Başlık ───────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 22))

        tk.Label(hdr, text="Toplu indirme", bg=BG, fg=TEXT, font=FONT_HERO).pack(anchor="w")
        tk.Label(hdr, text="Bağlantıları ekleyin; uygulama sırayla indirsin.",
                 bg=BG, fg=SUBTEXT, font=FONT_REGULAR).pack(anchor="w", pady=(6, 0))

        # ── 1. URL Giriş Kartı ──────────────────────────────────────
        c_input = Card(self)
        c_input.pack(fill="x", padx=32, pady=(0, 16))

        top = tk.Frame(c_input, bg=SURFACE)
        top.pack(fill="x")

        tk.Label(top, text="BAĞLANTILAR", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL_BOLD).pack(side="left")

        PillButton(top, text="Temizle", command=self._clear_input, small=True, style="ghost").pack(side="right")
        PillButton(top, text="Panodan ekle", command=self._paste_clipboard, small=True, style="secondary").pack(side="right", padx=(0, 8))

        self.text_input = tk.Text(
            c_input, bg=ENTRY_BG, fg=TEXT, insertbackground=ACCENT_LIGHT, selectbackground=ACCENT,
            relief="flat", bd=0, font=("Consolas", 10), height=5,
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT
        )
        self.text_input.pack(fill="x", pady=(10, 0))

        # ── 2. Format ve Ekle Çubuğu ────────────────────────────────
        c_act = Card(self)
        c_act.pack(fill="x", padx=32, pady=(0, 16))

        arow = tk.Frame(c_act, bg=SURFACE)
        arow.pack(fill="x")

        tk.Label(arow, text="Format:", bg=SURFACE, fg=SUBTEXT, font=FONT_REGULAR).pack(side="left")
        self.media_seg = SegmentedPill(
            arow,
            items=[("video", "Video"), ("audio", "Ses")],
            default_val="video"
        )
        self.media_seg.pack(side="left", padx=(10, 20))

        PillButton(arow, text="➕ Kuyruğa Ekle", command=self._add_to_queue, style="secondary").pack(side="right")

        # ── 3. Kuyruk Listesi ────────────────────────────────────────
        c_queue = Card(self)
        c_queue.pack(fill="both", expand=True, padx=32, pady=(0, 18))

        q_top = tk.Frame(c_queue, bg=SURFACE)
        q_top.pack(fill="x", pady=(0, 8))
        self.lbl_queue_count = tk.Label(q_top, text="Kuyruk · 0 öğe", bg=SURFACE, fg=TEXT, font=FONT_BOLD)
        self.lbl_queue_count.pack(side="left")

        PillButton(q_top, text="Kuyruğu temizle", command=self._clear_queue, small=True, style="ghost").pack(side="right")

        tree_frame = tk.Frame(c_queue, bg=SURFACE)
        tree_frame.pack(fill="both", expand=True)

        columns = ("no", "url", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=5)
        self.tree.heading("no", text="#")
        self.tree.heading("url", text="Bağlantı URL'si")
        self.tree.heading("status", text="Durum")

        self.tree.column("no", width=40, anchor="center")
        self.tree.column("url", width=480, anchor="w")
        self.tree.column("status", width=120, anchor="center")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── 4. Başlat Butonu ─────────────────────────────────────────
        PillButton(
            self,
            text="Tümünü indirmeye başla",
            command=self._on_start_batch,
            style="primary"
        ).pack(fill="x", padx=32, pady=(0, 24), ipady=3)

    def _paste_clipboard(self):
        try:
            clip = self.clipboard_get().strip()
            if clip:
                self.text_input.insert("end", clip + "\n")
        except Exception:
            pass

    def _clear_input(self):
        self.text_input.delete("1.0", "end")

    def _add_to_queue(self):
        raw = self.text_input.get("1.0", "end").strip()
        if not raw:
            return
        lines = [line.strip() for line in raw.splitlines() if line.strip() and line.strip().startswith("http")]
        if not lines:
            messagebox.showinfo("Bilgi", "Geçerli bir http/https bağlantısı bulunamadı.", parent=self)
            return

        for u in lines:
            idx = len(self.queue) + 1
            item = {"idx": idx, "url": u, "status": "⏳ Bekliyor"}
            self.queue.append(item)
            self.tree.insert("", "end", iid=str(idx), values=(idx, u, "⏳ Bekliyor"))

        self.lbl_queue_count.config(text=f"Kuyruk · {len(self.queue)} öğe")
        self.text_input.delete("1.0", "end")

    def _clear_queue(self):
        self.queue.clear()
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.lbl_queue_count.config(text="Kuyruk · 0 öğe")

    def update_item_status(self, idx, status_text):
        for item in self.queue:
            if item["idx"] == idx:
                item["status"] = status_text
                try:
                    self.tree.item(str(idx), values=(idx, item["url"], status_text))
                except Exception:
                    pass
                break

    def _on_start_batch(self):
        if not self.queue:
            self._add_to_queue()
        if not self.queue:
            messagebox.showwarning("Uyarı", "Kuyrukta indirilecek geçerli bağlantı yok!", parent=self)
            return

        urls = [item["url"] for item in self.queue]
        media_type = self.media_seg.get()
        options = {
            "mode": "batch",
            "media_type": media_type,
            "format": config.get("video_format", "mp4") if media_type == "video" else config.get("audio_format", "mp3"),
            "quality": config.get("video_quality", "Best Quality (En İyi)") if media_type == "video" else config.get("audio_quality", "Best Quality (En İyi)"),
            "embed_thumbnail": config.get("embed_thumbnail", True),
            "embed_subtitles": config.get("embed_subtitles", False),
            "subtitle_lang": config.get("subtitle_lang", "tr,en"),
            "add_metadata": config.get("add_metadata", True),
            "concurrent_fragments": config.get("concurrent_fragments", 4),
            "speed_limit": config.get("speed_limit", ""),
            "ignore_errors": config.get("ignore_errors", True)
        }

        if self.on_batch_requested:
            self.on_batch_requested(urls, config.get("download_dir"), options, self.update_item_status)

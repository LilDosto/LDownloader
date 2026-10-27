import tkinter as tk
from tkinter import ttk, messagebox
from ui.theme import (
    BG, SURFACE, SURFACE_LIGHT, ENTRY_BG, BORDER, ACCENT, ACCENT_LIGHT, TEXT, SUBTEXT, MUTED, SUCCESS, ERROR,
    FONT_HERO, FONT_TITLE, FONT_REGULAR, FONT_BOLD, FONT_SMALL, FONT_SMALL_BOLD
)
from ui.components import Card, PillButton, ModernEntry
from core.history import history


class HistoryTab(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.search_query = ""
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # ── Ana Tablo ve Arama Kartı ─────────────────────────────────
        c_table = Card(self, padx=24, pady=18)
        c_table.pack(fill="both", expand=True, padx=32, pady=(24, 14))

        # Üst Araç Çubuğu
        s_row = tk.Frame(c_table, bg=SURFACE)
        s_row.pack(fill="x", pady=(0, 12))

        self.lbl_count = tk.Label(s_row, text="Geçmiş (0)", bg=SURFACE, fg=TEXT, font=FONT_BOLD)
        self.lbl_count.pack(side="left", padx=(0, 16))

        self.search_var = tk.StringVar()
        self.search_entry = ModernEntry(
            s_row, textvariable=self.search_var,
            placeholder="🔍 Başlık, URL veya formata göre filtrele...",
            on_change=self._on_search_typed
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=3)

        PillButton(s_row, text="↻ Yenile", command=self.refresh, small=True, style="secondary").pack(side="left", padx=(10, 0))
        PillButton(s_row, text="🗑 Temizle", command=self._clear_all, small=True, style="danger").pack(side="left", padx=(8, 0))

        # Tablo
        tree_frame = tk.Frame(c_table, bg=SURFACE)
        tree_frame.pack(fill="both", expand=True)

        columns = ("date", "title", "format", "size", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("date", text="Tarih")
        self.tree.heading("title", text="Dosya / Video Başlığı")
        self.tree.heading("format", text="Format")
        self.tree.heading("size", text="Boyut")
        self.tree.heading("status", text="Durum")

        self.tree.column("date", width=130, anchor="center", stretch=False)
        self.tree.column("title", width=420, anchor="w")
        self.tree.column("format", width=130, anchor="center", stretch=False)
        self.tree.column("size", width=90, anchor="center", stretch=False)
        self.tree.column("status", width=100, anchor="center", stretch=False)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._play_selected())

        # ── Alt Eylem Çubuğu ─────────────────────────────────────────
        act_bar = tk.Frame(self, bg=BG)
        act_bar.pack(fill="x", padx=32, pady=(0, 20))

        PillButton(act_bar, text="▶ Dosyayı Aç / Oynat", command=self._play_selected, style="primary").pack(side="left", padx=(0, 10))
        PillButton(act_bar, text="📁 Klasörde Göster", command=self._open_folder_selected, style="secondary").pack(side="left", padx=(0, 10))
        PillButton(act_bar, text="🔗 Bağlantıyı Kopyala", command=self._copy_url_selected, style="secondary").pack(side="left", padx=(0, 10))
        PillButton(act_bar, text="✕ Listeden Kaldır", command=self._remove_selected, style="ghost").pack(side="left")

    def _on_search_typed(self, text):
        self.search_query = text.lower().strip()
        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        items = history.get_all()
        if self.search_query:
            items = [
                i for i in items
                if self.search_query in i.get("title", "").lower()
                or self.search_query in i.get("format", "").lower()
                or self.search_query in i.get("url", "").lower()
            ]

        self.lbl_count.config(text=f"Geçmiş ({len(items)})")

        for it in items:
            status_text = "✅ Başarılı" if it.get("status") == "completed" else "❌ Hata"
            self.tree.insert("", "end", iid=it["id"], values=(
                it.get("date", "—"),
                it.get("title", "—"),
                it.get("format", "—"),
                it.get("size", "—"),
                status_text
            ))

    def _get_selected_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Bilgi", "Lütfen listeden bir kayıt seçin.", parent=self)
            return None
        item_id = sel[0]
        for it in history.get_all():
            if it.get("id") == item_id:
                return it
        return None

    def _play_selected(self):
        it = self._get_selected_item()
        if it:
            if not history.play_file(it.get("path")):
                messagebox.showerror("Hata", f"Dosya bulunamadı veya açılamadı:\n{it.get('path')}", parent=self)

    def _open_folder_selected(self):
        it = self._get_selected_item()
        if it:
            if not history.show_in_folder(it.get("path")):
                messagebox.showerror("Hata", f"Hedef klasör açılamadı:\n{it.get('path')}", parent=self)

    def _copy_url_selected(self):
        it = self._get_selected_item()
        if it and it.get("url"):
            self.clipboard_clear()
            self.clipboard_append(it["url"])
            messagebox.showinfo("Kopyalandı", "Medya bağlantısı panoya kopyalandı.", parent=self)

    def _remove_selected(self):
        sel = self.tree.selection()
        if sel:
            history.remove(sel[0])
            self.refresh()

    def _clear_all(self):
        if messagebox.askyesno("Onay", "Tüm indirme geçmişini silmek istediğinize emin misiniz?", parent=self):
            history.clear()
            self.refresh()

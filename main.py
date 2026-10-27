"""LDownloader v3 — Video & Ses İndirici Ana Başlatıcı"""
import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if __name__ == "__main__":
    try:
        from ui.app import main
        main()
    except Exception as ex:
        import traceback
        log_path = "crash.log"
        try:
            from core.config import get_data_dir
            log_path = os.path.join(get_data_dir(), "crash.log")
            with open(log_path, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "LDownloader Başlatma Hatası",
            f"Uygulama başlatılırken bir hata oluştu:\n\n{ex}\n\nDetaylar: {log_path}"
        )
        sys.exit(1)

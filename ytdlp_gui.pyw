"""
LDownloader - Video & Ses İndirici (GUI)
Giriş noktası / Windows .pyw Başlatıcısı
"""
import os
import sys

# PyInstaller paketli ortamında veya kaynak koddan çalışırken kök dizini ekle
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if __name__ == "__main__":
    try:
        from ui.app import main
        main()
    except Exception as ex:
        import traceback
        try:
            exe_dir = os.path.dirname(sys.executable)
            with open(os.path.join(exe_dir, "crash.log"), "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "LDownloader Başlatma Hatası",
            f"Uygulama başlatılırken bir hata oluştu:\n\n{ex}\n\nDetaylar: crash.log"
        )
        sys.exit(1)

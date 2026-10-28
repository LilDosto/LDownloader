import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from uuid import uuid4
from core.config import get_data_dir

logger = logging.getLogger(__name__)


class HistoryManager:
    def __init__(self):
        self.history_file = os.path.join(get_data_dir(), "history.json")
        self.items = []
        self.load()

    def load(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                if not isinstance(items, list):
                    raise ValueError("History file must contain a JSON list.")
                self.items = items
            except (OSError, json.JSONDecodeError, ValueError):
                logger.exception("Could not load download history from %s", self.history_file)
                self.items = []
        else:
            self.items = []

    def save(self):
        temp_path = self.history_file + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2, ensure_ascii=False)
                f.flush()
            os.replace(temp_path, self.history_file)
        except (OSError, TypeError):
            logger.exception("Could not save download history to %s", self.history_file)
            try:
                os.remove(temp_path)
            except OSError:
                logger.debug("Could not remove temporary history file %s", temp_path, exc_info=True)

    def add(self, title, url, file_path, fmt_info, status="completed"):
        size_str = "—"
        if file_path and os.path.exists(file_path):
            try:
                bytes_size = os.path.getsize(file_path)
                if bytes_size >= 1024 * 1024 * 1024:
                    size_str = f"{bytes_size / (1024*1024*1024):.2f} GB"
                elif bytes_size >= 1024 * 1024:
                    size_str = f"{bytes_size / (1024*1024):.2f} MB"
                else:
                    size_str = f"{bytes_size / 1024:.1f} KB"
            except Exception:
                pass

        item = {
            "id": uuid4().hex,
            "title": title or os.path.basename(file_path or url),
            "url": url,
            "path": file_path,
            "format": fmt_info,
            "size": size_str,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": status
        }
        # En yeni en üstte
        self.items.insert(0, item)
        # Maksimum 200 geçmiş kaydı sakla
        if len(self.items) > 200:
            self.items = self.items[:200]
        self.save()
        return item

    def get_all(self):
        return self.items

    def remove(self, item_id):
        self.items = [i for i in self.items if i.get("id") != item_id]
        self.save()

    def clear(self):
        self.items = []
        self.save()

    @staticmethod
    def show_in_folder(file_path):
        """Dosyayı Windows Explorer'da seçili olarak gösterir."""
        if not file_path:
            return False
        
        path = os.path.normpath(file_path)
        if os.path.exists(path):
            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{path}"')
                return True
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
                return True
        elif os.path.isdir(os.path.dirname(path)):
            if sys.platform == "win32":
                subprocess.Popen(f'explorer "{os.path.dirname(path)}"')
                return True
        return False

    @staticmethod
    def play_file(file_path):
        """Dosyayı varsayılan medya oynatıcıda açar."""
        if not file_path or not os.path.exists(file_path):
            return False
        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            else:
                subprocess.Popen(["xdg-open", file_path])
            return True
        except Exception:
            return False

history = HistoryManager()

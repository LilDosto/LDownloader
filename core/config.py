import os
import sys
import json
import logging

logger = logging.getLogger(__name__)

def get_app_dir():
    """PyInstaller veya kaynak kod dizini."""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_dir():
    """Kullanıcı verilerinin ve ayarların saklandığı dizin."""
    app_data = os.getenv('APPDATA')
    if app_data:
        data_dir = os.path.join(app_data, 'LDownloader')
    else:
        data_dir = os.path.join(os.path.expanduser('~'), '.ldownloader')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_bin_dir():
    """Taşınabilir yt-dlp.exe ve ffmpeg.exe ikililerinin saklandığı dizin."""
    # Öncelik 1: Uygulama çalışma dizinindeki bin/ (yazılabilirse veya içinde araç varsa)
    local_bin = os.path.join(get_app_dir(), 'bin')
    if os.path.isdir(local_bin) and os.access(local_bin, os.W_OK):
        return local_bin
    
    # Öncelik 2: AppData altındaki bin/
    user_bin = os.path.join(get_data_dir(), 'bin')
    os.makedirs(user_bin, exist_ok=True)
    return user_bin


class ConfigManager:
    _DEFAULT_CONFIG = {
        "theme": "dark",
        "download_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
        "video_format": "mp4",
        "video_quality": "Best Quality (En İyi)",
        "audio_format": "mp3",
        "audio_quality": "Best Quality (En İyi)",
        "cookies_mode": "none",
        "cookies_browser": "chrome",
        "cookies_path": "",
        "embed_subtitles": False,
        "subtitle_lang": "tr,en",
        "embed_thumbnail": True,
        "add_metadata": True,
        "concurrent_fragments": 4,
        "auto_fetch_metadata": True,
        "speed_limit": "",
        "proxy": "",
        "ignore_errors": True,
        "use_download_archive": False,
        "sponsorblock_remove": False,
        "sponsorblock_cats": "sponsor,intro,outro,selfpromo,interaction"
    }

    def __init__(self):
        self.config_path = os.path.join(get_data_dir(), "config.json")
        self.config = dict(self._DEFAULT_CONFIG)
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if not isinstance(saved, dict):
                    raise ValueError("Config file must contain a JSON object.")
                if "concurrent_fragments" in saved:
                    try:
                        fragments = int(saved["concurrent_fragments"])
                    except (TypeError, ValueError):
                        fragments = self._DEFAULT_CONFIG["concurrent_fragments"]
                    if fragments not in (1, 2, 4, 8, 16):
                        fragments = self._DEFAULT_CONFIG["concurrent_fragments"]
                    saved["concurrent_fragments"] = fragments
                self.config.update(saved)
            except (OSError, json.JSONDecodeError, ValueError):
                logger.exception("Could not load configuration from %s", self.config_path)

    def save(self):
        temp_path = self.config_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                f.flush()
            os.replace(temp_path, self.config_path)
        except OSError:
            logger.exception("Could not save configuration to %s", self.config_path)
            try:
                os.remove(temp_path)
            except OSError:
                logger.debug("Could not remove temporary configuration file %s", temp_path, exc_info=True)

    def get(self, key, default=None):
        return self.config.get(key, default if default is not None else self._DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()

# Tekil örnek
config = ConfigManager()

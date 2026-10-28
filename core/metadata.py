import os
import io
import threading
import requests
from PIL import Image, ImageTk
from core.dependencies import find_executable

_METADATA_CACHE = {}
_CACHE_LOCK = threading.Lock()
_MAX_CACHE_SIZE = 64
_IN_FLIGHT = {}

def format_duration(seconds):
    """Saniyeyi ss:dd veya saat:ss:dd formatına dönüştürür."""
    if not seconds:
        return "—"
    try:
        s = int(seconds)
        hours = s // 3600
        minutes = (s % 3600) // 60
        secs = s % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    except Exception:
        return "—"


def extract_resolutions(info_dict):
    """Videonun format listesinden gerçek çözünürlükleri çıkarır."""
    formats = info_dict.get("formats") or []
    heights = set()
    for f in formats:
        # Sadece video içeren formatlar
        if f.get("vcodec") != "none" and f.get("height"):
            heights.add(int(f["height"]))

    sorted_heights = sorted(list(heights), reverse=True)
    res_list = ["Best Quality (En İyi)"]
    for h in sorted_heights:
        label = f"{h}p"
        if h >= 2160:
            label += " (4K)"
        elif h >= 1440:
            label += " (2K)"
        elif h >= 1080:
            label += " (FHD)"
        elif h >= 720:
            label += " (HD)"
        res_list.append(label)

    return res_list


def fetch_thumbnail_image(url, size=(160, 90)):
    """Thumbnail URL'sinden resmi çeker ve belirtilen boyutta PIL Image döndürür."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            img_data = resp.content
            img = Image.open(io.BytesIO(img_data))
            img = img.convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            return img
    except Exception:
        pass
    return None


def fetch_video_metadata(url: str, cookies_args: list = None, proxy: str = None, callback=None, error_callback=None):
    """Videonun temel bilgilerini arka planda çeker (önbellek ve istek tekilleştirme destekli)."""
    clean_url = (url or "").strip()
    if not clean_url:
        if error_callback:
            error_callback("Geçersiz URL")
        return

    with _CACHE_LOCK:
        if clean_url in _METADATA_CACHE:
            cached = _METADATA_CACHE[clean_url]
            if callback:
                # Önbellekteki veriyi anında döndür
                threading.Thread(target=lambda: callback(cached), daemon=True).start()
            return

        if clean_url in _IN_FLIGHT:
            _IN_FLIGHT[clean_url].append((callback, error_callback))
            return

        _IN_FLIGHT[clean_url] = [(callback, error_callback)]

    def _worker():
        try:
            import yt_dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
                'skip_download': True,
                'socket_timeout': 15,
            }
            if proxy:
                ydl_opts['proxy'] = proxy

            if cookies_args:
                # Cookies args parse (örnek: --cookies-from-browser firefox[:profile] veya --cookies file)
                for i, arg in enumerate(cookies_args):
                    if arg == "--cookies-from-browser" and i + 1 < len(cookies_args):
                        spec = cookies_args[i + 1]
                        if ":" in spec:
                            b_name, b_prof = spec.split(":", 1)
                            ydl_opts['cookiesfrombrowser'] = (b_name, b_prof)
                        else:
                            ydl_opts['cookiesfrombrowser'] = (spec,)
                    elif arg == "--cookies" and i + 1 < len(cookies_args):
                        ydl_opts['cookiefile'] = cookies_args[i + 1]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                if not info:
                    raise ValueError("Medya bilgileri alınamadı.")

                is_playlist = info.get('_type') == 'playlist' or 'entries' in info
                entries = list(info.get('entries') or []) if is_playlist else []
                first_entry = entries[0] if (is_playlist and entries and isinstance(entries[0], dict)) else info

                title = first_entry.get("title") or info.get("title") or "Bilinmeyen Başlık"
                uploader = (
                    first_entry.get("uploader")
                    or first_entry.get("channel")
                    or info.get("uploader")
                    or info.get("channel")
                    or "Bilinmeyen Kanal"
                )
                duration = format_duration(first_entry.get("duration") or info.get("duration"))
                thumbnail_url = first_entry.get("thumbnail") or info.get("thumbnail")
                if not thumbnail_url:
                    thumbs = first_entry.get("thumbnails") or info.get("thumbnails") or []
                    if thumbs and isinstance(thumbs, list):
                        thumbnail_url = thumbs[-1].get("url")

                resolutions = extract_resolutions(first_entry)
                thumb_img = fetch_thumbnail_image(thumbnail_url)

                metadata = {
                    "is_playlist": is_playlist,
                    "playlist_count": len(entries) if is_playlist else 1,
                    "title": title,
                    "uploader": uploader,
                    "duration": duration,
                    "thumbnail_url": thumbnail_url,
                    "thumbnail_img": thumb_img,
                    "resolutions": resolutions,
                    "raw_info": first_entry
                }

                with _CACHE_LOCK:
                    if len(_METADATA_CACHE) >= _MAX_CACHE_SIZE:
                        # En eski kaydı temizle
                        _METADATA_CACHE.pop(next(iter(_METADATA_CACHE)))
                    _METADATA_CACHE[clean_url] = metadata
                    listeners = _IN_FLIGHT.pop(clean_url, [])

                for cb, _ in listeners:
                    if cb:
                        try:
                            cb(metadata)
                        except Exception:
                            pass

        except Exception as ex:
            err_msg = str(ex)
            with _CACHE_LOCK:
                listeners = _IN_FLIGHT.pop(clean_url, [])
            for _, err_cb in listeners:
                if err_cb:
                    try:
                        err_cb(err_msg)
                    except Exception:
                        pass

    threading.Thread(target=_worker, daemon=True).start()

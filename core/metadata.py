import os
import io
import threading
import requests
from PIL import Image, ImageTk
from core.dependencies import find_executable

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


def fetch_video_metadata(url: str, cookies_args: list = None, callback=None, error_callback=None):
    """Videonun temel bilgilerini arka planda çeker."""
    def _worker():
        try:
            import yt_dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
            }
            if cookies_args:
                # Cookies args parse (örnek: --cookies-from-browser firefox veya --cookies file)
                for i, arg in enumerate(cookies_args):
                    if arg == "--cookies-from-browser" and i + 1 < len(cookies_args):
                        ydl_opts['cookiesfrombrowser'] = (cookies_args[i+1],)
                    elif arg == "--cookies" and i + 1 < len(cookies_args):
                        ydl_opts['cookiefile'] = cookies_args[i+1]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Eğer playlist ise ilk videoyu al veya genel bilgi oluştur
                is_playlist = 'entries' in info
                first_entry = info['entries'][0] if is_playlist and info.get('entries') else info

                title = first_entry.get("title") or info.get("title", "Bilinmeyen Başlık")
                uploader = first_entry.get("uploader") or info.get("uploader", "Bilinmeyen Kanal")
                duration = format_duration(first_entry.get("duration"))
                thumbnail_url = first_entry.get("thumbnail") or info.get("thumbnail")
                resolutions = extract_resolutions(first_entry)

                thumb_img = fetch_thumbnail_image(thumbnail_url)

                metadata = {
                    "is_playlist": is_playlist,
                    "title": title,
                    "uploader": uploader,
                    "duration": duration,
                    "thumbnail_url": thumbnail_url,
                    "thumbnail_img": thumb_img,
                    "resolutions": resolutions,
                    "raw_info": first_entry
                }

                if callback:
                    callback(metadata)

        except Exception as ex:
            if error_callback:
                error_callback(str(ex))

    threading.Thread(target=_worker, daemon=True).start()

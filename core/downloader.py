import os
import sys
import re
import subprocess
import threading
from core.dependencies import find_executable, get_ffmpeg_dir, get_ytdlp_cmd
from core.diagnostics import diagnose

class DownloadEngine:
    _PROGRESS_RE = re.compile(
        r"\[PROGRESS\]\s*(?P<pct>[\d.]+)(?:%\s*)?\|\s*(?P<speed>.*?)\s*\|\s*(?P<total>.*?)\s*\|\s*(?P<eta>.*)"
    )
    _DL_RE = re.compile(
        r"\[download\]\s+(?P<pct>[\d.]+)%\s+of\s+~?(?P<total>\S+)\s+"
        r"at\s+(?P<speed>.*?)\s+ETA\s+(?P<eta>\S+)"
    )
    _DEST_RE = re.compile(
        r"\[(?:download|Merger|ExtractAudio|FixupM3u8|VideoRemuxer|VideoConvertor)\]\s+"
        r"(?:Destination:\s+|Merging formats into\s+\"|Writing video subtitles to:\s+|Remuxing video from \S+ to\s+\"?)(?P<path>[^\"]+)"
    )
    _ALREADY_RE = re.compile(
        r"\[download\]\s+(?P<path>.+?)\s+has already been downloaded"
    )
    _FINAL_PATH_PREFIX = "[FINAL_PATH] "

    def __init__(self):
        self._proc = None
        self._running = False
        self._cancelled = False
        self._current_file = None
        self._lock = threading.Lock()

    @property
    def is_running(self):
        return self._running

    def cancel(self):
        """Devam eden indirmeyi ve tüm alt süreç ağacını güvenle ve arayüzü dondurmadan sonlandırır."""
        with self._lock:
            if not self._running or not self._proc:
                return
            self._cancelled = True
            proc = self._proc

        def _do_kill():
            try:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    proc.kill()
            except Exception:
                pass

        threading.Thread(target=_do_kill, daemon=True).start()

    def start_download(self, cmd_args, callbacks):
        """
        İndirmeyi arka planda başlatır.
        callbacks dict:
            - on_progress(pct, speed, total, eta)
            - on_log(line, tag)
            - on_status(msg)
            - on_complete(success, output_path, error_msg)
        """
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._cancelled = False
            self._current_file = None

        thread = threading.Thread(target=self._worker, args=(cmd_args, callbacks), daemon=True)
        thread.start()
        return True

    def _worker(self, cmd_args, cb):
        rc = -1
        error_message = None
        last_destination = None

        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"
            from core.config import get_bin_dir
            b_dir = get_bin_dir()
            if b_dir and b_dir not in env.get("PATH", ""):
                env["PATH"] = f"{b_dir};{env.get('PATH', '')}"

            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            self._proc = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=flags,
                bufsize=1,
                env=env
            )

            if self._proc and self._proc.stdout:
                for line in iter(self._proc.stdout.readline, ''):
                    line = line.rstrip()
                    if not line:
                        continue

                    if line.startswith(self._FINAL_PATH_PREFIX):
                        final_p = line[len(self._FINAL_PATH_PREFIX):].strip().strip('"')
                        if final_p and final_p != "NA":
                            last_destination = final_p
                            self._current_file = final_p
                        continue

                    # 1. Dosya yolu yakalama
                    m_dest = self._DEST_RE.search(line) or self._ALREADY_RE.search(line)
                    if m_dest:
                        dest = m_dest.group("path").strip().strip('"')
                        if not dest.endswith((".part", ".ytdl", ".vtt", ".srt", ".ass", ".lrc")):
                            last_destination = dest
                            self._current_file = dest

                    # Durum / Aşama güncellemesi
                    if line.startswith("[ExtractAudio]"):
                        if cb.get("on_status"):
                            cb["on_status"]("Ses dönüştürülüyor...")
                    elif line.startswith("[Merger]"):
                        if cb.get("on_status"):
                            cb["on_status"]("Formatlar birleştiriliyor...")
                    elif line.startswith(("[EmbedThumbnail]", "[ThumbnailsConvertor]")):
                        if cb.get("on_status"):
                            cb["on_status"]("Kapak resmi ekleniyor...")
                    elif line.startswith("[Metadata]"):
                        if cb.get("on_status"):
                            cb["on_status"]("Üstveri ekleniyor...")
                    elif line.startswith("[SponsorBlock]"):
                        if cb.get("on_status"):
                            cb["on_status"]("Sponsorlu bölümler kesiliyor...")
                    elif line.startswith("[download] Destination:"):
                        if cb.get("on_status"):
                            cb["on_status"]("İndiriliyor...")

                    # 2. İlerleme ayrıştırma
                    parsed = self._parse_progress(line, cb.get("on_progress"))

                    # 3. Akıllı Hata Teşhisi
                    diag = diagnose(line)
                    if diag:
                        if cb.get("on_log"):
                            cb["on_log"](f"💡 {diag['title']}: {diag['solution']}", "accent")

                    # 4. Log etiketi belirleme
                    tag = "info"
                    if "ERROR:" in line:
                        tag = "error"
                        error_message = line
                    elif "WARNING:" in line:
                        tag = "warn"
                    elif "[download] 100%" in line or "100% of" in line:
                        tag = "success"

                    is_progress_line = line.startswith("[PROGRESS]") or (parsed and bool(self._DL_RE.search(line)))
                    if cb.get("on_log") and not is_progress_line:
                        cb["on_log"](line, tag)

            if self._proc:
                self._proc.wait()
                rc = self._proc.returncode

        except FileNotFoundError as fnf:
            error_message = (
                "yt-dlp veya FFmpeg sistemde bulunamadı. "
                "Lütfen Ayarlar sekmesine giderek '⚡ Kur' butonu ile bileşenleri kurun."
            )
            if cb.get("on_log"):
                cb["on_log"](f"❌ {error_message}", "error")
        except Exception as ex:
            error_message = str(ex)
            if cb.get("on_log"):
                cb["on_log"](f"❌ Kritik Hata: {ex}", "error")

        finally:
            with self._lock:
                self._running = False
                cancelled = self._cancelled
                if self._proc and self._proc.stdout:
                    try:
                        self._proc.stdout.close()
                    except Exception:
                        pass
                self._proc = None

            success = (rc == 0 and not cancelled)
            if cb.get("on_complete"):
                cb["on_complete"](success, last_destination or self._current_file, error_message, cancelled)

    def _parse_progress(self, line, on_progress):
        if not on_progress:
            return False

        # Özel template kontrolü
        m = self._PROGRESS_RE.search(line)
        if m:
            try:
                pct = float(m.group("pct").strip())
                speed = m.group("speed").strip()
                total = m.group("total").strip()
                eta = m.group("eta").strip()

                speed = "—" if not speed or any(x in speed.lower() for x in ["unknown", "na", "—"]) else speed
                total = "—" if not total or any(x in total.lower() for x in ["unknown", "na", "—"]) else total
                eta = "—" if not eta or any(x in eta.lower() for x in ["unknown", "na", "—"]) or "" in eta else eta

                on_progress(pct, speed, total, eta)
                return True
            except Exception:
                pass

        # Standart yt-dlp ilerleme satırı
        m = self._DL_RE.search(line)
        if m:
            try:
                pct = float(m.group("pct"))
                total = m.group("total")
                speed = m.group("speed").strip()
                eta = m.group("eta").strip()
                on_progress(pct, speed, total, eta)
                return True
            except Exception:
                pass

        return False


def build_command(url, output_dir, options):
    """
    yt-dlp için tüm seçenekleri birleştirip komut listesini üretir.
    options alanları:
        - mode: "single" veya "playlist"
        - media_type: "video" veya "audio"
        - format: "mp4", "mkv", "webm", "mp3", "m4a", "flac", "wav" vb.
        - quality: "Best Quality (En İyi)" veya "1080p", "720p" / "320 kbps"
        - cookies_args: list
        - embed_subtitles: bool
        - subtitle_lang: str
        - embed_thumbnail: bool
        - add_metadata: bool
        - concurrent_fragments: int
        - playlist_start: str
        - playlist_end: str
        - ignore_errors: bool
        - speed_limit: str
        - proxy: str
    """
    ytdlp_cmd = get_ytdlp_cmd()
    cmd = list(ytdlp_cmd) + ["--newline"]

    # Yerel FFmpeg kontrolü
    ffmpeg_dir = get_ffmpeg_dir()
    if ffmpeg_dir:
        cmd += ["--ffmpeg-location", ffmpeg_dir]

    # Çerezler
    cookies_args = options.get("cookies_args") or []
    cmd.extend(cookies_args)

    media_type = options.get("media_type", "video")
    out_format = options.get("format", "mp4" if media_type == "video" else "mp3").lower()
    quality = options.get("quality", "Best Quality (En İyi)")

    # Video / Ses Formatı Seçimi
    if media_type == "video":
        if "Best" in quality:
            if out_format == "mp4":
                cmd += ["-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv+ba/b", "--merge-output-format", "mp4"]
            elif out_format == "mkv":
                cmd += ["-f", "bv*+ba/b", "--merge-output-format", "mkv"]
            elif out_format == "webm":
                cmd += ["-f", "bv*[ext=webm]+ba[ext=webm]/b[ext=webm]/bv+ba/b", "--merge-output-format", "webm"]
            else:
                cmd += ["-f", "bv*+ba/b", "--merge-output-format", out_format]
        else:
            height = re.search(r"\d+", quality)
            num_h = height.group(0) if height else "1080"
            if out_format == "mp4":
                cmd += [
                    "-f", f"bestvideo[height<={num_h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={num_h}]+bestaudio/best[height<={num_h}]",
                    "--merge-output-format", "mp4"
                ]
            else:
                cmd += [
                    "-f", f"bestvideo[height<={num_h}]+bestaudio/best[height<={num_h}]",
                    "--merge-output-format", out_format
                ]
    else:
        # Audio indirme
        cmd += ["-x", "--audio-format", out_format]
        if "Best" in quality:
            cmd += ["--audio-quality", "0"]
        else:
            bitrate = re.search(r"\d+", quality)
            num_b = bitrate.group(0) if bitrate else "320"
            cmd += ["--audio-quality", f"{num_b}k"]

    # Gelişmiş Seçenekler (Kapak resmi yalnızca desteklenen formatlarda gömülür)
    if options.get("embed_thumbnail", True) and out_format not in ("wav", "webm"):
        cmd.append("--embed-thumbnail")

    if options.get("add_metadata", True):
        cmd.append("--add-metadata")

    if options.get("embed_subtitles"):
        langs = options.get("subtitle_lang", "tr,en")
        cmd += ["--write-subs", "--write-auto-subs", "--sub-langs", langs, "--embed-subs"]

    try:
        concurrency = int(options.get("concurrent_fragments", 4))
    except (TypeError, ValueError) as ex:
        raise ValueError("Parça sayısı 1 ile 16 arasında bir tam sayı olmalıdır.") from ex
    if not 1 <= concurrency <= 16:
        raise ValueError("Parça sayısı 1 ile 16 arasında olmalıdır.")
    if concurrency > 1:
        cmd += ["--concurrent-fragments", str(concurrency)]

    if options.get("mode") == "playlist" and options.get("ignore_errors", True):
        cmd.append("--ignore-errors")

    speed_limit = options.get("speed_limit")
    if speed_limit:
        cmd += ["--limit-rate", speed_limit]

    proxy = options.get("proxy")
    if proxy:
        cmd += ["--proxy", proxy]

    # İndirme Arşivi (--download-archive)
    if options.get("use_download_archive"):
        archive_path = options.get("archive_file")
        if not archive_path:
            from core.config import get_data_dir
            archive_path = os.path.join(get_data_dir(), "archive.txt")
        cmd += ["--download-archive", archive_path]

    # SponsorBlock Entegrasyonu (--sponsorblock-remove)
    if options.get("sponsorblock_remove"):
        sb_cats = (options.get("sponsorblock_cats") or "sponsor,intro,outro").strip()
        if sb_cats:
            cmd += ["--sponsorblock-remove", sb_cats]

    # Bölüm Kesme / Zaman Aralığı İndirme (--download-sections)
    clip_section = clip_section_range(
        options.get("clip_start"),
        options.get("clip_end")
    )
    if clip_section:
        cmd += ["--download-sections", clip_section]

    safe_output_dir = os.path.abspath(output_dir or os.getcwd())

    # Playlist aralığı
    if options.get("mode") == "playlist":
        playlist_range = playlist_items_range(
            options.get("playlist_start"),
            options.get("playlist_end")
        )
        if playlist_range:
            cmd += ["--playlist-items", playlist_range]
        cmd.append("--yes-playlist")
        cmd += ["-o", os.path.join(safe_output_dir, "%(playlist_title)s", "%(playlist_index)s - %(title)s.%(ext)s")]
    else:
        cmd.append("--no-playlist")
        cmd += ["-o", os.path.join(safe_output_dir, "%(title)s.%(ext)s")]

    # Kararlı ilerleme şablonu ve nihai dosya yolu çıktısı
    # NOT: yt-dlp'de --print bayrağı varsayılan olarak --quiet ve --no-progress modunu tetikler.
    # Bu yüzden --progress ve --no-quiet açıkça eklenmelidir ki konsol ve ilerleme çubuğu çalışsın.
    # --progress-delta 0.15 ile ilerleme güncellemeleri optimize edilir, UI donması ve CPU aşırı yükü engellenir.
    cmd += [
        "--print",
        "after_move:[FINAL_PATH] %(filepath)s",
        "--progress",
        "--no-quiet",
        "--progress-delta",
        "0.15",
        "--progress-template",
        "download:[PROGRESS] %(progress._percent_str)s | %(progress._speed_str)s | %(progress._total_bytes_str)s | %(progress._eta_str)s"
    ]

    cmd.append(url)
    return cmd

engine = DownloadEngine()


_TIME_RE = re.compile(r"^(?:\d+:)?[0-5]?\d:[0-5]\d(?:\.\d+)?$|^\d+(?:\.\d+)?$")


def _parse_timestamp_seconds(ts: str) -> float:
    parts = ts.split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError("Geçersiz zaman formatı.")


def clip_section_range(start, end):
    """Zaman aralığını doğrular ve yt-dlp --download-sections değerini (*start-end) döndürür."""
    start = str(start or "").strip()
    end = str(end or "").strip()
    if not start and not end:
        return None
    if start and not _TIME_RE.match(start):
        raise ValueError("Başlangıç zamanı geçersiz (Örn: 01:20 veya 00:01:20 girin).")
    if end and end.lower() != "inf" and not _TIME_RE.match(end):
        raise ValueError("Bitiş zamanı geçersiz (Örn: 03:45 veya 00:03:45 girin).")

    s_sec = _parse_timestamp_seconds(start) if start else 0.0
    if end and end.lower() != "inf":
        e_sec = _parse_timestamp_seconds(end)
        if e_sec <= s_sec:
            raise ValueError("Klip bitiş zamanı başlangıç zamanından büyük olmalıdır.")

    return f"*{start or '00:00'}-{end or 'inf'}"


def playlist_items_range(start, end):
    """Validate playlist indexes and return yt-dlp's playlist-items value."""
    start = str(start or "").strip()
    end = str(end or "").strip()
    if start and not start.isdigit():
        raise ValueError("Başlangıç sırası pozitif bir tam sayı olmalıdır.")
    if end and not end.isdigit():
        raise ValueError("Bitiş sırası pozitif bir tam sayı olmalıdır.")
    if start and int(start) < 1:
        raise ValueError("Başlangıç sırası en az 1 olmalıdır.")
    if end and int(end) < 1:
        raise ValueError("Bitiş sırası en az 1 olmalıdır.")
    if start and end and int(end) < int(start):
        raise ValueError("Bitiş sırası başlangıç sırasından küçük olamaz.")
    if start or end:
        return f"{start or '1'}:{end}"
    return None

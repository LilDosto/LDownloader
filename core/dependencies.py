import os
import sys
import shutil
import zipfile
import subprocess
import configparser
import requests
import time
from core.config import get_bin_dir, get_app_dir, get_data_dir

# bin/ dizinini çalışma zamanı PATH değişkeninin başına ekle
_bin_dir = get_bin_dir()
if _bin_dir and _bin_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{_bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

def get_ytdlp_cmd():
    """yt-dlp çalıştırma komutunu liste olarak döndürür (exe veya python -m yt_dlp)."""
    exe = find_executable("yt-dlp")
    if exe:
        return [exe]
    if not getattr(sys, "frozen", False):
        try:
            import yt_dlp  # noqa: F401
            return [sys.executable, "-m", "yt_dlp"]
        except ImportError:
            pass
    return ["yt-dlp"]

def find_executable(name: str):
    """Belirtilen çalıştırılabilir dosyayı bin/ klasöründe veya PATH'te arar."""
    exe_name = f"{name}.exe" if sys.platform == "win32" else name

    # 1. User AppData bin dizinini kontrol et
    user_bin = os.path.join(get_data_dir(), "bin", exe_name)
    if os.path.isfile(user_bin) and os.access(user_bin, os.X_OK):
        return user_bin

    # 2. Local / Aktif bin dizinini kontrol et
    bin_dir = get_bin_dir()
    local_path = os.path.join(bin_dir, exe_name)
    if os.path.isfile(local_path) and os.access(local_path, os.X_OK):
        return local_path

    # 3. PyInstaller _MEIPASS veya app dizinindeki bin klasörü
    app_bin = os.path.join(get_app_dir(), "bin", exe_name)
    if os.path.isfile(app_bin):
        return app_bin

    # 4. Python Scripts dizini kontrolü (örn: yt-dlp pip ile kurulmuşsa)
    python_dir = os.path.dirname(sys.executable)
    py_script = os.path.join(python_dir, "Scripts", exe_name)
    if os.path.isfile(py_script):
        return py_script

    # 5. Windows Programs Python Scripts kontrolü
    if sys.platform == "win32":
        local_appdata = os.getenv("LOCALAPPDATA", "")
        py_programs = os.path.join(local_appdata, "Programs", "Python")
        if os.path.isdir(py_programs):
            for entry in os.listdir(py_programs):
                candidate = os.path.join(py_programs, entry, "Scripts", exe_name)
                if os.path.isfile(candidate):
                    return candidate

    # 6. Sistem PATH kontrolü
    return shutil.which(name)


def get_ytdlp_status():
    """yt-dlp durumunu (kurulu_mu, versiyon, yol) döndürür."""
    exe = find_executable("yt-dlp")
    if not exe:
        # pip modülü veya PyInstaller gömülü modül kontrolü
        try:
            import yt_dlp
            import yt_dlp.version
            ver = getattr(yt_dlp.version, "__version__", "Gömülü")
            return True, str(ver), "embedded"
        except Exception:
            return False, "Bulunamadı", None

    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        out = subprocess.check_output([exe, "--version"], text=True, stderr=subprocess.STDOUT, creationflags=flags)
        return True, out.strip(), exe
    except Exception:
        return True, "Mevcut", exe


def get_ffmpeg_status():
    """ffmpeg durumunu (kurulu_mu, versiyon, yol) döndürür."""
    exe = find_executable("ffmpeg")
    if not exe:
        return False, "Bulunamadı", None
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        out = subprocess.check_output([exe, "-version"], text=True, stderr=subprocess.STDOUT, creationflags=flags)
        first_line = out.splitlines()[0] if out else "Mevcut"
        return True, first_line[:30], exe
    except Exception:
        return True, "Mevcut", exe


def get_js_status():
    """YouTube n-challenge/EJS için JS motoru durumunu döndürür."""
    for js in ("deno", "node", "qjs"):
        exe = find_executable(js)
        if exe:
            return True, f"Hazır ({js.capitalize()})", exe
    return False, "Bulunamadı", None


def get_ffmpeg_dir():
    """Eğer ffmpeg yerel bin dizinindeyse dizin yolunu döndürür (--ffmpeg-location için)."""
    exe = find_executable("ffmpeg")
    if exe:
        return os.path.dirname(exe)
    return None


def install_deno(progress_callback=None):
    """YouTube EJS challenge çözümleri için resmi Deno motorunu indirir."""
    bin_dir = get_bin_dir()
    os.makedirs(bin_dir, exist_ok=True)
    zip_path = os.path.join(bin_dir, "deno_download.zip")
    url = "https://github.com/denoland/deno/releases/download/v2.9.6/deno-x86_64-pc-windows-msvc.zip"
    download_file_with_progress(url, zip_path, progress_callback)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extract("deno.exe", bin_dir)
    try:
        os.remove(zip_path)
    except Exception:
        pass
    return os.path.join(bin_dir, "deno.exe")


def download_file_with_progress(url: str, dest_path: str, progress_callback=None):
    """URL'den dosyayı indirir ve ilerlemeyi bildirir."""
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    total_length = response.headers.get('content-length')

    downloaded = 0
    total = int(total_length) if total_length else None
    last_callback_time = 0.0

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total:
                    now = time.monotonic()
                    pct = (downloaded / total) * 100
                    if (now - last_callback_time >= 0.08) or pct >= 100:
                        last_callback_time = now
                        progress_callback(pct, downloaded, total)


def install_ytdlp(progress_callback=None):
    """Resmi GitHub yayınından en güncel yt-dlp.exe dosyasını indirir."""
    bin_dir = get_bin_dir()
    os.makedirs(bin_dir, exist_ok=True)
    target = os.path.join(bin_dir, "yt-dlp.exe")
    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

    temp_target = target + ".tmp"
    download_file_with_progress(url, temp_target, progress_callback)
    if os.path.exists(target):
        try:
            os.remove(target)
        except Exception:
            pass
    shutil.move(temp_target, target)
    return target


def install_ffmpeg(progress_callback=None):
    """yt-dlp tarafından resmi olarak önerilen taşınabilir FFmpeg yapısını indirip ayıklar."""
    bin_dir = get_bin_dir()
    os.makedirs(bin_dir, exist_ok=True)
    zip_path = os.path.join(bin_dir, "ffmpeg_download.zip")

    # yt-dlp resmi FFmpeg win64 yapısı (gpl)
    url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

    download_file_with_progress(url, zip_path, progress_callback)

    # Ayıkla ve ffmpeg.exe ile ffprobe.exe'yi bin_dir içine taşı
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            filename = os.path.basename(member)
            if filename in ("ffmpeg.exe", "ffprobe.exe"):
                source = zf.open(member)
                target_path = os.path.join(bin_dir, filename)
                with open(target_path, "wb") as target_file:
                    shutil.copyfileobj(source, target_file)

    try:
        os.remove(zip_path)
    except Exception:
        pass

    return os.path.join(bin_dir, "ffmpeg.exe")


def _find_zen_profile() -> str | None:
    """Zen Browser için aktif Firefox tabanlı profil klasörünü bulur."""
    appdata = os.getenv("APPDATA", "")
    zen_root = os.path.join(appdata, "Zen")
    profiles_ini = os.path.join(zen_root, "profiles.ini")
    if os.path.isfile(profiles_ini):
        try:
            cp = configparser.ConfigParser()
            cp.read(profiles_ini, encoding="utf-8")
            for section in cp.sections():
                if section.startswith("Install") and cp.has_option(section, "Default"):
                    rel = cp.get(section, "Default")
                    cand = os.path.normpath(os.path.join(zen_root, rel))
                    if os.path.isdir(cand):
                        return cand
            for section in cp.sections():
                if cp.has_option(section, "Path"):
                    p = cp.get(section, "Path")
                    is_rel = cp.get(section, "IsRelative", fallback="1") == "1"
                    cand = os.path.normpath(os.path.join(zen_root, p) if is_rel else p)
                    if os.path.isdir(cand) and (cp.get(section, "Default", fallback="0") == "1" or "default" in p.lower()):
                        return cand
        except Exception:
            pass

    zen_profiles = os.path.join(zen_root, "Profiles")
    if os.path.isdir(zen_profiles):
        folders = [os.path.join(zen_profiles, f) for f in os.listdir(zen_profiles) if os.path.isdir(os.path.join(zen_profiles, f))]
        for folder in folders:
            if "default-release" in os.path.basename(folder).lower() or "default" in os.path.basename(folder).lower():
                if os.path.isfile(os.path.join(folder, "cookies.sqlite")):
                    return folder
        for folder in folders:
            if os.path.isfile(os.path.join(folder, "cookies.sqlite")):
                return folder
        if folders:
            return folders[0]
    return None


def resolve_cookies_args(mode: str, browser: str = "firefox", cookies_file: str = ""):
    """Çerez parametrelerini akıllıca çözer. Zen Browser için Firefox profilini bulur."""
    if not mode or mode in ("none", "off", "kapali", "kapalı"):
        return []

    if mode == "file":
        if cookies_file and cookies_file != "Seçilmedi" and os.path.isfile(cookies_file):
            return ["--cookies", cookies_file]
        raise FileNotFoundError(
            "Seçilen cookies.txt dosyası bulunamadı. Ayarlar bölümünden geçerli bir dosya seçin veya çerez kullanımını kapatın."
        )

    if mode == "browser":
        b = (browser or "").lower().strip()
        if b == "zen":
            profile_path = _find_zen_profile()
            if profile_path:
                return ["--cookies-from-browser", f"firefox:{profile_path}"]
            return ["--cookies-from-browser", "firefox"]

        return ["--cookies-from-browser", b]

    return []


def test_browser_cookies(browser_name: str):
    """Belirtilen tarayıcıdan çerez çekilip çekilemediğini test eder."""
    args = resolve_cookies_args("browser", browser_name)
    if not args:
        return False, "Geçersiz çerez parametresi"

    cmd = get_ytdlp_cmd() + args + ["--simulate", "--no-warnings", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=flags, timeout=15)
        if proc.returncode == 0:
            return True, f"✅ {browser_name.capitalize()} çerezleri başarıyla okundu!"

        err = proc.stderr.lower()
        if "failed to decrypt with dpapi" in err or "dpapi" in err or "appbound" in err:
            return False, (
                f"⚠️ {browser_name.capitalize()}: Windows DPAPI / App-Bound güvenlik koruması nedeniyle doğrudan çerez okunamadı. "
                f"Çözüm: Firefox/Zen kullanın veya çerezleri 'cookies.txt' eklentisiyle dışa aktarıp 'cookies.txt' modunda yükleyin."
            )
        if "could not copy" in err or "database" in err or "locked" in err:
            return False, f"⚠️ {browser_name.capitalize()} şu an açık olduğu için Windows dosyayı kilitliyor. Tarayıcıyı kapatıp tekrar deneyin."
        if "could not find" in err:
            return False, f"⚠️ {browser_name.capitalize()} çerez veritabanı bulunamadı. Bu tarayıcının sisteminizde yüklü olduğundan emin olun."
        return False, f"Hata: {proc.stderr.strip()[:180]}"
    except Exception as ex:
        return False, str(ex)

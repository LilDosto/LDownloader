import os
import sys
import shutil
import zipfile
import subprocess
import requests
from core.config import get_bin_dir, get_app_dir

# bin/ dizinini çalışma zamanı PATH değişkeninin başına ekle
_bin_dir = get_bin_dir()
if _bin_dir and _bin_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{_bin_dir};{os.environ.get('PATH', '')}"

def find_executable(name: str):
    """Belirtilen çalıştırılabilir dosyayı bin/ klasöründe veya PATH'te arar."""
    # 1. Local / User bin dizinini kontrol et
    bin_dir = get_bin_dir()
    local_path = os.path.join(bin_dir, f"{name}.exe" if sys.platform == "win32" else name)
    if os.path.isfile(local_path) and os.access(local_path, os.X_OK):
        return local_path

    # 2. PyInstaller _MEIPASS veya app dizinindeki bin klasörü
    app_bin = os.path.join(get_app_dir(), "bin", f"{name}.exe" if sys.platform == "win32" else name)
    if os.path.isfile(app_bin):
        return app_bin

    # 3. Python Scripts dizini kontrolü (örn: yt-dlp pip ile kurulmuşsa)
    python_dir = os.path.dirname(sys.executable)
    py_script = os.path.join(python_dir, "Scripts", f"{name}.exe" if sys.platform == "win32" else name)
    if os.path.isfile(py_script):
        return py_script

    # 4. Windows Programs Python Scripts kontrolü
    if sys.platform == "win32":
        local_appdata = os.getenv("LOCALAPPDATA", "")
        py_programs = os.path.join(local_appdata, "Programs", "Python")
        if os.path.isdir(py_programs):
            for entry in os.listdir(py_programs):
                candidate = os.path.join(py_programs, entry, "Scripts", f"{name}.exe")
                if os.path.isfile(candidate):
                    return candidate

    # 5. Sistem PATH kontrolü
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

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total:
                    pct = (downloaded / total) * 100
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


def resolve_cookies_args(mode: str, browser: str = "firefox", cookies_file: str = ""):
    """Çerez parametrelerini akıllıca çözer. Zen Browser için Firefox profilini bulur."""
    if not mode or mode in ("none", "off", "kapali", "kapalı"):
        return []

    if mode == "file":
        if cookies_file and os.path.isfile(cookies_file):
            return ["--cookies", cookies_file]
        raise FileNotFoundError(
            "Seçilen cookies.txt dosyası bulunamadı. Ayarlar bölümünden geçerli bir dosya seçin veya çerez kullanımını kapatın."
        )

    if mode == "browser":
        b = (browser or "").lower().strip()
        if b == "zen":
            # Zen Browser Firefox tabanlıdır, profil klasörünü bul
            appdata = os.getenv("APPDATA", "")
            zen_profiles = os.path.join(appdata, "Zen", "Profiles")
            if os.path.exists(zen_profiles):
                for folder in os.listdir(zen_profiles):
                    if "default" in folder.lower():
                        profile_path = os.path.join(zen_profiles, folder)
                        return ["--cookies-from-browser", f"firefox:{profile_path}"]
            return ["--cookies-from-browser", "firefox"]

        return ["--cookies-from-browser", b]

    return []


def test_browser_cookies(browser_name: str):
    """Belirtilen tarayıcıdan çerez çekilip çekilemediğini test eder."""
    args = resolve_cookies_args("browser", browser_name)
    if not args:
        return False, "Geçersiz çerez parametresi"

    exe = find_executable("yt-dlp") or "yt-dlp"
    cmd = [exe] + args + ["--simulate", "--no-warnings", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=flags, timeout=12)
        if proc.returncode == 0:
            return True, f"✅ {browser_name.capitalize()} çerezleri başarıyla okundu!"

        err = proc.stderr.lower()
        if "failed to decrypt with dpapi" in err or "dpapi" in err:
            return False, (
                f"⚠️ {browser_name.capitalize()}: Windows DPAPI güvenlik koruması nedeniyle doğrudan çerez okunamadı. "
                f"Çözüm: Çerezleri 'cookies.txt' eklentisiyle dışa aktarıp 'cookies.txt' modunda kullanın."
            )
        if "could not copy" in err or "database" in err:
            return False, f"⚠️ {browser_name.capitalize()} şu an açık olduğu için Windows dosyayı kilitliyor. Tarayıcıyı kapatıp tekrar deneyin."
        if "could not find" in err:
            return False, f"⚠️ {browser_name.capitalize()} çerez veritabanı bulunamadı. Bu tarayıcının sisteminizde yüklü olduğundan emin olun."
        return False, f"Hata: {proc.stderr[:150]}"
    except Exception as ex:
        return False, str(ex)

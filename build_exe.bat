@echo off
chcp 65001 >nul
echo ===================================================
echo   LDownloader v3.3.0 - Windows EXE & Kurulum Sihirbazi
echo ===================================================
echo.

python -m PyInstaller --noconfirm ytdlp_indirici.spec
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Derleme basarisiz oldu. PyInstaller kurulu oldugundan emin olun:
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
if exist build rmdir /s /q build
echo [BASARILI] dist\LDownloader.exe basariyla olusturuldu!

set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if exist "%ISCC_PATH%" (
    echo.
    echo Kurulum Sihirbazi (Setup.exe) derleniyor...
    "%ISCC_PATH%" installer.iss
    if %ERRORLEVEL% EQU 0 (
        echo [BASARILI] Kurulum dosyasi dist\LDownloader-v3.3.0-Setup.exe olusturuldu!
    )
)

echo.
echo Islem tamamlandi!
pause

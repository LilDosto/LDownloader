@echo off
chcp 65001 >nul
echo ===================================================
echo   LDownloader v3 - Windows EXE Derleme Araci
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
pause

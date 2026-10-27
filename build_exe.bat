@echo off
chcp 65001 > nul
echo ========================================================
echo       LDownloader v2.0 - PyInstaller Derleme Araci
echo ========================================================
echo.

python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [HATA] Bagimliliklar yuklenemedi!
    pause
    exit /b 1
)

echo.
echo [*] EXE paketi olusturuluyor...
pyinstaller --noconfirm ytdlp_indirici.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo [BASARILI] Derleme tamamlandi!
    echo Calistirilabilir dosya: dist\LDownloader.exe
    echo ========================================================
) else (
    echo.
    echo [HATA] PyInstaller derleme sirasinda hata olustu!
)

pause

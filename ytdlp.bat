@echo off
title yt-dlp Hizli Indirici
chcp 65001 >nul

:start
cls
echo.
echo ==========================================
echo       yt-dlp Video/Ses Indirici
echo ==========================================
echo.

set /p url="Indirilecek linki yapistirin: "

if "%url%"=="" (
    echo Link bos olamaz!
    pause
    goto start
)

echo.
echo [1] Video Olarak Indir (En yuksek kalite + mp4)
echo [2] Ses (MP3) Olarak Indir
echo [3] Cikis
echo.

set /p secim="Seciminizi yapin (1/2/3): "

if "%secim%"=="1" goto video
if "%secim%"=="2" goto audio
if "%secim%"=="3" exit
goto start

:video
echo.
echo Video indiriliyor...
yt-dlp -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv+ba/b" --merge-output-format mp4 "%url%"
goto end

:audio
echo.
echo Ses dosyasi (MP3) hazirlaniyor...
yt-dlp -x --audio-format mp3 --audio-quality 0 "%url%"
goto end

:end
echo.
echo Islem tamamlandi!
echo.
pause
goto start
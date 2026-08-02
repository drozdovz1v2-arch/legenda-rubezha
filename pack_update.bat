@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "OUT=updates\packages"
set "ZIP=%OUT%\LegendaRubezha_beta_0.0.0.2.zip"

if not exist "dist\LegendaRubezha\LegendaRubezha.exe" (
  echo Сначала собери игру: pyinstaller --noconfirm LegendaRubezha.spec
  pause
  exit /b 1
)

if not exist "%OUT%" mkdir "%OUT%"

echo Упаковка обновления...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\LegendaRubezha\*' -DestinationPath '%ZIP%' -Force"

echo.
echo Готово: %ZIP%
echo.
echo 1. Загрузи zip на хостинг ^(GitHub Releases, Google Drive, свой сервер^)
echo 2. Укажи download_url и sha256 в updates\manifest.json
echo.
powershell -NoProfile -Command "(Get-FileHash '%ZIP%' -Algorithm SHA256).Hash.ToLower()"
pause

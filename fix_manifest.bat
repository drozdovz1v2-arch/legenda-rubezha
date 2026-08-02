@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "MANIFEST=%~dp0updates\manifest.json"
set "URL=https://raw.githubusercontent.com/drozdovz1v2-arch/legenda-rubezha/main/updates/manifest.json"

echo Скачиваем свежий manifest.json...
powershell -NoProfile -Command ^
  "$ProgressPreference='SilentlyContinue';" ^
  "Invoke-WebRequest -Uri '%URL%' -OutFile '%MANIFEST%' -UseBasicParsing"

if errorlevel 1 (
  echo Ошибка загрузки.
  pause
  exit /b 1
)

echo Готово: %MANIFEST%
echo.
echo Теперь открой лаунчер - Проверить обновления - Обновить
pause

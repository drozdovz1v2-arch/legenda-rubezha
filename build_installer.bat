@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Сборка игры ===
pyinstaller --noconfirm LegendaRubezha.spec
if errorlevel 1 goto :fail

echo.
echo === Сборка лаунчера ===
pyinstaller --noconfirm LegendaRubezhaLauncher.spec
if errorlevel 1 goto :fail

echo.
echo === Сборка установщика ===
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
  echo Inno Setup не найден. Установите: winget install JRSoftware.InnoSetup
  goto :fail
)

"%ISCC%" installer.iss
if errorlevel 1 goto :fail

echo.
echo Готово!
echo   installer\LegendaRubezha_Setup_beta_0.0.0.4.exe
echo   dist\LegendaRubezhaLauncher\LegendaRubezhaLauncher.exe
echo.
echo Для автообновлений:
echo   1. pack_update.bat — упаковать zip
echo   2. Залить manifest.json + zip на хостинг
echo   3. Указать URL в updates\launcher_config.json
goto :end

:fail
echo.
echo Ошибка сборки.
pause
exit /b 1

:end
pause

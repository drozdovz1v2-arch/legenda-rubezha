@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "VER=0.0.0.4"
set "STAGE=dist\friend_package"
set "OUT=updates\packages\LegendaRubezha_FriendSetup_%VER%.zip"

if not exist "dist\LegendaRubezha\LegendaRubezha.exe" (
  echo Сначала собери игру и лаунчер:
  echo   pyinstaller --noconfirm LegendaRubezha.spec
  echo   pyinstaller --noconfirm LegendaRubezhaLauncher.spec
  pause
  exit /b 1
)

if not exist "dist\LegendaRubezhaLauncher\LegendaRubezhaLauncher.exe" (
  echo Нет dist\LegendaRubezhaLauncher\LegendaRubezhaLauncher.exe — собери лаунчер.
  pause
  exit /b 1
)

echo Сборка пакета для друга...
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%"
mkdir "%STAGE%\updates"
mkdir "%STAGE%\Launcher"

xcopy /E /I /Y "dist\LegendaRubezha\*" "%STAGE%\"
xcopy /E /I /Y "dist\LegendaRubezhaLauncher\*" "%STAGE%\Launcher\"
copy /Y "updates\launcher_config.json" "%STAGE%\"
copy /Y "updates\version.json" "%STAGE%\"
copy /Y "updates\manifest.json" "%STAGE%\updates\"
copy /Y "updates\github_repo.json" "%STAGE%\updates\"
copy /Y "updates\КАК_УСТАНОВИТЬ.txt" "%STAGE%\"

if not exist "updates\packages" mkdir "updates\packages"
powershell -NoProfile -Command "Compress-Archive -Path '%STAGE%\*' -DestinationPath '%OUT%' -Force"

echo.
echo Готово! Отправь другу ОДИН файл:
echo   %OUT%
echo.
echo Друг: распаковать - открыть Launcher\LegendaRubezhaLauncher.exe - Играть
pause

@echo off
chcp 65001 >nul
cd /d "%~dp0"
pyinstaller --noconfirm LegendaRubezhaLauncher.spec
if errorlevel 1 pause & exit /b 1
echo Готово: dist\LegendaRubezhaLauncher\LegendaRubezhaLauncher.exe
pause

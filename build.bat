@echo off
cd /d "%~dp0"
pyinstaller --noconfirm LegendaRubezha.spec
echo.
echo Готово: dist\LegendaRubezha\LegendaRubezha.exe
pause

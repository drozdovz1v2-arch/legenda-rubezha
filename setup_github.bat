@echo off
chcp 65001 >nul
cd /d "%~dp0"

if "%~1"=="" (
  echo.
  echo Использование:
  echo   setup_github.bat ВАШ_GITHUB_ЛОГИН [имя_репо]
  echo.
  echo Пример:
  echo   setup_github.bat drozd legenda-rubezha
  echo.
  pause
  exit /b 1
)

set "REPO=%~2"
if "%REPO%"=="" set "REPO=legenda-rubezha"

python setup_github.py %~1 %REPO%
pause

@echo off
chcp 65001 >nul
cd /d "%~dp0"

if "%~1"=="" (
  echo Сначала: setup_github.bat ВАШ_ЛОГИН
  pause
  exit /b 1
)

echo === Git: первый push на GitHub ===
if not exist .git (
  git init
  git branch -M main
)

git add .
git status
echo.
set /p OK=Коммитить все файлы? (Y/N): 
if /I not "%OK%"=="Y" exit /b 0

git commit -m "Legenda Rubezha beta 0.0.0.2 — игра, лаунчер, автообновления"

echo.
echo Если репозиторий ещё не создан:
echo   gh repo create %~2 --public --source=. --remote=origin --push
echo.
echo Если репозиторий уже есть:
echo   git remote add origin https://github.com/%~1/%~2.git
echo   git push -u origin main
echo.
echo Первый релиз (сборка в GitHub Actions):
echo   git tag v0.0.0.2
echo   git push origin v0.0.0.2
echo.
pause

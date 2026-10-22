@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [BadgeFarmer 24/7] Отключение автозапуска...
powershell -Command "Remove-Item \"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\BadgeFarmer247.lnk\" -Force -ErrorAction SilentlyContinue"
echo Автозапуск удален.
pause

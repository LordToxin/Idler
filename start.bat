@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [BadgeFarmer 24/7] Запуск в фоновом режиме...
cscript //nologo start_silent.vbs
timeout /t 2 >nul
python status.py
pause

@echo off
chcp 65001 >nul
cd /d "%~dp0"
python status.py
pause

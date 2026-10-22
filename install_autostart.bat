@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [BadgeFarmer 24/7] Установка автозапуска при старте Windows...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\BadgeFarmer247.lnk\"); $sc.TargetPath = 'wscript.exe'; $sc.Arguments = '\"%~dp0start_silent.vbs\"'; $sc.WorkingDirectory = '%~dp0'; $sc.Description = 'BadgeFarmer 24/7 Autostart'; $sc.Save()"
echo Автозапуск успешно настроен! При каждом включении компьютера фармер будет крутить игры в фоне 24/7.
pause

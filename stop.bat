@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [BadgeFarmer 24/7] Остановка...
python -c "
import os, json, subprocess

base = r'%~dp0'
state_file = os.path.join(base, 'state.json')
lock_file = os.path.join(base, 'farmer.lock')

if os.path.exists(lock_file):
    try:
        with open(lock_file) as f:
            pid = int(f.read().strip())
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(lock_file)
        print(f'Фармер (PID {pid}) остановлен.')
    except Exception as e:
        print(f'Ошибка остановки: {e}')

if os.path.exists(state_file):
    try:
        with open(state_file) as f:
            st = json.load(f)
        c_pid = st.get('current_pid')
        if c_pid:
            subprocess.run(['taskkill', '/F', '/PID', str(c_pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        st['running'] = False
        st['current_pid'] = None
        st['current_game'] = None
        with open(state_file, 'w') as f:
            json.dump(st, f, indent=2)
    except Exception:
        pass
"
echo Фармер полностью остановлен.
pause

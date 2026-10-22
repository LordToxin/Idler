import os
import sys
import json
import subprocess

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")
LOCK_FILE = os.path.join(BASE_DIR, "farmer.lock")

MUTEX_NAME = "Local\\BadgeFarmer247_SingleInstance_Mutex"

def is_running():
    import ctypes
    ERROR_ALREADY_EXISTS = 183
    m = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    is_alive = (ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS)
    if m:
        ctypes.windll.kernel32.CloseHandle(m)
    pid = None
    if is_alive and os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
        except Exception:
            pass
    return is_alive, pid

def print_dashboard():
    running, pid = is_running()
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    print("=" * 65)
    print("           BADGE FARMER 24/7 — СТАТУС И ПРОГРЕСС")
    print("=" * 65)

    if running:
        print(f"  ● СТАТУС:          \033[92mАКТИВЕН И РАБОТАЕТ 24/7\033[0m (PID: {pid})")
    else:
        print(f"  ○ СТАТУС:          \033[91mОСТАНОВЛЕН\033[0m")

    mode = state.get("mode", "variety").upper()
    print(f"  ● ТЕКУЩИЙ РЕЖИМ:   {mode}")

    cur_game = state.get("current_game")
    if cur_game and running:
        print(f"  ● АКТИВНАЯ ИГРА:   \033[96m{cur_game.get('name')}\033[0m ({cur_game.get('exe')})")
    else:
        print(f"  ● АКТИВНАЯ ИГРА:   Нет")

    # Variety progress
    unique = state.get("unique_games_farmed", [])
    target = state.get("variety_target", 100)
    count = len(unique)
    pct = min(100, int((count / target) * 100)) if target else 0
    filled = int(pct / 5)
    bar = "█" * filled + "░" * (20 - filled)

    print("-" * 65)
    print(f"  [1] Game Variety Badge (100 уникальных игр):")
    print(f"      Прогресс: [{bar}] {pct}% ({count}/{target})")
    if count >= target:
        print("      \033[92m✔ Бейдж готов к получению (100+ игр зарегистрировано)!\033[0m")
    else:
        rem_min = int(((target - count) * state.get("rotation_interval", 80)) / 60)
        print(f"      Осталось накрутить: {target - count} игр (~{rem_min} минут)")

    # Game Time progress
    total_sec = state.get("total_farmed_seconds", 0)
    total_hours = round(total_sec / 3600, 1)
    print("-" * 65)
    print(f"  [2] Game Time Badge (Часы в играх 24/7):")
    print(f"      Всего накручено: \033[93m{total_hours} ч.\033[0m ({total_sec // 60} мин.)")
    print(f"      Основная игра 24/7: {state.get('gametime_main_name', 'Dota 2')}")

    print("=" * 65)
    print("  Управление:")
    print("    start.bat           — Запустить в скрытом режиме 24/7")
    print("    stop.bat            — Остановить фармер")
    print("    install_autostart.bat — Включить автозапуск при старте Windows")
    print("=" * 65)

if __name__ == "__main__":
    print_dashboard()

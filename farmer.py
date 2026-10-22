import os
import sys
import time
import json
import shutil
import signal
import threading
import subprocess
from datetime import datetime

import ctypes
from PIL import Image, ImageDraw
import pystray
from pypresence import Presence

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")
GAMES_FILE = os.path.join(BASE_DIR, "games.json")
LOG_FILE = os.path.join(BASE_DIR, "farmer.log")
LOCK_FILE = os.path.join(BASE_DIR, "farmer.lock")
DUMMY_RUNNER = os.path.join(BASE_DIR, "dummy_runner.exe")
GAMES_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "BadgeFarmerGames")

os.makedirs(GAMES_DIR, exist_ok=True)

MUTEX_NAME = "Local\\BadgeFarmer247_SingleInstance_Mutex"
_mutex = None

def check_single_instance():
    global _mutex
    ERROR_ALREADY_EXISTS = 183
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        sys.exit(0)
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    if sys.stdout is not None:
        try:
            print(line)
        except Exception:
            pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_games():
    try:
        with open(GAMES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading games.json: {e}")
        return []

def load_state():
    default_state = {
        "mode": "variety",              # "variety" or "gametime"
        "rotation_interval": 80,
        "current_game_index": 0,
        "current_game": None,
        "current_pid": None,
        "unique_games_farmed": [],
        "total_farmed_seconds": 0,
        "variety_target": 100,
        "gametime_main_game": "dota2.exe",
        "gametime_main_name": "Dota 2",
        "gametime_main_id": "356875988589740042",
        "running": True,
        "paused": False,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_state.update(data)
                default_state["running"] = True
                return default_state
        except Exception as e:
            log(f"Error reading state.json: {e}")
    return default_state

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Error saving state.json: {e}")

# Global references
running_flag = True
state = load_state()
rpc_instance = None
current_process = None
tray_icon = None
skip_requested = False

def set_discord_rpc(client_id: str, game_name: str, details_text: str):
    global rpc_instance
    if rpc_instance:
        try:
            rpc_instance.close()
        except Exception:
            pass
        rpc_instance = None

    try:
        rpc = Presence(client_id)
        rpc.connect()
        rpc.update(
            state=game_name,
            details=details_text,
            start=int(time.time()),
            large_text=game_name
        )
        rpc_instance = rpc
        log(f"[Discord RPC] Active game set to: {game_name} ({client_id})")
        return True
    except Exception as e:
        log(f"[Discord RPC] Note: Discord IPC connect: {e}")
        return False

def close_discord_rpc():
    global rpc_instance
    if rpc_instance:
        try:
            rpc_instance.close()
        except Exception:
            pass
        rpc_instance = None

def kill_current_game():
    global current_process
    close_discord_rpc()
    if current_process:
        try:
            current_process.terminate()
            current_process.wait(timeout=2)
        except Exception:
            try:
                current_process.kill()
            except Exception:
                pass
        current_process = None

    if state.get("current_pid"):
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(state["current_pid"])],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=0x08000000)
        except Exception:
            pass
        state["current_pid"] = None

def spawn_game(exe_name: str):
    global current_process
    dest_exe = os.path.join(GAMES_DIR, exe_name)
    try:
        shutil.copyfile(DUMMY_RUNNER, dest_exe)
    except Exception as e:
        log(f"Failed to copy dummy runner to {dest_exe}: {e}")
        return None

    try:
        flags = 0x08000000 # CREATE_NO_WINDOW
        proc = subprocess.Popen([dest_exe], creationflags=flags)
        current_process = proc
        return proc.pid
    except Exception as e:
        log(f"Failed to spawn {exe_name}: {e}")
        return None

def update_tray_ui():
    global tray_icon
    if not tray_icon:
        return

    cur_game = state.get("current_game")
    game_title = cur_game.get("name") if cur_game else "Ожидание..."
    count = len(state.get("unique_games_farmed", []))
    target = state.get("variety_target", 100)
    hours = round(state.get("total_farmed_seconds", 0) / 3600, 1)
    status_text = "ПАУЗА" if state.get("paused") else "АКТИВЕН 24/7"

    # Tooltip on hover (near Wi-Fi)
    tooltip = f"BadgeFarmer 24/7 ({status_text})\nИгра: {game_title}\nПрогресс: {count}/{target} ({hours}ч)"
    try:
        tray_icon.title = tooltip[:127] # Windows limit
    except Exception:
        pass

def farmer_worker():
    global running_flag, skip_requested
    games = load_games()
    last_save_time = time.time()

    log("=" * 60)
    log("BadgeFarmer 24/7 Worker Loop Started")

    while running_flag:
        if state.get("paused"):
            time.sleep(1)
            continue

        mode = state.get("mode", "variety")

        # --- VARIETY ROTATION ---
        if mode == "variety":
            farmed_set = set(state.get("unique_games_farmed", []))
            target = state.get("variety_target", 100)

            if len(farmed_set) >= target:
                log(">>> Variety Goal Reached (100 Unique Games logged)! <<<")
                log(f">>> Switching to 24/7 Game Time farming on: {state.get('gametime_main_name', 'Dota 2')} <<<")
                state["mode"] = "gametime"
                save_state(state)
                update_tray_ui()
                continue

            candidate_game = None
            for g in games:
                if g["exe"] not in farmed_set:
                    candidate_game = g
                    break

            if not candidate_game:
                state["mode"] = "gametime"
                save_state(state)
                continue

            kill_current_game()

            exe_name = candidate_game["exe"]
            game_name = candidate_game["name"]
            game_id = candidate_game.get("id", "356875988589740042")

            pid = spawn_game(exe_name)
            count = len(farmed_set) + 1
            set_discord_rpc(game_id, game_name, f"Game Variety ({count}/{target})")

            state["current_game"] = candidate_game
            state["current_pid"] = pid
            state["unique_games_farmed"].append(exe_name)
            save_state(state)
            update_tray_ui()

            log(f"[{count}/{target}] Now farming: {game_name} ({exe_name}) | PID: {pid}")

            interval = state.get("rotation_interval", 80)
            elapsed = 0
            skip_requested = False
            while elapsed < interval and running_flag and not skip_requested:
                if not state.get("paused"):
                    time.sleep(1)
                    elapsed += 1
                    state["total_farmed_seconds"] += 1
                    if time.time() - last_save_time > 30:
                        save_state(state)
                        update_tray_ui()
                        last_save_time = time.time()
                else:
                    time.sleep(1)

        # --- GAMETIME 24/7 ---
        elif mode == "gametime":
            target_exe = state.get("gametime_main_game", "dota2.exe")
            target_name = state.get("gametime_main_name", "Dota 2")
            target_id = state.get("gametime_main_id", "356875988589740042")

            is_alive = False
            if current_process and current_process.poll() is None:
                is_alive = True

            if not is_alive:
                kill_current_game()
                pid = spawn_game(target_exe)
                set_discord_rpc(target_id, target_name, "Game Time Farm (24/7)")
                state["current_game"] = {"name": target_name, "exe": target_exe, "id": target_id}
                state["current_pid"] = pid
                save_state(state)
                update_tray_ui()
                log(f"[24/7 Game Time] Active game: {target_name} ({target_exe}) | PID: {pid}")

            for _ in range(6):
                if not running_flag:
                    break
                time.sleep(5)
                if not state.get("paused"):
                    state["total_farmed_seconds"] += 5

            if time.time() - last_save_time > 60:
                save_state(state)
                update_tray_ui()
                last_save_time = time.time()

    kill_current_game()
    state["running"] = False
    state["current_pid"] = None
    state["current_game"] = None
    save_state(state)
    log("BadgeFarmer 24/7 Engine Stopped gracefully.")

def create_tray_image():
    # 64x64 stylish icon with gaming badge shape
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Discord purple rounded badge
    d.rounded_rectangle((4, 4, 60, 60), radius=14, fill=(88, 101, 242))
    # Green live dot in top-right
    d.ellipse((44, 8, 56, 20), fill=(87, 242, 135))
    # Gamepad silhouette
    d.ellipse((14, 24, 50, 48), fill=(255, 255, 255))
    d.ellipse((22, 32, 28, 38), fill=(88, 101, 242))
    d.ellipse((36, 32, 42, 38), fill=(88, 101, 242))
    return img

def action_skip(icon, item):
    global skip_requested
    skip_requested = True
    log("User clicked 'Next Game' from tray menu.")

def action_toggle_pause(icon, item):
    state["paused"] = not state.get("paused", False)
    save_state(state)
    update_tray_ui()
    log(f"User toggled pause. Paused = {state['paused']}")

def action_open_status(icon, item):
    status_bat = os.path.join(BASE_DIR, "status.bat")
    try:
        subprocess.Popen(["cmd.exe", "/c", "start", "", status_bat])
    except Exception:
        pass

def action_exit(icon, item):
    global running_flag
    running_flag = False
    if icon:
        icon.stop()

def get_menu():
    cur_game = state.get("current_game")
    game_title = cur_game.get("name") if cur_game else "—"
    count = len(state.get("unique_games_farmed", []))
    target = state.get("variety_target", 100)
    hours = round(state.get("total_farmed_seconds", 0) / 3600, 1)
    status_label = "Статус: На паузе ⏸" if state.get("paused") else "Статус: Работает 24/7 🟢"

    return pystray.Menu(
        pystray.MenuItem(status_label, lambda icon, item: None, enabled=False),
        pystray.MenuItem(f"🎮 Игра: {game_title}", lambda icon, item: None, enabled=False),
        pystray.MenuItem(f"📊 Прогресс: {count}/{target} игр", lambda icon, item: None, enabled=False),
        pystray.MenuItem(f"⏱ Наиграно: {hours} ч.", lambda icon, item: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("⏭ Следующая игра (Skip)", action_skip),
        pystray.MenuItem("⏸ Пауза / Возобновить", action_toggle_pause),
        pystray.MenuItem("📋 Открыть окно статуса", action_open_status),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ Выход", action_exit)
    )

def main():
    global tray_icon
    check_single_instance()

    # Start worker in background thread
    worker_th = threading.Thread(target=farmer_worker, daemon=True)
    worker_th.start()

    # Create tray icon
    img = create_tray_image()
    tray_icon = pystray.Icon(
        name="BadgeFarmer247",
        icon=img,
        title="BadgeFarmer 24/7: Запуск...",
        menu=pystray.Menu(get_menu)
    )

    update_tray_ui()
    log("Tray Icon initialized in Windows Notification Area (near Wi-Fi/Clock).")
    tray_icon.run()

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception as e:
        log(f"FATAL: {traceback.format_exc()}")

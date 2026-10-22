import win32gui, win32con, os, subprocess

wc = win32gui.WNDCLASS()
wc.lpfnWndProc = win32gui.DefWindowProc
wc.lpszClassName = 'DiscordGameWindowTest'
wc.hInstance = win32gui.GetModuleHandle(None)
class_atom = win32gui.RegisterClass(wc)

hwnd = win32gui.CreateWindow(
    class_atom, 'Dota 2',
    win32con.WS_OVERLAPPEDWINDOW,
    100, 100, 300, 200, 0, 0, wc.hInstance, None
)
win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
win32gui.UpdateWindow(hwnd)

pid = os.getpid()
print(f"Window created, HWND: {hwnd}, PID: {pid}")

node_script = f"""
const utils = require("C:/Users/Max/AppData/Local/Discord/app-1.0.9264/modules/discord_game_utils-1/discord_game_utils/discord_game_utils.node");
utils.identifyGame({pid}, (err, data) => console.log("IDENTIFIED:", err, data));
"""

res = subprocess.run(['node', '-e', node_script], capture_output=True, text=True)
print("Node output:", res.stdout)
win32gui.DestroyWindow(hwnd)

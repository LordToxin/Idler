# ⚡ BadgeFarmer247 Engine

> Ultra-lightweight, 24/7 autonomous background process orchestrator for card farming and telemetry with Win32 Mutex locking and Discord RPC integration.

[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows)](https://github.com/LordToxin)
[![Author](https://img.shields.io/badge/Author-LordToxin-00f5d4?style=flat-square&logo=github)](https://github.com/LordToxin)

---

## 🔬 Architecture & System Internals

```
┌────────────────────────────────────────────────────────┐
│            Local\BadgeFarmer_SingleInstance            │
│               [Win32 Kernel Named Mutex]               │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    Orchestration Core                  │
│       • Win32 Process Lifecycle Management             │
│       • Dynamic Game State Rotation Engine             │
│       • Discord IPC Telemetry (Rich Presence)          │
│       • Background WinTray Context Loop                │
└────────────────────────────────────────────────────────┘
```

### Key Technical Characteristics:
* **Kernel-Level Single Instance**: Utilizes `kernel32.CreateMutexW` to ensure strict single-process execution across Windows session boundaries with zero file-lock racing.
* **Non-Blocking Background Tray**: Built on a decoupled worker thread dispatching tray events without stalling heartbeat ticks.
* **Dynamic Process Substitution**: Sandboxed dummy execution via localized AppData storage (`BadgeFarmerGames`) with automated binary cleanup on SIGINT/SIGTERM.
* **Fault-Tolerant State Recovery**: JSON atomic write operations preventing state file corruption during abrupt machine reboots or power loss.

---

## 🚀 Installation & Headless Deployment

```bash
# Clone the repository
git clone https://github.com/LordToxin/BadgeFarmer.git
cd BadgeFarmer

# Install dependencies
pip install -r requirements.txt

# Run in background (headless)
start start_silent.vbs
```

---

## 📄 License

Distributed under the **MIT License**. Engineered by [LordToxin](https://github.com/LordToxin).

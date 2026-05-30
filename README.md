# 996 Protocol — Deep Work Timer

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt5-5.15+-orange.svg" alt="PyQt">
</p>

> Open-source productivity system. No entertainment. No time-wasting. Only building, reading, and research.

---

## What is 996 Protocol?

**996 Protocol** is a voluntary deep work timer adapted from Chinese work culture (9am to 9pm, 6 days a week). It helps you focus on meaningful work by counting down 12 hours and enforcing the **20-20-20 eye protection rule** — every 20 minutes, look at something 20 feet away for 20 seconds.

This app doesn't judge you. It just shows you the time you have left.

---

## Features

| Feature | Description |
|---------|-------------|
| **996 Countdown** | 12-hour timer counting down from 12:00:00 to 00:00:00 |
| **Start 20-20-20** | Timer starts with eye protection enabled |
| **Start (focus mode)** | Timer starts without interruptions |
| **Stop session** | Pauses everything for breaks |
| **End day** | Saves summary, resets timer for next day |
| **Eye break overlay** | Fullscreen dark overlay, 20-sec break, unskippable for first 10 sec |
| **Clipboard Notes** | Auto-capture clipboard content with timestamps for quick reference |
| **Daily dashboard** | Manual notes, time worked, eye break count |
| **Streak tracker** | 7-day squares (Mon-Sun), green if 4+ hours worked |
| **Auto-save** | Every 5 seconds + on all state changes |
| **System tray** | Minimize to tray, right-click menu |
| **Keyboard shortcuts** | `Ctrl+S` stop, `Ctrl+R` resume, `Ctrl+E` end day, `Ctrl+T` toggle always-on-top, `Ctrl+Q` quit |
| **Theme toggle** | Dark (default) / Light mode |
| **Data storage** | Fully local: `~/.996protocol/data.json` + `~/.996protocol/clipboard_notes.json` |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/kuro-toji/996-20-rule.git
cd 996-20-rule

# Install dependencies
pip install PyQt5

# Run the app
python 996.py
```

> **Note:** If PyQt5 is unavailable, the app automatically falls back to PyQt6.

---

## Usage

1. **Start a session** — Click "Start 20-20-20" (with eye protection) or "Start (focus mode)" (no eye breaks)
2. **Work** — The timer counts down. Eye breaks occur every 20 minutes if enabled
3. **Pause** — Click "Stop session" to pause (resumes where you left off)
4. **End day** — Click "End day" to save your session summary and reset

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Stop/Pause session |
| `Ctrl+R` | Resume last session mode |
| `Ctrl+E` | End day |
| `Ctrl+T` | Toggle always-on-top |
| `Ctrl+Q` | Quit app |

---

## Clipboard Notes

The app automatically captures clipboard content to help you remember important snippets:

- **Auto-capture**: Any text copied (>10 chars) is automatically saved
- **Manual add**: Click "+ Add" to manually create a note
- **Copy back**: Click 📋 to copy a note back to clipboard
- **Delete**: Click × to remove a note
- **Daily reset**: Clipboard notes clear at the start of each new day

Notes are stored in `~/.996protocol/clipboard_notes.json` (last 100 notes kept).

---

## Data Storage

All data is stored locally in JSON format:

```
~/.996protocol/data.json
~/.996protocol/clipboard_notes.json
```

### Main data.json structure:

```json
{
  "sessions": {
    "2026-04-04": {
      "worked_seconds": 38400,
      "eye_breaks": 12,
      "stop_cycles": 3,
      "note": "Read SICP chapters 3-4...",
      "completed": true
    }
  },
  "streak": {
    "2026-04-01": true,
    "2026-04-02": true,
    "2026-04-03": false
  },
  "settings": {
    "theme": "dark",
    "always_on_top": false,
    "eye_protection_default": true
  }
}
```

### Clipboard notes structure:

```json
[
  {
    "content": "Important text snippet captured...",
    "timestamp": "2026-04-04T14:30:00",
    "tags": ["manual"]
  },
  {
    "content": "https://github.com/user/repo",
    "timestamp": "2026-04-04T15:45:00",
    "tags": ["url"]
  }
]
```

---

## Eye Protection (20-20-20 Rule)

Every 20 minutes of active work:
1. Main window goes semi-transparent
2. Fullscreen overlay appears with "Eye Break" message
3. 20-second countdown (unskippable for first 10 seconds)
4. After 20 seconds, overlay auto-dismisses
5. Eye break counter increments

---

## Streak Tracker

The app tracks your weekly progress with 7 squares (Mon–Sun):
- **Green** — 4+ hours worked that day
- **Gray** — No session or less than 4 hours
- **Green border** — Today

---

## Theme

**Dark mode** (default):
- Background: `#0e0e0f`
- Cards: `#161618`
- Accent green: `#1fbe82`
- Accent amber: `#f0a830`
- Accent purple: `#8b7cf8`

**Light mode**:
- Background: `#f5f5f7`
- Cards: `#ffffff`
- Same accent colors

---

## Requirements

- Python 3.7+
- PyQt5 or PyQt6
- No internet required (fully offline)
- Cross-platform: Linux, Windows, macOS

---

## License

MIT — use it, fork it, ship it.

---

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

---

<p align="center">
  <strong>Work hard. Focus. Build.</strong>
</p>
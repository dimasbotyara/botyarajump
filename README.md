# 🦘 botyarajump

> **A juice-infused Doodle Jump–style platformer with 9 game modes, skin passives, daily quests, a story campaign, and a built-in level editor.** Pure Pygame-CE, zero engine bloat.

![Python CI](https://github.com/dimasbotyara/botyarajump/actions/workflows/python-app.yml/badge.svg)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Pygame-CE](https://img.shields.io/badge/Engine-Pygame--CE%202.5%2B-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

---

## ✨ Features

### 🎮 9 Unique Endless Game Modes
Every mode flips the formula:

| Mode | Twist |
|------|-------|
| 🌟 **Classic** | The timeless balance — all powerups, no surprises |
| 🌋 **Rising Lava** | Escape molten lava climbing from below |
| 🌑 **Dark Hunt** | Pitch-dark world with a flashlight spotlight around you |
| 🌀 **Gravity Chaos** | Gravity shifts every 15s — moon, heavy, hyper speed |
| ⏱️ **Time Attack** | 30-second clock; gain time by jumping, coins, and kills |
| 💀 **Hardcore** | No powerups, no shields, 1 life, brutal gaps |
| 🪞 **Mirror World** | Reversed controls to melt your brain |
| 👾 **Boss Mayhem** | UFOs and shooting clouds everywhere |
| 🧊 **Ice Avalanche** | Slippery platforms + falling icicles |

### 🎭 Skin Passive Abilities
Each skin isn't just cosmetic — it changes how you play:

- 🥷 **Ninja** — mid-air **Double Jump**
- 🪙 **Gold** — coin magnet + 25% extra coins
- 👻 **Ghost** — free **shield** that absorbs one lethal hit
- 🤖 **Robot** — rapid-fire **laser blaster**
- 🌈 **Rainbow** — +15% jump velocity
- ⚡ **Neon** — +25% movement speed
- 🧊 **Blue** — immune to ice platform slipping

Mix and match with the mode of your choice — Hardcore + Ghost is a completely different game from Classic + Neon.

### 📅 Daily Quests
3 unique challenges generated every day, each worth coin rewards. Come back daily — the quests rotate.

### 🧊 8+ Interactive Platform Types
- **Normal** — the reliable bread and butter
- **Moving** — slides horizontally
- **Breakable** — one jump and it's gone
- **Disappearing** — vanishes after you touch it
- **Spring** — super jump
- **Ice** — slippery (unless you're Blue skin)
- **Sand** — collapses after a short delay
- **Conveyor** — pushes you sideways
- **Portal** — teleports you across the level

### 📜 Story Mode + Level Editor
- **Story Mode** — multi-stage campaign with star ratings
- **Level Editor** — drag-and-drop level builder with **JSON export/import**
- Ship with `levels/level_1.json` through `level_5.json`, plus a `custom_levels/` folder for your own creations
- Share your levels as plain JSON

### 🎨 Juice & Visuals
- **Dynamic squash & stretch** body deformation
- **Camera screen shake** on impacts
- **Trail effects** and custom **particle systems** (`particles.py`)
- **Combo system** (`combo.py`) for chained jumps
- **Coins** with pickup effects (`coins.py`)
- **Powerups** and **boosters** — 4 booster slots bound to `1`–`4`

### 🏆 Progression
- **Achievements** system (`achievements.py`)
- **Shop** with skin unlocks (`shop.py`)
- Persistent `save_data.json` keeps your coins, unlocks, and progress
- **Daily quest tracking**

### 🌍 Localization
- **EN / RU** translation out of the box (`localization.py`)

### 🎛️ Fully Remappable Controls
Everything bindable in Settings — including the four booster hotkeys.

---

## 🚀 Quick Start

### 🚀 One-Click Launchers

```bash
./run.sh          # Linux / macOS
run.bat           # Windows (CMD)
.\run.ps1         # Windows (PowerShell)
```

### 📦 Manual Installation

```bash
git clone https://github.com/dimasbotyara/botyarajump.git
cd botyarajump

python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows

pip install -r requirements.txt
python main.py
```

**Requires:** Python 3.10+ and **Pygame-CE 2.5+** (Community Edition).

---

## 🎮 Default Controls

| Action | Primary | Secondary |
| :--- | :---: | :---: |
| **Move Left** | `←` | `A` |
| **Move Right** | `→` | `D` |
| **Shoot Blaster** | `↑` | `W` |
| **Pause / Resume** | `Esc` | `P` |
| **Use Boosters** | `1` `2` `3` `4` | remappable |

> 💡 Everything can be rebound in **Settings**.

---

## 📂 Project Structure

```
botyarajump/
├── main.py              # 🎯 Entry point
├── game.py              # Main loop, states, game-mode controller
├── player.py            # Physics, skin passives, squash & stretch
├── platforms.py         # 9 platform types + procedural generator
├── enemies.py           # Snakes, UFOs, clouds — AI + collisions
├── powerups.py          # In-run powerups
├── boosters.py          # Active boosters (1-4 keys)
├── coins.py             # Coin pickup logic + magnet
├── combo.py             # Combo chain tracker
├── camera.py            # Camera, shake, parallax
├── particles.py         # Trail, portal, stomp emitters
├── renderer.py          # All drawing routines
├── ui.py                # Menus, mode select, HUD, buttons
├── level_editor.py      # Drag & drop level builder
├── story_mode.py        # Campaign progression + stars
├── daily_quests.py      # Daily challenge generator & tracking
├── achievements.py      # Achievement tracker
├── shop.py              # Skin shop + passive abilities
├── settings.py          # SaveManager & config persistence
├── localization.py      # EN / RU strings
├── utils.py             # Shared helpers
├── levels/              # 📁 level_1.json … level_5.json
├── custom_levels/       # 📁 your own creations
├── save_data.json       # Auto-generated progress
├── run.sh / .bat / .ps1 # Launchers
├── requirements.txt
└── LICENSE
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Engine** | Pygame-CE 2.5+ |
| **Physics** | Custom (squash & stretch, dynamic gravity) |
| **Data** | JSON (levels, save file, custom levels) |
| **i18n** | Built-in (EN / RU) |

Zero external Python dependencies beyond `pygame-ce` — everything else is hand-rolled.

---

## 🔧 Customization

### Creating your own levels
Use the **in-game Level Editor** → drag platforms, place hazards, save. Levels export as JSON to `custom_levels/` and can be shared as plain text.

### Adding a new game mode
Each mode is a config block in `game.py`. Copy a mode's dict, tweak the gravity / powerup rules / enemy density, and add it to the mode-select list in `ui.py`.

### Adding a new skin passive
Add an entry to `shop.py`, then read it in `player.py` at runtime to change jump velocity, speed, double-jump availability, etc.

### Tweaking juice
`particles.py`, `camera.py`, and `player.py` hold all the squash/stretch, shake, and trail parameters.

---

## 🐛 Troubleshooting

**`pygame` module not found**
- Install **pygame-ce**, not the original pygame: `pip install pygame-ce`. The project relies on CE-specific rendering.

**`run.sh` permission denied**
- `chmod +x run.sh`

**High scores aren't saving**
- Check that `save_data.json` is writable in the project directory. Some sandboxed environments block file writes there — move the project out of a restricted path.

**Level editor crashes on save**
- Make sure `custom_levels/` exists. The launchers create it automatically, but manual installs might skip it.

**Story mode stars wrong after editing levels**
- Stars are stored per stage in `save_data.json`. Delete the file to reset progress.

---

## 🚧 Roadmap

- ✅ 9 endless modes
- ✅ Daily quests
- ✅ Skin passives
- ✅ Story campaign
- ✅ Level editor
- ⬜ Community level browser (via URL paste)
- ⬜ More skins

---

## ⚠️ Disclaimer

This is a **fan-made platformer inspired by Doodle Jump**. Not affiliated with the original creators. All art, code, and audio in this repo are original or properly licensed — see `LICENSE`.

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](LICENSE).

---

## 💖 Acknowledgements

- Built with **[Pygame-CE](https://pyga.me)** (Community Edition)
- Inspired by the classic **Doodle Jump**

---

## 👤 Author

**dimasbotyara** — [@dimasbotyara](https://github.com/dimasbotyara)

Made with 🦘, ☕, and an unhealthy love for squash & stretch.

---

<div align="center">

**If you bounced your way to a new high score, drop a ⭐**

</div>

# 🦘 Botyara Jump

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Pygame-CE](https://img.shields.io/badge/Engine-Pygame--CE%202.5%2B-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

An action-packed, juice-infused **Doodle Jump–style platformer** built with **Pygame-CE**. Featuring 9 unique game modes, daily quests, shop skin passives, dynamic squash & stretch physics, particle effects, story campaign, and an in-game level editor!

---

## 🔥 Key Features

- 🎮 **9 Unique Endless Game Modes**:
  - 🌟 **Classic** — Timeless jumping balance with all powerups.
  - 🌋 **Rising Lava** — Escape the rising molten lava below.
  - 🌑 **Dark Hunt** — Pitch dark world with a spotlight flashlight around your character.
  - 🌀 **Gravity Chaos** — Dynamic gravity shifts every 15 seconds (moon gravity, heavy gravity, hyper speed).
  - ⏱️ **Time Attack** — Race against a 30s ticking clock; gain time by jumping, collecting coins, and defeating monsters.
  - 💀 **Hardcore** — No powerups, no shields, 1 life, and unforgiving platform gaps.
  - 🪞 **Mirror World** — Reversed controls test your brain & agility.
  - 👾 **Boss Mayhem** — High density of hostile UFOs and shooting clouds.
  - 🧊 **Ice Avalanche** — 100% slippery ice platforms + falling icicle hazards.
- 📅 **Daily Quests System**: 3 unique daily challenges generated every day with coin rewards.
- 🎭 **Skin Passive Abilities**:
  - 🥷 **Ninja**: Mid-air Double Jump.
  - 🪙 **Gold**: Coin magnet + 25% extra coins.
  - 👻 **Ghost**: Shield absorbing 1 lethal hit per run.
  - 🤖 **Robot**: Rapid-fire laser blaster.
  - 🌈 **Rainbow**: +15% jump velocity.
  - ⚡ **Neon**: +25% movement speed.
  - 🧊 **Blue**: Immunity to ice platform slipping.
- 🧊 **8+ Interactive Platform Types**: Normal, Moving, Breakable, Disappearing, Spring, Ice, Sand (collapsing), Conveyor, and Portal.
- 🎨 **Visuals & Juice**: Dynamic squash & stretch body deformation, camera screen shakes, trail effects, and custom particle systems.
- 🛠️ **Built-in Level Editor**: Full drag-and-drop level creation tool with JSON export/import.
- 📜 **Story Mode**: Multi-stage campaign mode with custom star ratings.

---

## ⚡ Quick Start

### 🚀 One-Click Launchers
Simply run the launcher script for your platform:

- **Linux / macOS**:
  ```bash
  ./run.sh
  ```
- **Windows (CMD)**:
  ```cmd
  run.bat
  ```
- **Windows (PowerShell)**:
  ```powershell
  .\run.ps1
  ```

---

### 📦 Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dimasbotyara/botyarajump.git
   cd botyarajump
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Linux / macOS
   # OR
   .venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game**:
   ```bash
   python main.py
   ```

---

## 🎮 Default Controls

| Action | Primary Key | Secondary Key |
| :--- | :---: | :---: |
| **Move Left** | `Left Arrow` | `A` |
| **Move Right** | `Right Arrow` | `D` |
| **Shoot Blaster** | `Up Arrow` | `W` |
| **Pause / Resume** | `Escape` | `P` |
| **Use Boosters** | `1`, `2`, `3`, `4` | Custom |

> 💡 *All controls can be fully remapped in the **Settings** menu.*

---

## 📂 Project Architecture

```text
botyarajump/
├── main.py              # Application entry point
├── game.py              # Main loop, states, and game modes controller
├── player.py            # Physics, skin passives, squash/stretch
├── platforms.py         # Platform types and level generator
├── enemies.py           # Enemy AI, snakes, UFOs, and collisions
├── daily_quests.py      # Daily Quest Manager & reward system
├── shop.py              # Shop UI & skin abilities
├── level_editor.py      # Integrated Level Editor
├── ui.py                # UI screens, Mode Select, HUD, and buttons
├── renderer.py          # Graphics, shapes, and drawing routines
├── particles.py         # Particle emitters (trails, portals, stomps)
├── settings.py          # SaveManager & settings persistence
├── localization.py      # Multi-language translation support (EN / RU)
├── run.sh / run.bat     # One-click launchers for Linux & Windows
└── save_data.json       # Game progress (auto-generated)
```

---

## 📝 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 💖 Acknowledgements

- Built with **[Pygame-CE](https://pyga.me)** (Community Edition).
- Inspired by the classic **Doodle Jump**.

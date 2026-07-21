botyarajump
===========

A Doodle Jump–style platformer built with Pygame (pygame-ce). Play endless or story levels, collect coins, use boosters, unlock skins, and build custom levels with the included editor.

Features
- Endless mode and Story mode (levels in /levels).
- Level editor and support for custom levels (saved in /custom_levels).
- Enemies, powerups, boosters, coins, achievements, and shop.
- Configurable controls, fullscreen/resizable window, and save data persistence (save_data.json).
- Localized text support and simple particle/GUI systems.

Requirements
- Python 3.10+ (project tested with later versions)
- Platform SDL dependencies required by pygame (libsdl2, image, mixer, ttf, etc.)
- Python packages: see requirements.txt (pygame-ce, pyperclip)

Installation
1. Clone the repo:
   git clone https://github.com/dimasbotyara/botyarajump.git
2. Create and activate a virtual environment (recommended):
   python -m venv .venv
   source .venv/bin/activate  (or .venv\\Scripts\\activate on Windows)
3. Install dependencies:
   pip install -r requirements.txt

Running
From project root:

    python main.py

The game window is resizable and supports fullscreen (toggle in settings).

Default controls
- Move left: Left Arrow or A
- Move right: Right Arrow or D
- Shoot / secondary: Up Arrow or W
- Pause: Esc or P
- Boosters: 1, 2, 3, 4 (can be remapped in Settings)

Settings & Save Data
- Save file: save_data.json (created/updated automatically).
- Default resolution: 480×800 (change in Settings).
- Difficulty and other defaults are in settings.py.

Story & Custom Levels
- Story levels are JSON files in /levels (level_1.json … level_5.json).
- The game generates default story levels on first run.
- Create custom levels with the Level Editor or by placing level JSON in /custom_levels and loading them from the Custom Levels menu.

Project layout (key files)
- main.py — entry point
- game.py — main game loop and state
- settings.py — default settings and SaveManager
- levels/ — story levels (JSON)
- custom_levels/ — user-made levels
- save_data.json — user save file (created at runtime)
- requirements.txt — dependencies

Extending & Contributing
- Contributions welcome. Open issues or submit PRs.
- Prefer small, focused changes and include tests when applicable.
- If adding assets, avoid committing large binary files; prefer optimized images.

Troubleshooting
- If pygame install fails, install platform SDL prerequisites (libsdl2, sdl2-image, sdl2-mixer, sdl2-ttf) via your package manager.
- If the window doesn't open: ensure correct Python interpreter and that pygame-ce is installed in the active venv.
- Corrupted save file? Delete save_data.json to regenerate defaults.

License
MIT — see LICENSE file.

Acknowledgements
- Inspired by Doodle Jump.
- Uses pygame-ce and other open-source libraries.

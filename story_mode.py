"""
botyarajump - Story Mode
Handles story mode level progression and narrative.
"""

import os
import json

from settings import save_manager, STORY_LEVELS_DIR


# Story text between levels
STORY_TEXTS = {
    1: {
        "en": {
            "intro": "The adventure begins! Climb your way to the top!",
            "complete": "Great job! You've conquered the first peak!"
        },
        "ru": {
            "intro": "Приключение начинается! Поднимись на самый верх!",
            "complete": "Отлично! Ты покорил первую вершину!"
        }
    },
    2: {
        "en": {
            "intro": "The enemies are getting tougher. Watch your step!",
            "complete": "You've made it through the danger zone!"
        },
        "ru": {
            "intro": "Враги становятся сильнее. Будь осторожен!",
            "complete": "Ты прорвался через опасную зону!"
        }
    },
    3: {
        "en": {
            "intro": "The platforms are disappearing! Hurry up!",
            "complete": "Incredible! You defied gravity itself!"
        },
        "ru": {
            "intro": "Платформы исчезают! Поторопись!",
            "complete": "Невероятно! Ты бросил вызов гравитации!"
        }
    },
    4: {
        "en": {
            "intro": "A dark force awaits. Only the brave will survive!",
            "complete": "The darkness retreats before you!"
        },
        "ru": {
            "intro": "Тёмная сила ждёт. Только смелые выживут!",
            "complete": "Тьма отступает перед тобой!"
        }
    },
    5: {
        "en": {
            "intro": "The final ascent! Everything is at stake!",
            "complete": "You are the champion! The sky is yours!"
        },
        "ru": {
            "intro": "Финальный подъём! Всё на кону!",
            "complete": "Ты чемпион! Небо принадлежит тебе!"
        }
    }
}


def get_story_text(level_num, text_type="intro"):
    """Get story text for a level.
    text_type: 'intro' or 'complete'
    """
    lang = save_manager.get_language()
    level_texts = STORY_TEXTS.get(level_num, {})
    lang_texts = level_texts.get(lang, level_texts.get("en", {}))
    return lang_texts.get(text_type, "")


def generate_default_levels():
    """Generate default story level files if they don't exist."""
    os.makedirs(STORY_LEVELS_DIR, exist_ok=True)

    default_levels = {
        1: _generate_level_1(),
        2: _generate_level_2(),
        3: _generate_level_3(),
        4: _generate_level_4(),
        5: _generate_level_5(),
    }

    for num, data in default_levels.items():
        filepath = os.path.join(STORY_LEVELS_DIR, f"level_{num}.json")
        if not os.path.exists(filepath):
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except IOError:
                pass


def _generate_level_1():
    """Level 1: Simple introduction."""
    platforms = []
    y = 145
    # Starting platform
    platforms.append({"type": "normal", "x": 5, "y": y, "width": 3})
    y -= 4
    for i in range(25):
        x = 2 + (i % 7) * 2
        platforms.append({"type": "normal", "x": x, "y": y, "width": 2})
        y -= 3

    return {
        "name": "Level 1 - First Steps",
        "author": "botyarajump",
        "version": 1,
        "height": 5000,
        "grid_size": 32,
        "background_theme": "day",
        "platforms": platforms,
        "enemies": [],
        "coins": [
            {"x": 4 + i * 3, "y": 140 - i * 12} for i in range(8)
        ],
        "powerups": [],
        "start": {"x": 6, "y": 144},
        "finish_y": y + 5,
        "star_scores": [300, 600, 1000]
    }


def _generate_level_2():
    """Level 2: Enemies introduced."""
    platforms = []
    enemies = []
    coins = []
    y = 145

    platforms.append({"type": "normal", "x": 5, "y": y, "width": 3})
    y -= 4

    for i in range(30):
        x = 1 + (i * 3) % 10
        ptype = "moving" if i % 5 == 3 else "normal"
        p = {"type": ptype, "x": x, "y": y, "width": 2}
        if ptype == "moving":
            p["range"] = 3
            p["speed"] = 2
        platforms.append(p)

        if i % 6 == 4:
            enemies.append({"type": "slug", "x": x + 1, "y": y - 1})
        if i % 4 == 0:
            coins.append({"x": x + 1, "y": y - 2})

        y -= 3

    return {
        "name": "Level 2 - New Foes",
        "author": "botyarajump",
        "version": 1,
        "height": 6000,
        "grid_size": 32,
        "background_theme": "sunset",
        "platforms": platforms,
        "enemies": enemies,
        "coins": coins,
        "powerups": [
            {"type": "shield", "x": 6, "y": 100}
        ],
        "start": {"x": 6, "y": 144},
        "finish_y": y + 5,
        "star_scores": [400, 800, 1500]
    }


def _generate_level_3():
    """Level 3: Disappearing platforms."""
    platforms = []
    enemies = []
    coins = []
    y = 145

    platforms.append({"type": "normal", "x": 5, "y": y, "width": 3})
    y -= 4

    for i in range(35):
        x = 1 + (i * 4) % 9
        if i % 3 == 0:
            ptype = "disappearing"
        elif i % 5 == 2:
            ptype = "breakable"
        else:
            ptype = "normal"

        p = {"type": ptype, "x": x, "y": y, "width": 2}
        platforms.append(p)

        if i % 7 == 3:
            enemies.append({"type": "bat", "x": x, "y": y - 2})
        if i % 3 == 0:
            coins.append({"x": x, "y": y - 2})

        y -= 3

    return {
        "name": "Level 3 - Now You See Me",
        "author": "botyarajump",
        "version": 1,
        "height": 7000,
        "grid_size": 32,
        "background_theme": "night",
        "platforms": platforms,
        "enemies": enemies,
        "coins": coins,
        "powerups": [
            {"type": "jetpack", "x": 5, "y": 80}
        ],
        "start": {"x": 6, "y": 144},
        "finish_y": y + 5,
        "star_scores": [500, 1000, 2000]
    }


def _generate_level_4():
    """Level 4: Heavy enemies."""
    platforms = []
    enemies = []
    coins = []
    powerups = []
    y = 145

    platforms.append({"type": "normal", "x": 5, "y": y, "width": 3})
    y -= 4

    for i in range(40):
        x = 1 + (i * 3 + i) % 9
        ptype = "normal" if i % 4 != 3 else "moving"
        p = {"type": ptype, "x": x, "y": y, "width": 2}
        if ptype == "moving":
            p["range"] = 4
            p["speed"] = 2.5
        platforms.append(p)

        if i % 5 == 2:
            enemy_types = ["slug", "bat", "red_ball", "ghost"]
            etype = enemy_types[i % len(enemy_types)]
            enemies.append({"type": etype, "x": x + 1, "y": y - 2})

        if i % 3 == 0:
            coins.append({"x": x, "y": y - 2})

        y -= 3

    powerups.append({"type": "blaster", "x": 4, "y": 100})
    powerups.append({"type": "shield", "x": 7, "y": 60})

    return {
        "name": "Level 4 - Dark Forces",
        "author": "botyarajump",
        "version": 1,
        "height": 8000,
        "grid_size": 32,
        "background_theme": "space",
        "platforms": platforms,
        "enemies": enemies,
        "coins": coins,
        "powerups": powerups,
        "start": {"x": 6, "y": 144},
        "finish_y": y + 5,
        "star_scores": [600, 1200, 2500]
    }


def _generate_level_5():
    """Level 5: Ultimate challenge."""
    platforms = []
    enemies = []
    coins = []
    powerups = []
    y = 145

    platforms.append({"type": "normal", "x": 5, "y": y, "width": 3})
    y -= 4

    for i in range(50):
        x = 1 + (i * 5 + i * i) % 9
        r = i % 7
        if r == 0:
            ptype = "disappearing"
        elif r == 1:
            ptype = "breakable"
        elif r == 2:
            ptype = "moving"
        elif r == 5:
            ptype = "spring"
        else:
            ptype = "normal"

        p = {"type": ptype, "x": x, "y": y, "width": 2}
        if ptype == "moving":
            p["range"] = 5
            p["speed"] = 3
        platforms.append(p)

        if i % 4 == 2:
            all_enemy_types = ["slug", "bat", "red_ball", "ghost",
                                "snake", "evil_cloud", "ufo"]
            etype = all_enemy_types[i % len(all_enemy_types)]
            enemies.append({"type": etype, "x": max(1, x - 1), "y": y - 2})

        if i % 2 == 0:
            coins.append({"x": x + 1, "y": y - 2})

        y -= 3

    # Boss area: black hole near finish
    enemies.append({"type": "black_hole", "x": 5, "y": y + 15})

    powerups.append({"type": "jetpack", "x": 3, "y": 100})
    powerups.append({"type": "blaster", "x": 8, "y": 70})
    powerups.append({"type": "shield", "x": 5, "y": y + 25})
    powerups.append({"type": "magnet", "x": 6, "y": 120})

    return {
        "name": "Level 5 - The Final Ascent",
        "author": "botyarajump",
        "version": 1,
        "height": 10000,
        "grid_size": 32,
        "background_theme": "lava",
        "platforms": platforms,
        "enemies": enemies,
        "coins": coins,
        "powerups": powerups,
        "start": {"x": 6, "y": 144},
        "finish_y": y + 5,
        "star_scores": [800, 1600, 3000]
    }
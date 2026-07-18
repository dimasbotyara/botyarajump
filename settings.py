"""
botyarajump - Settings Manager
Handles loading/saving all game settings and save data.
"""

import json
import os
import sys

# Path to save file in project directory
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_data.json")
CUSTOM_LEVELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_levels")
STORY_LEVELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels")

# Ensure directories exist
os.makedirs(CUSTOM_LEVELS_DIR, exist_ok=True)
os.makedirs(STORY_LEVELS_DIR, exist_ok=True)

# Screen defaults
DEFAULT_WIDTH = 480
DEFAULT_HEIGHT = 800

# Physics defaults
GRAVITY = 0.5
PLAYER_JUMP_VELOCITY = -12
PLAYER_SPEED = 6
PLAYER_MAX_FALL_SPEED = 15

# Platform defaults
PLATFORM_WIDTH = 70
PLATFORM_HEIGHT = 15
PLATFORM_COUNT_BASE = 8

# Difficulty multipliers
DIFFICULTY_SETTINGS = {
    "easy": {
        "enemy_spawn_chance": 0.03,
        "breakable_chance": 0.08,
        "disappearing_chance": 0.03,
        "moving_chance": 0.1,
        "spring_chance": 0.08,
        "coin_spawn_chance": 0.15,
        "enemy_speed_mult": 0.7,
        "platform_gap_mult": 0.85,
        "score_mult": 0.8
    },
    "normal": {
        "enemy_spawn_chance": 0.06,
        "breakable_chance": 0.12,
        "disappearing_chance": 0.06,
        "moving_chance": 0.15,
        "spring_chance": 0.06,
        "coin_spawn_chance": 0.1,
        "enemy_speed_mult": 1.0,
        "platform_gap_mult": 1.0,
        "score_mult": 1.0
    },
    "hard": {
        "enemy_spawn_chance": 0.1,
        "breakable_chance": 0.18,
        "disappearing_chance": 0.1,
        "moving_chance": 0.2,
        "spring_chance": 0.04,
        "coin_spawn_chance": 0.07,
        "enemy_speed_mult": 1.4,
        "platform_gap_mult": 1.2,
        "score_mult": 1.5
    }
}

# Booster defaults
BOOSTER_COOLDOWN = 15.0  # seconds, shared cooldown
BOOSTER_TYPES = {
    "super_jump": {
        "duration": 0,  # instant
        "price": 50
    },
    "shield": {
        "duration": 5.0,
        "price": 80
    },
    "slowmo": {
        "duration": 3.0,
        "price": 60
    },
    "bomb": {
        "duration": 0,  # instant
        "price": 100
    }
}

# Shop items
SHOP_SKINS = {
    "default": {"price": 0, "name_key": "skin_default"},
    "red": {"price": 50, "name_key": "skin_red"},
    "blue": {"price": 50, "name_key": "skin_blue"},
    "gold": {"price": 150, "name_key": "skin_gold"},
    "neon": {"price": 200, "name_key": "skin_neon"},
    "pixel": {"price": 100, "name_key": "skin_pixel"},
    "ghost": {"price": 250, "name_key": "skin_ghost"},
    "rainbow": {"price": 300, "name_key": "skin_rainbow"},
    "ninja": {"price": 200, "name_key": "skin_ninja"},
    "robot": {"price": 350, "name_key": "skin_robot"}
}

SHOP_TRAILS = {
    "none": {"price": 0, "name_key": "trail_none"},
    "fire": {"price": 100, "name_key": "trail_fire"},
    "stars": {"price": 100, "name_key": "trail_stars"},
    "rainbow": {"price": 150, "name_key": "trail_rainbow"},
    "bubbles": {"price": 80, "name_key": "trail_bubbles"},
    "snow": {"price": 120, "name_key": "trail_snow"},
    "hearts": {"price": 130, "name_key": "trail_hearts"},
    "lightning": {"price": 200, "name_key": "trail_lightning"}
}

SHOP_THEMES = {
    "day": {"price": 0, "name_key": "theme_day"},
    "night": {"price": 100, "name_key": "theme_night"},
    "sunset": {"price": 120, "name_key": "theme_sunset"},
    "space": {"price": 200, "name_key": "theme_space"},
    "forest": {"price": 150, "name_key": "theme_forest"},
    "ocean": {"price": 150, "name_key": "theme_ocean"},
    "candy": {"price": 180, "name_key": "theme_candy"},
    "lava": {"price": 250, "name_key": "theme_lava"}
}


def get_default_save_data():
    """Return default save data structure."""
    return {
        "high_score": 0,
        "coins": 0,
        "settings": {
            "language": "en",
            "music_volume": 0.7,
            "sfx_volume": 1.0,
            "hud_opacity": 255,
            "controls": {
                "left": ["K_LEFT", "K_a"],
                "right": ["K_RIGHT", "K_d"],
                "shoot": ["K_UP", "K_w"],
                "pause": ["K_ESCAPE", "K_p"],
                "booster_1": ["K_1", ""],
                "booster_2": ["K_2", ""],
                "booster_3": ["K_3", ""],
                "booster_4": ["K_4", ""]
            },
            "fullscreen": False,
            "resolution": [DEFAULT_WIDTH, DEFAULT_HEIGHT],
            "difficulty": "normal",
            "show_fps": False
        },
        "unlocks": {
            "skins": ["default"],
            "trails": ["none"],
            "themes": ["day"],
            "boosters": []
        },
        "equipped": {
            "skin": "default",
            "trail": "none",
            "theme": "day",
            "boosters": ["", "", "", ""]
        },
        "statistics": {
            "total_jumps": 0,
            "total_games": 0,
            "total_kills": 0,
            "total_coins_collected": 0,
            "total_coins_spent": 0,
            "total_platforms_landed": 0,
            "total_breakable_broken": 0,
            "total_playtime_seconds": 0.0,
            "highest_combo": 0,
            "max_height_reached": 0,
            "powerups_used": {
                "spring": 0,
                "jetpack": 0,
                "blaster": 0,
                "shield": 0,
                "magnet": 0
            },
            "enemies_killed_by_type": {
                "slug": 0,
                "bat": 0,
                "black_hole": 0,
                "ghost": 0,
                "red_ball": 0,
                "snake": 0,
                "evil_cloud": 0,
                "ufo": 0
            },
            "deaths": 0,
            "boosters_used": 0
        },
        "achievements": {},
        "story_progress": {
            "unlocked_level": 1,
            "stars": {
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0,
                "5": 0
            }
        }
    }


def deep_merge(base, override):
    """Deep merge override into base, keeping base keys that don't exist in override."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class SaveManager:
    """Manages loading and saving game data."""

    def __init__(self):
        self.data = get_default_save_data()
        self.load()

    def load(self):
        """Load save data from file, merging with defaults."""
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                self.data = deep_merge(get_default_save_data(), loaded)
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"Warning: Could not load save file: {e}")
                self.data = get_default_save_data()
        else:
            self.data = get_default_save_data()
            self.save()

    def save(self):
        """Save data to file."""
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save file: {e}")

    # --- Convenience getters/setters ---

    @property
    def settings(self):
        return self.data["settings"]

    @property
    def statistics(self):
        return self.data["statistics"]

    @property
    def unlocks(self):
        return self.data["unlocks"]

    @property
    def equipped(self):
        return self.data["equipped"]

    @property
    def story_progress(self):
        return self.data["story_progress"]

    @property
    def high_score(self):
        return self.data["high_score"]

    @high_score.setter
    def high_score(self, value):
        self.data["high_score"] = value

    @property
    def coins(self):
        return self.data["coins"]

    @coins.setter
    def coins(self, value):
        self.data["coins"] = value

    def get_language(self):
        return self.settings.get("language", "en")

    def set_language(self, lang):
        self.settings["language"] = lang
        self.save()

    def get_difficulty(self):
        return self.settings.get("difficulty", "normal")

    def get_difficulty_settings(self):
        diff = self.get_difficulty()
        return DIFFICULTY_SETTINGS.get(diff, DIFFICULTY_SETTINGS["normal"])

    def get_controls(self):
        return self.settings.get("controls", get_default_save_data()["settings"]["controls"])

    def set_control(self, action, slot, key_name):
        """Set a control binding. action='left', slot=0 or 1, key_name='K_LEFT'."""
        controls = self.get_controls()
        if action in controls:
            while len(controls[action]) <= slot:
                controls[action].append("")
            controls[action][slot] = key_name
            self.save()

    def get_hud_opacity(self):
        return self.settings.get("hud_opacity", 255)

    def set_hud_opacity(self, value):
        self.settings["hud_opacity"] = max(0, min(255, value))
        self.save()

    def get_resolution(self):
        res = self.settings.get("resolution", [DEFAULT_WIDTH, DEFAULT_HEIGHT])
        return tuple(res)

    def set_resolution(self, width, height):
        self.settings["resolution"] = [width, height]
        self.save()

    def is_fullscreen(self):
        return self.settings.get("fullscreen", False)

    def set_fullscreen(self, value):
        self.settings["fullscreen"] = value
        self.save()

    def get_music_volume(self):
        return self.settings.get("music_volume", 0.7)

    def get_sfx_volume(self):
        return self.settings.get("sfx_volume", 1.0)

    # --- Statistics ---

    def add_stat(self, key, amount=1):
        """Increment a statistic."""
        if key in self.statistics:
            self.statistics[key] += amount

    def add_nested_stat(self, category, key, amount=1):
        """Increment a nested statistic like enemies_killed_by_type.slug."""
        if category in self.statistics and isinstance(self.statistics[category], dict):
            if key not in self.statistics[category]:
                self.statistics[category][key] = 0
            self.statistics[category][key] += amount

    def set_stat_max(self, key, value):
        """Set statistic only if new value is higher."""
        if key in self.statistics:
            if value > self.statistics[key]:
                self.statistics[key] = value

    # --- Unlocks ---

    def unlock_item(self, category, item_id):
        """Unlock a shop item. category='skins','trails','themes','boosters'."""
        if category in self.unlocks:
            if item_id not in self.unlocks[category]:
                self.unlocks[category].append(item_id)
                self.save()

    def is_unlocked(self, category, item_id):
        """Check if item is unlocked."""
        if category in self.unlocks:
            return item_id in self.unlocks[category]
        return False

    def equip_item(self, category, item_id):
        """Equip an item. category='skin','trail','theme'."""
        if category in self.equipped:
            self.equipped[category] = item_id
            self.save()

    def equip_booster(self, slot, booster_id):
        """Equip a booster to slot 0-3."""
        if 0 <= slot < 4:
            self.equipped["boosters"][slot] = booster_id
            self.save()

    def spend_coins(self, amount):
        """Spend coins if enough. Returns True if successful."""
        if self.coins >= amount:
            self.coins -= amount
            self.add_stat("total_coins_spent", amount)
            self.save()
            return True
        return False

    def earn_coins(self, amount):
        """Add coins."""
        self.coins += amount
        self.add_stat("total_coins_collected", amount)
        self.save()

    # --- Achievements ---

    def unlock_achievement(self, achievement_id):
        """Mark achievement as unlocked. Returns True if newly unlocked."""
        if achievement_id not in self.data["achievements"]:
            import time
            self.data["achievements"][achievement_id] = {
                "unlocked": True,
                "timestamp": time.time()
            }
            self.save()
            return True
        return False

    def is_achievement_unlocked(self, achievement_id):
        return achievement_id in self.data["achievements"]

    # --- Story ---

    def complete_story_level(self, level_num, stars):
        """Mark story level as complete with star rating."""
        key = str(level_num)
        if key in self.story_progress["stars"]:
            if stars > self.story_progress["stars"][key]:
                self.story_progress["stars"][key] = stars
        if level_num >= self.story_progress["unlocked_level"]:
            self.story_progress["unlocked_level"] = min(level_num + 1, 5)
        self.save()


# Global save manager instance
save_manager = SaveManager()
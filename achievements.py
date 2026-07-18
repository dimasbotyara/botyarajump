"""
botyarajump - Achievements & Statistics
Tracks player progress and unlocks achievements.
"""

import pygame
import time
import math

from settings import save_manager
from utils import create_surface_with_alpha, clamp


# Achievement definitions
# Each has: id, name_key, desc_key, check_function
ACHIEVEMENT_DEFS = [
    # === JUMPS ===
    {
        "id": "ach_first_jump",
        "category": "jumps",
        "icon": "jump",
        "check": lambda stats, **kw: stats.get("total_jumps", 0) >= 1
    },
    {
        "id": "ach_100_jumps",
        "category": "jumps",
        "icon": "jump",
        "check": lambda stats, **kw: stats.get("total_jumps", 0) >= 100
    },
    {
        "id": "ach_1000_jumps",
        "category": "jumps",
        "icon": "jump",
        "check": lambda stats, **kw: stats.get("total_jumps", 0) >= 1000
    },
    {
        "id": "ach_10000_jumps",
        "category": "jumps",
        "icon": "jump",
        "check": lambda stats, **kw: stats.get("total_jumps", 0) >= 10000
    },

    # === SCORE ===
    {
        "id": "ach_score_500",
        "category": "score",
        "icon": "score",
        "check": lambda stats, **kw: kw.get("high_score", 0) >= 500
    },
    {
        "id": "ach_score_1000",
        "category": "score",
        "icon": "score",
        "check": lambda stats, **kw: kw.get("high_score", 0) >= 1000
    },
    {
        "id": "ach_score_5000",
        "category": "score",
        "icon": "score",
        "check": lambda stats, **kw: kw.get("high_score", 0) >= 5000
    },
    {
        "id": "ach_score_10000",
        "category": "score",
        "icon": "score",
        "check": lambda stats, **kw: kw.get("high_score", 0) >= 10000
    },
    {
        "id": "ach_score_50000",
        "category": "score",
        "icon": "score",
        "check": lambda stats, **kw: kw.get("high_score", 0) >= 50000
    },

    # === ENEMIES ===
    {
        "id": "ach_first_kill",
        "category": "enemies",
        "icon": "kill",
        "check": lambda stats, **kw: stats.get("total_kills", 0) >= 1
    },
    {
        "id": "ach_10_kills",
        "category": "enemies",
        "icon": "kill",
        "check": lambda stats, **kw: stats.get("total_kills", 0) >= 10
    },
    {
        "id": "ach_50_kills",
        "category": "enemies",
        "icon": "kill",
        "check": lambda stats, **kw: stats.get("total_kills", 0) >= 50
    },
    {
        "id": "ach_kill_all_types",
        "category": "enemies",
        "icon": "kill",
        "check": lambda stats, **kw: all(
            stats.get("enemies_killed_by_type", {}).get(t, 0) > 0
            for t in ["slug", "bat", "black_hole", "ghost",
                       "red_ball", "snake", "evil_cloud", "ufo"]
        )
    },
    {
        "id": "ach_5_kills_one_game",
        "category": "enemies",
        "icon": "kill",
        "check": lambda stats, **kw: kw.get("session_kills", 0) >= 5
    },

    # === COINS ===
    {
        "id": "ach_10_coins",
        "category": "coins",
        "icon": "coin",
        "check": lambda stats, **kw: stats.get("total_coins_collected", 0) >= 10
    },
    {
        "id": "ach_100_coins",
        "category": "coins",
        "icon": "coin",
        "check": lambda stats, **kw: stats.get("total_coins_collected", 0) >= 100
    },
    {
        "id": "ach_500_coins",
        "category": "coins",
        "icon": "coin",
        "check": lambda stats, **kw: stats.get("total_coins_collected", 0) >= 500
    },
    {
        "id": "ach_1000_coins",
        "category": "coins",
        "icon": "coin",
        "check": lambda stats, **kw: stats.get("total_coins_collected", 0) >= 1000
    },

    # === COMBO ===
    {
        "id": "ach_combo_3",
        "category": "combo",
        "icon": "combo",
        "check": lambda stats, **kw: stats.get("highest_combo", 0) >= 3
    },
    {
        "id": "ach_combo_5",
        "category": "combo",
        "icon": "combo",
        "check": lambda stats, **kw: stats.get("highest_combo", 0) >= 5
    },
    {
        "id": "ach_combo_10",
        "category": "combo",
        "icon": "combo",
        "check": lambda stats, **kw: stats.get("highest_combo", 0) >= 10
    },

    # === POWERUPS ===
    {
        "id": "ach_use_jetpack",
        "category": "powerups",
        "icon": "powerup",
        "check": lambda stats, **kw: stats.get("powerups_used", {}).get("jetpack", 0) >= 1
    },
    {
        "id": "ach_use_all_powerups",
        "category": "powerups",
        "icon": "powerup",
        "check": lambda stats, **kw: all(
            stats.get("powerups_used", {}).get(p, 0) > 0
            for p in ["spring", "jetpack", "blaster", "shield", "magnet"]
        )
    },
    {
        "id": "ach_10_springs",
        "category": "powerups",
        "icon": "powerup",
        "check": lambda stats, **kw: stats.get("powerups_used", {}).get("spring", 0) >= 10
    },

    # === SHOP ===
    {
        "id": "ach_first_purchase",
        "category": "shop",
        "icon": "shop",
        "check": lambda stats, **kw: stats.get("total_coins_spent", 0) > 0
    },
    {
        "id": "ach_buy_all",
        "category": "shop",
        "icon": "shop",
        "check": lambda stats, **kw: kw.get("all_purchased", False)
    },
    {
        "id": "ach_save_500",
        "category": "shop",
        "icon": "coin",
        "check": lambda stats, **kw: kw.get("current_coins", 0) >= 500
    },

    # === PLATFORMS ===
    {
        "id": "ach_100_platforms",
        "category": "platforms",
        "icon": "platform",
        "check": lambda stats, **kw: stats.get("total_platforms_landed", 0) >= 100
    },
    {
        "id": "ach_50_breakable",
        "category": "platforms",
        "icon": "platform",
        "check": lambda stats, **kw: stats.get("total_breakable_broken", 0) >= 50
    },
    {
        "id": "ach_moving_platform",
        "category": "platforms",
        "icon": "platform",
        "check": lambda stats, **kw: kw.get("landed_moving", False)
    },

    # === STORY ===
    {
        "id": "ach_story_level_1",
        "category": "story",
        "icon": "story",
        "check": lambda stats, **kw: kw.get("story_progress", {}).get("unlocked_level", 1) > 1
    },
    {
        "id": "ach_story_complete",
        "category": "story",
        "icon": "story",
        "check": lambda stats, **kw: kw.get("story_progress", {}).get("unlocked_level", 1) > 5
    },
    {
        "id": "ach_story_all_stars",
        "category": "story",
        "icon": "story",
        "check": lambda stats, **kw: all(
            kw.get("story_progress", {}).get("stars", {}).get(str(i), 0) >= 3
            for i in range(1, 6)
        )
    },

    # === MISC ===
    {
        "id": "ach_10_games",
        "category": "misc",
        "icon": "misc",
        "check": lambda stats, **kw: stats.get("total_games", 0) >= 10
    },
    {
        "id": "ach_100_games",
        "category": "misc",
        "icon": "misc",
        "check": lambda stats, **kw: stats.get("total_games", 0) >= 100
    },
    {
        "id": "ach_fall_1000",
        "category": "misc",
        "icon": "misc",
        "check": lambda stats, **kw: stats.get("max_height_reached", 0) >= 1000
    },
    {
        "id": "ach_1_hour",
        "category": "misc",
        "icon": "misc",
        "check": lambda stats, **kw: stats.get("total_playtime_seconds", 0) >= 3600
    },
    {
        "id": "ach_change_language",
        "category": "misc",
        "icon": "misc",
        "check": lambda stats, **kw: kw.get("language_changed", False)
    },
    {
        "id": "ach_open_settings",
        "category": "misc",
        "icon": "misc",
        "check": lambda stats, **kw: kw.get("settings_opened", False)
    },
    {
        "id": "ach_create_level",
        "category": "misc",
        "icon": "misc",
        "check": lambda stats, **kw: kw.get("level_created", False)
    },
]

# Categories for display grouping
ACHIEVEMENT_CATEGORIES = [
    ("jumps", "Jumps / Прыжки"),
    ("score", "Score / Очки"),
    ("enemies", "Enemies / Враги"),
    ("coins", "Coins / Монеты"),
    ("combo", "Combo / Комбо"),
    ("powerups", "Powerups / Бонусы"),
    ("shop", "Shop / Магазин"),
    ("platforms", "Platforms / Платформы"),
    ("story", "Story / Сюжет"),
    ("misc", "Misc / Разное"),
]


class AchievementNotification:
    """A popup notification for newly unlocked achievement."""

    def __init__(self, achievement_id):
        self.achievement_id = achievement_id
        self.timer = 0
        self.duration = 3.0
        self.alive = True

        # Animation
        self.slide_in_time = 0.3
        self.slide_out_time = 0.3
        self.hold_time = self.duration - self.slide_in_time - self.slide_out_time

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.alive = False

    def get_y_offset(self):
        """Get vertical offset for slide animation."""
        if self.timer < self.slide_in_time:
            # Slide in from top
            progress = self.timer / self.slide_in_time
            return -60 + 60 * progress
        elif self.timer > self.duration - self.slide_out_time:
            # Slide out to top
            progress = (self.timer - (self.duration - self.slide_out_time)) / self.slide_out_time
            return -60 * progress
        return 0

    def get_alpha(self):
        if self.timer < self.slide_in_time:
            return int(255 * (self.timer / self.slide_in_time))
        elif self.timer > self.duration - self.slide_out_time:
            remaining = self.duration - self.timer
            return int(255 * (remaining / self.slide_out_time))
        return 255


class AchievementManager:
    """Checks and manages achievements."""

    def __init__(self):
        self.notifications = []
        self.pending_checks = {}  # Extra context for achievement checks

        # Tracking flags that don't go into stats
        self._language_changed = False
        self._settings_opened = False
        self._level_created = False
        self._landed_on_moving = False
        self._session_kills = 0

    def reset_session(self):
        """Reset per-game session tracking."""
        self._session_kills = 0
        self._landed_on_moving = False

    def flag(self, flag_name, value=True):
        """Set a tracking flag."""
        if flag_name == "language_changed":
            self._language_changed = value
        elif flag_name == "settings_opened":
            self._settings_opened = value
        elif flag_name == "level_created":
            self._level_created = value
        elif flag_name == "landed_moving":
            self._landed_on_moving = value

    def add_session_kill(self):
        """Track a kill in current session."""
        self._session_kills += 1

    def check_all(self, current_score=0):
        """Check all achievements and unlock any newly earned ones.
        Returns list of newly unlocked achievement IDs.
        """
        stats = save_manager.statistics
        newly_unlocked = []

        # Build context dict
        from settings import (SHOP_SKINS, SHOP_TRAILS, SHOP_THEMES)

        # Check if all items purchased
        all_skins = all(save_manager.is_unlocked("skins", s) for s in SHOP_SKINS)
        all_trails = all(save_manager.is_unlocked("trails", t) for t in SHOP_TRAILS)
        all_themes = all(save_manager.is_unlocked("themes", t) for t in SHOP_THEMES)
        all_purchased = all_skins and all_trails and all_themes

        context = {
            "high_score": max(save_manager.high_score, current_score),
            "current_coins": save_manager.coins,
            "all_purchased": all_purchased,
            "session_kills": self._session_kills,
            "landed_moving": self._landed_on_moving,
            "story_progress": save_manager.story_progress,
            "language_changed": self._language_changed,
            "settings_opened": self._settings_opened,
            "level_created": self._level_created,
        }

        for ach_def in ACHIEVEMENT_DEFS:
            ach_id = ach_def["id"]

            # Skip already unlocked
            if save_manager.is_achievement_unlocked(ach_id):
                continue

            # Check condition
            try:
                if ach_def["check"](stats, **context):
                    is_new = save_manager.unlock_achievement(ach_id)
                    if is_new:
                        newly_unlocked.append(ach_id)
                        self.notifications.append(
                            AchievementNotification(ach_id)
                        )
            except Exception as e:
                pass  # Silently skip broken achievement checks

        return newly_unlocked

    def update(self, dt):
        """Update notification animations."""
        for notif in self.notifications:
            notif.update(dt)
        self.notifications = [n for n in self.notifications if n.alive]

    def draw_notifications(self, surface, screen_width):
        """Draw achievement unlock notifications."""
        from renderer import font_manager
        from localization import get_text

        for i, notif in enumerate(self.notifications):
            y_offset = notif.get_y_offset() + i * 65
            alpha = notif.get_alpha()

            if alpha <= 0:
                continue

            # Notification box
            box_width = min(300, screen_width - 20)
            box_height = 55
            box_x = screen_width // 2 - box_width // 2
            box_y = 10 + int(y_offset)

            # Background
            bg_surf = create_surface_with_alpha(box_width, box_height)
            pygame.draw.rect(bg_surf, (40, 40, 60, min(220, alpha)),
                             (0, 0, box_width, box_height), border_radius=10)
            pygame.draw.rect(bg_surf, (255, 200, 50, alpha),
                             (0, 0, box_width, box_height), width=2, border_radius=10)
            surface.blit(bg_surf, (box_x, box_y))

            # Trophy icon
            from renderer import sprite_renderer
            icon_size = 30
            icon_x = box_x + 10
            icon_y = box_y + box_height // 2 - icon_size // 2
            sprite_renderer.draw_achievement_icon(surface, icon_x, icon_y,
                                                   icon_size, unlocked=True)

            # Text
            ach_name = get_text(notif.achievement_id)
            unlocked_text = get_text("achievements_unlocked")

            name_font = font_manager.get_font(16)
            unlock_font = font_manager.get_font(12)

            name_surf = name_font.render(ach_name, True, (255, 255, 255))
            name_surf.set_alpha(alpha)
            unlock_surf = unlock_font.render(unlocked_text, True, (255, 200, 50))
            unlock_surf.set_alpha(alpha)

            text_x = icon_x + icon_size + 10
            surface.blit(unlock_surf, (text_x, box_y + 8))
            surface.blit(name_surf, (text_x, box_y + 25))

    def get_total_count(self):
        """Get total number of achievements."""
        return len(ACHIEVEMENT_DEFS)

    def get_unlocked_count(self):
        """Get number of unlocked achievements."""
        return sum(
            1 for ach in ACHIEVEMENT_DEFS
            if save_manager.is_achievement_unlocked(ach["id"])
        )

    def get_progress_percent(self):
        """Get percentage of achievements unlocked."""
        total = self.get_total_count()
        if total == 0:
            return 0
        return int(self.get_unlocked_count() / total * 100)

    def get_achievements_by_category(self):
        """Get achievements grouped by category."""
        result = {}
        for cat_id, cat_name in ACHIEVEMENT_CATEGORIES:
            result[cat_id] = {
                "name": cat_name,
                "achievements": [
                    ach for ach in ACHIEVEMENT_DEFS
                    if ach.get("category") == cat_id
                ]
            }
        return result
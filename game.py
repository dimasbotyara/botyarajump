"""
botyarajump - Game
Main game logic, state management, and gameplay loop.
"""

import pygame
import math
import time
import json
import os

from settings import save_manager, DEFAULT_WIDTH, DEFAULT_HEIGHT, STORY_LEVELS_DIR
from localization import get_text
from renderer import font_manager, sprite_renderer
from camera import Camera
from player import Player
from platforms import PlatformManager
from enemies import EnemyManager
from powerups import PowerupManager
from coins import CoinManager
from boosters import BoosterManager
from combo import ComboSystem
from particles import ParticleSystem
from achievements import AchievementManager
from ui import UI, UIState
from shop import Shop
from utils import (
    create_surface_with_alpha, draw_text_with_alpha,
    format_time, key_name_to_key
)


class GameState:
    """Possible game states."""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    STORY_PLAYING = "story_playing"
    EDITOR = "editor"


class Game:
    """Main game class. Manages everything."""

    def __init__(self):
        """Initialize the game."""
        pygame.init()

        # Virtual resolution (internal game logic)
        self.virtual_w, self.virtual_h = save_manager.get_resolution()
        self.screen_width = self.virtual_w
        self.screen_height = self.virtual_h

        # Window resolution (actual OS window)
        self.window_w, self.window_h = self.virtual_w, self.virtual_h

        flags = pygame.RESIZABLE
        if save_manager.is_fullscreen():
            flags |= pygame.FULLSCREEN

        self.window = pygame.display.set_mode((self.window_w, self.window_h), flags)
        pygame.display.set_caption("botyarajump")

        # Internal drawing surface (fixed size)
        self.screen = pygame.Surface((self.virtual_w, self.virtual_h)).convert()

        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60

        # Game state
        self.state = GameState.MENU

        # Core systems
        self.camera = Camera(self.screen_width, self.screen_height)
        self.player = Player(
            self.screen_width // 2 - 20,
            self.screen_height - 100,
            self.screen_width
        )
        self.platform_manager = PlatformManager(self.screen_width, self.screen_height)
        self.enemy_manager = EnemyManager(self.screen_width, self.screen_height)
        self.powerup_manager = PowerupManager(self.screen_width, self.screen_height)
        self.coin_manager = CoinManager(self.screen_width, self.screen_height)
        self.booster_manager = BoosterManager()
        self.combo = ComboSystem()
        self.particles = ParticleSystem()
        self.achievement_manager = AchievementManager()

        # UI
        self.ui = UI(self.screen_width, self.screen_height)
        self.shop = Shop(self.screen_width, self.screen_height)

        # Level editor (lazy import)
        self._level_editor = None

        # Score and game session
        self.score = 0
        self.coins_this_game = 0
        self.game_start_time = 0
        self.session_playtime = 0

        # Story mode
        self.story_level = None
        self.story_level_data = None
        self.story_finish_y = 0

        # Custom level
        self.custom_level_data = None

        # Pause keys
        self._pause_keys = []
        self._update_pause_keys()

        # Achievement check timer
        self._last_ach_check = 0.0

        # Booster callback
        self.booster_manager.on_activate = self._on_booster_activate

        # First run - show language select
        if save_manager.data.get("achievements", {}) == {}:
            self.ui.state = UIState.LANGUAGE_SELECT
        else:
            self.ui.state = UIState.MAIN_MENU

        # FPS tracking
        self._fps_display = 0
        self._fps_timer = 0

    def _update_pause_keys(self):
        """Cache pause key bindings."""
        controls = save_manager.get_controls()
        self._pause_keys = []
        for key_name in controls.get("pause", ["K_ESCAPE", "K_p"]):
            k = key_name_to_key(key_name)
            if k is not None:
                self._pause_keys.append(k)

    def start_new_game(self, mode_id="classic"):
        """Start a new endless game with specified mode."""
        self.current_mode = mode_id
        self.state = GameState.PLAYING
        self.ui.state = UIState.PLAYING
        self.score = 0
        self.coins_this_game = 0
        self.game_start_time = time.time()
        self.session_playtime = 0
        self._last_ach_check = 0.0
        self.story_level = None
        self.story_level_data = None
        self.custom_level_data = None

        # Reset mode parameters
        self.lava_y = self.screen_height
        self.time_left = 30.0
        self.gravity_timer = 15.0
        self.gravity_mode = "normal"
        self.icicle_timer = 0.0

        import settings
        settings.GRAVITY = 0.5

        # Reset all systems
        self.camera.reset()
        self.player.reset(
            self.screen_width // 2 - 20,
            self.screen_height - 100
        )
        self.platform_manager.reset()

        if mode_id == "hardcore":
            self.platform_manager.spring_chance = 0
            self.platform_manager.portal_chance = 0
            self.platform_manager.moving_chance = 0.25
        elif mode_id == "ice":
            self.platform_manager.ice_chance = 1.0
        elif mode_id == "boss":
            self.enemy_manager.spawn_chance = 0.14

        self.enemy_manager.reset()
        self.powerup_manager.reset()
        self.coin_manager.reset()
        self.booster_manager.reset()
        self.combo.reset()
        self.particles.reset()
        self.achievement_manager.reset_session()

        self._update_pause_keys()

        # Stats
        save_manager.add_stat("total_games")

    def start_story_level(self, level_num):
        """Start a story mode level."""
        level_path = os.path.join(STORY_LEVELS_DIR, f"level_{level_num}.json")

        if not os.path.exists(level_path):
            return False

        try:
            with open(level_path, 'r', encoding='utf-8') as f:
                level_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return False

        self.story_level = level_num
        self.story_level_data = level_data
        self._load_level(level_data)
        self.state = GameState.STORY_PLAYING
        self.ui.state = UIState.STORY_PLAYING
        return True

    def start_custom_level(self, level_info):
        """Start a custom level."""
        try:
            with open(level_info["filepath"], 'r', encoding='utf-8') as f:
                level_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return False

        self.custom_level_data = level_data
        self.story_level = None
        self._load_level(level_data)
        self.state = GameState.PLAYING
        self.ui.state = UIState.PLAYING
        return True

    def _load_level(self, level_data):
        """Load a level from JSON data."""
        self.score = 0
        self.coins_this_game = 0
        self.game_start_time = time.time()
        self.session_playtime = 0
        self._last_ach_check = 0.0

        self.camera.reset()

        # Find start position
        grid_size = level_data.get("grid_size", 32)
        start_x = self.screen_width // 2 - 20
        start_y = self.screen_height - 100

        for pdata in level_data.get("platforms", []):
            if pdata.get("is_start", False):
                start_x = pdata.get("x", 0) * grid_size
                start_y = pdata.get("y", 0) * grid_size - 50
                break

        self.player.reset(start_x, start_y)
        self.player.screen_width = self.screen_width

        self.platform_manager = PlatformManager(self.screen_width, self.screen_height)
        self.platform_manager.load_from_level_data(level_data)

        self.enemy_manager = EnemyManager(self.screen_width, self.screen_height)
        self.enemy_manager.load_from_level_data(level_data)

        self.powerup_manager = PowerupManager(self.screen_width, self.screen_height)
        self.powerup_manager.load_from_level_data(level_data)

        self.coin_manager = CoinManager(self.screen_width, self.screen_height)
        self.coin_manager.load_from_level_data(level_data)

        self.booster_manager.reset()
        self.combo.reset()
        self.particles.reset()
        self.achievement_manager.reset_session()

        self.story_finish_y = level_data.get("finish_y", 0) * grid_size
        save_manager.add_stat("total_games")

    def _on_booster_activate(self, booster_id):
        """Callback when a booster is activated."""
        if booster_id == "super_jump":
            self.player.activate_super_jump_booster()
            self.particles.emit_super_jump(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height
            )
            self.camera.shake(6, 0.2)

        elif booster_id == "shield":
            self.player.activate_shield_booster()
            self.particles.emit_powerup_collect(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height // 2,
                "shield"
            )

        elif booster_id == "slowmo":
            self.player.activate_slowmo()
            self.particles.emit_powerup_collect(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height // 2,
                "blaster"
            )

        elif booster_id == "bomb":
            killed = self.enemy_manager.kill_all_on_screen(self.camera)
            self.particles.emit_bomb(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height // 2
            )
            self.camera.shake(10, 0.5)

            for enemy in killed:
                self._on_enemy_killed(enemy)

    def _on_enemy_killed(self, enemy):
        """Handle enemy death effects."""
        self.particles.emit_enemy_death(
            enemy.x + enemy.width // 2,
            enemy.y + enemy.height // 2
        )

        self.coin_manager.spawn_from_enemy(
            enemy.x + enemy.width // 2,
            enemy.y + enemy.height // 2,
            count=max(1, enemy.score_value // 50)
        )

        actual_score = self.combo.add_kill(
            enemy.x + enemy.width // 2,
            enemy.y,
            enemy.score_value
        )
        self.score += actual_score

        save_manager.add_stat("total_kills")
        save_manager.add_nested_stat("enemies_killed_by_type", enemy.enemy_type)
        self.player.session_kills += 1
        self.achievement_manager.add_session_kill()

        self.achievement_manager.check_all(self.score)
        from daily_quests import quest_manager
        quest_manager.on_kill(1)
        if getattr(self, "current_mode", "classic") == "time_attack":
            self.time_left = min(60.0, self.time_left + 3.5)

    def update(self, dt):
        """Update game logic."""
        sprite_renderer.update(dt)
        self.ui.update(dt)

        if self.state in (GameState.PLAYING, GameState.STORY_PLAYING):
            self._update_gameplay(dt)
        elif self.state == GameState.GAME_OVER:
            self.particles.update(dt)
            self.player.update(dt)
            self.achievement_manager.update(dt)

        if self.ui.state == UIState.LEVEL_EDITOR and self._level_editor:
            self._level_editor.update(dt)

        self._fps_timer += dt
        if self._fps_timer >= 0.5:
            self._fps_display = self.clock.get_fps()
            self._fps_timer = 0

    def _update_gameplay(self, dt):
        """Update active gameplay."""
        self.session_playtime += dt
        save_manager.add_stat("total_playtime_seconds", dt)

        self.player.update(dt)
        self.camera.update(self.player.y, dt)

        if self.player.alive and self.player.is_falling():
            landed_platform = self.platform_manager.check_collision(self.player, dt)
            if landed_platform:
                from daily_quests import quest_manager
                quest_manager.on_platform(landed_platform.platform_type)

                self.particles.emit_jump(
                    self.player.x + self.player.width // 2,
                    self.player.y + self.player.height
                )

                if getattr(self, "current_mode", "classic") == "time_attack":
                    self.time_left = min(60.0, self.time_left + 0.3)

                if landed_platform.platform_type == "portal":
                    self.camera.shake(8, 0.35)
                    self.particles.emit_super_jump(
                        self.player.x + self.player.width // 2,
                        self.player.y + self.player.height
                    )
                elif landed_platform.platform_type == "spring":
                    self.camera.shake(4, 0.15)

                if landed_platform.platform_type == "moving":
                    self.achievement_manager.flag("landed_moving")

                if landed_platform.platform_type == "breakable":
                    self.particles.emit_platform_break(
                        landed_platform.x, landed_platform.y,
                        landed_platform.width
                    )

        if self.state == GameState.PLAYING:
            self.platform_manager.update(dt, self.camera)
        else:
            for p in self.platform_manager.platforms:
                if p.alive:
                    p.update(dt)

        self.enemy_manager.update(dt, self.player, self.camera)

        if self.player.alive and self.player.is_falling():
            stomped = self.enemy_manager.check_stomp_collision(self.player)
            for enemy in stomped:
                self._on_enemy_killed(enemy)
                self.camera.shake(5, 0.2)

        if self.player.bullets:
            bullet_kills = self.enemy_manager.check_bullet_collision(self.player.bullets)
            for enemy in bullet_kills:
                self._on_enemy_killed(enemy)

        if self.player.alive:
            took_damage = self.enemy_manager.check_damage_collision(self.player)
            if took_damage:
                died = self.player.take_damage()
                if died:
                    self._on_player_death()
                else:
                    self.particles.emit_shield_break(
                        self.player.x + self.player.width // 2,
                        self.player.y + self.player.height // 2
                    )
                    self.camera.shake(4, 0.2)

        self.powerup_manager.update(dt, self.player, self.camera)
        self.coin_manager.update(dt, self.player, self.camera)
        self.booster_manager.update(dt)
        self.combo.update(dt)
        self.particles.update(dt)

        trail = save_manager.equipped.get("trail", "none")
        if trail != "none" and self.player.alive:
            self.particles.update_trail(
                dt,
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height,
                trail
            )

        self.achievement_manager.update(dt)

        height_score = self.camera.get_score_from_height()
        diff = save_manager.get_difficulty_settings()
        self.score = max(self.score, int(height_score * diff["score_mult"]))

        new_coins = self.player.session_coins - self.coins_this_game
        if new_coins > 0:
            from daily_quests import quest_manager
            quest_manager.on_coin(new_coins)
            if getattr(self, "current_mode", "classic") == "time_attack":
                self.time_left = min(60.0, self.time_left + new_coins * 1.2)
        self.coins_this_game = self.player.session_coins

        from daily_quests import quest_manager
        quest_manager.on_score(self.score)

        # Mode mechanics updates
        mode = getattr(self, "current_mode", "classic")

        if mode == "lava":
            height_climbed = max(0, self.screen_height - self.camera.y_offset)
            spd = 0.8 + (height_climbed / 4500.0)
            self.lava_y -= spd * dt * 60
            if self.player.alive and self.player.y + self.player.height >= self.lava_y:
                self.player.alive = False
                self._on_player_death()

        elif mode == "time_attack":
            if self.player.alive:
                self.time_left -= dt
                if self.time_left <= 0:
                    self.time_left = 0
                    self.player.alive = False
                    self._on_player_death()

        elif mode == "gravity":
            self.gravity_timer -= dt
            if self.gravity_timer <= 0:
                self.gravity_timer = 15.0
                self.gravity_mode = random.choice(["normal", "low", "heavy", "hyper"])
                import settings
                if self.gravity_mode == "low":
                    settings.GRAVITY = 0.25
                elif self.gravity_mode == "heavy":
                    settings.GRAVITY = 0.85
                else:
                    settings.GRAVITY = 0.5
                self.camera.shake(4, 0.2)

        elif mode == "ice" and self.player.alive:
            self.icicle_timer += dt
            if self.icicle_timer >= 2.2:
                self.icicle_timer = 0
                rx = random.randint(30, self.screen_width - 30)
                from enemies import create_enemy, Enemy
                hazard = create_enemy(Enemy.RED_BALL, rx, self.camera.y_offset - 40)
                self.enemy_manager.enemies.append(hazard)

        if self.player.alive and self.camera.is_below_death_line(self.player.y):
            self.player.alive = False
            self._on_player_death()

        if self.state == GameState.STORY_PLAYING and self.player.alive:
            if self.player.y <= self.story_finish_y:
                self._on_story_level_complete()

        if self.session_playtime - self._last_ach_check >= 5.0:
            self._last_ach_check = self.session_playtime
            self.achievement_manager.check_all(self.score)

    def _on_player_death(self):
        """Handle player death."""
        import settings
        settings.GRAVITY = 0.5

        self.particles.emit_death(
            self.player.x + self.player.width // 2,
            self.player.y + self.player.height // 2
        )
        self.camera.shake(8, 0.4)

        self.player.vy = -5

        mode = getattr(self, "current_mode", "classic")
        save_manager.set_mode_high_score(mode, self.score)

        is_new_record = self.score > save_manager.high_score
        if is_new_record:
            save_manager.high_score = self.score

        save_manager.set_stat_max("max_height_reached", abs(int(self.camera.highest_y)))
        save_manager.set_stat_max("highest_combo", self.combo.max_combo_this_game)

        score_coins = self.score // 100
        total_coins = self.coins_this_game + score_coins
        save_manager.earn_coins(score_coins, persist=False)

        self.achievement_manager.check_all(self.score)

        self.ui.game_over_data = {
            "score": self.score,
            "high_score": save_manager.high_score,
            "coins_earned": total_coins,
            "is_new_record": is_new_record,
        }

        self.state = GameState.GAME_OVER
        self.ui.state = UIState.GAME_OVER

        save_manager.save()

    def _on_story_level_complete(self):
        """Handle story level completion."""
        star_scores = self.story_level_data.get("star_scores", [500, 1000, 2000])
        stars = 0
        for threshold in star_scores:
            if self.score >= threshold:
                stars += 1

        stars = max(1, stars)

        save_manager.complete_story_level(self.story_level, stars)
        self.achievement_manager.check_all(self.score)

        score_coins = self.score // 50
        save_manager.earn_coins(score_coins, persist=False)

        self.ui.game_over_data = {
            "score": self.score,
            "high_score": save_manager.high_score,
            "coins_earned": self.coins_this_game + score_coins,
            "is_new_record": False,
            "story_stars": stars,
            "story_level": self.story_level,
        }

        self.state = GameState.GAME_OVER
        self.ui.state = UIState.STORY_COMPLETE

        save_manager.save()

    def _map_mouse_coords(self, pos):
        """Translate window mouse coordinates to virtual screen coordinates."""
        mx, my = pos
        scale = min(self.window_w / self.virtual_w, self.window_h / self.virtual_h)
        scaled_w = self.virtual_w * scale
        scaled_h = self.virtual_h * scale
        offset_x = (self.window_w - scaled_w) / 2
        offset_y = (self.window_h - scaled_h) / 2

        vx = (mx - offset_x) / scale
        vy = (my - offset_y) / scale

        vx = max(0, min(self.virtual_w, vx))
        vy = max(0, min(self.virtual_h, vy))

        return (int(vx), int(vy))

    def handle_event(self, event):
        """Handle a single event based on current state."""
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.VIDEORESIZE:
            # Just update the OS window size, internal logic stays unchanged
            self.window_w = max(1, event.w)
            self.window_h = max(1, event.h)
            flags = pygame.RESIZABLE
            if save_manager.is_fullscreen():
                flags |= pygame.FULLSCREEN
            self.window = pygame.display.set_mode((self.window_w, self.window_h), flags)
            return

        ui_state = self.ui.state

        if ui_state == UIState.LANGUAGE_SELECT:
            if self.ui.handle_language_select(event):
                self.ui.state = UIState.MAIN_MENU
                self.achievement_manager.flag("language_changed")

        elif ui_state == UIState.MAIN_MENU:
            action = self.ui.handle_main_menu(event)
            if action:
                self._handle_menu_action(action)

        elif ui_state == UIState.PLAYING or ui_state == UIState.STORY_PLAYING:
            self._handle_gameplay_event(event)

        elif ui_state == UIState.PAUSED:
            action = self.ui.handle_pause(event)
            if action:
                self._handle_pause_action(action)

        elif ui_state == UIState.GAME_OVER or ui_state == UIState.STORY_COMPLETE:
            action = self.ui.handle_game_over(event)
            if action:
                self._handle_gameover_action(action)

        elif ui_state == UIState.SETTINGS:
            action = self.ui.handle_settings(event)
            if action:
                self._handle_settings_action(action)

        elif ui_state == UIState.CONTROLS:
            action = self.ui.handle_controls(event)
            if action:
                if action == "back":
                    self.ui.state = UIState.SETTINGS

        elif ui_state == UIState.SHOP:
            action = self.shop.handle_event(event)
            if action == "back":
                self.ui.state = UIState.MAIN_MENU

        elif ui_state == UIState.ACHIEVEMENTS:
            action = self.ui.handle_achievements(event)
            if action == "back":
                self.ui.state = UIState.MAIN_MENU

        elif ui_state == UIState.DAILY_QUESTS:
            action = self.ui.handle_daily_quests(event)
            if action == "back":
                self.ui.state = UIState.MAIN_MENU

        elif ui_state == UIState.STATISTICS:
            action = self.ui.handle_statistics(event)
            if action == "back":
                self.ui.state = UIState.MAIN_MENU

        elif ui_state == UIState.STORY_SELECT:
            action = self.ui.handle_story_select(event)
            if action == "back":
                self.ui.state = UIState.MAIN_MENU
            elif isinstance(action, int):
                if self.start_story_level(action):
                    self.state = GameState.STORY_PLAYING
                    self.ui.state = UIState.STORY_PLAYING

        elif ui_state == UIState.CUSTOM_LEVELS:
            action = self.ui.handle_custom_levels(event)
            if action == "back":
                self.ui.state = UIState.MAIN_MENU
            elif isinstance(action, dict):
                if self.start_custom_level(action):
                    self.state = GameState.PLAYING
                    self.ui.state = UIState.PLAYING

        elif ui_state == UIState.LEVEL_EDITOR:
            if self._level_editor:
                action = self._level_editor.handle_event(event)
                if action == "back":
                    self.ui.state = UIState.MAIN_MENU
                elif action == "test":
                    level_data = self._level_editor.export_level_data()
                    if level_data:
                        self.custom_level_data = level_data
                        self._load_level(level_data)
                        self.state = GameState.STORY_PLAYING
                        self.ui.state = UIState.STORY_PLAYING
                        self.story_level = None

    def _handle_menu_action(self, action):
        """Handle main menu button press."""
        if action == "play":
            self.ui.state = UIState.MODE_SELECT
        elif action == "story":
            self.ui.state = UIState.STORY_SELECT
        elif action == "shop":
            self.ui.state = UIState.SHOP
        elif action == "quests":
            self.ui.state = UIState.DAILY_QUESTS
        elif action == "achievements":
            self.achievement_manager.check_all(0)
            self.ui.state = UIState.ACHIEVEMENTS
        elif action == "statistics":
            self.ui.state = UIState.STATISTICS
        elif action == "editor":
            self._open_level_editor()
        elif action == "custom_levels":
            self.ui.refresh_custom_levels()
            self.ui.state = UIState.CUSTOM_LEVELS
        elif action == "settings":
            self.achievement_manager.flag("settings_opened")
            self.achievement_manager.check_all(0)
            self.ui.state = UIState.SETTINGS
        elif action == "quit":
            self.running = False

    def _handle_gameplay_event(self, event):
        """Handle events during gameplay."""
        if event.type == pygame.KEYDOWN:
            if event.key in self._pause_keys:
                self.state = GameState.PAUSED
                self.ui.state = UIState.PAUSED
                return

        # Mirror mode control swap
        if getattr(self, "current_mode", "classic") == "mirror" and event.type in (pygame.KEYDOWN, pygame.KEYUP):
            ev_dict = event.__dict__.copy()
            if event.key in self.player._left_keys and self.player._right_keys:
                ev_dict["key"] = self.player._right_keys[0]
            elif event.key in self.player._right_keys and self.player._left_keys:
                ev_dict["key"] = self.player._left_keys[0]
            swapped_event = pygame.event.Event(event.type, ev_dict)
            self.player.handle_event(swapped_event)
        else:
            self.player.handle_event(event)

        self.booster_manager.handle_event(event)

    def _handle_pause_action(self, action):
        """Handle pause menu action."""
        if action == "resume":
            self.state = GameState.PLAYING if not self.story_level else GameState.STORY_PLAYING
            self.ui.state = UIState.PLAYING if not self.story_level else UIState.STORY_PLAYING
        elif action == "restart":
            if self.story_level:
                self.start_story_level(self.story_level)
            else:
                self.start_new_game(getattr(self, "current_mode", "classic"))
        elif action == "menu":
            self.state = GameState.MENU
            self.ui.state = UIState.MAIN_MENU

    def _handle_gameover_action(self, action):
        """Handle game over action."""
        if action == "retry":
            if self.story_level:
                self.start_story_level(self.story_level)
            else:
                self.start_new_game(getattr(self, "current_mode", "classic"))
        elif action == "menu":
            self.state = GameState.MENU
            self.ui.state = UIState.MAIN_MENU

    def _handle_settings_action(self, action):
        """Handle settings action."""
        if action == "back":
            self.ui.state = UIState.MAIN_MENU
            save_manager.save()
        elif action == "controls":
            self.ui.state = UIState.CONTROLS
        elif action == "toggle_fullscreen":
            fs = save_manager.is_fullscreen()
            save_manager.set_fullscreen(not fs)
            new_fs = save_manager.is_fullscreen()
            flags = pygame.RESIZABLE
            if new_fs:
                flags |= pygame.FULLSCREEN
                info = pygame.display.Info()
                self.window_w = info.current_w
                self.window_h = info.current_h
            else:
                self.window_w, self.window_h = self.virtual_w, self.virtual_h
            self.window = pygame.display.set_mode((self.window_w, self.window_h), flags)

    def _open_level_editor(self):
        """Open level editor (lazy import)."""
        if self._level_editor is None:
            from level_editor import LevelEditor
            self._level_editor = LevelEditor(self.screen_width, self.screen_height)
        self._level_editor.reset()
        self.ui.state = UIState.LEVEL_EDITOR
        self.achievement_manager.flag("level_created")
        self.achievement_manager.check_all(0)

    def draw(self):
        """Draw current frame."""
        ui_state = self.ui.state

        # All drawing happens on the fixed virtual screen
        if ui_state == UIState.LANGUAGE_SELECT:
            self.ui.draw_language_select(self.screen)

        elif ui_state == UIState.MAIN_MENU:
            self.ui.draw_main_menu(self.screen)

        elif ui_state in (UIState.PLAYING, UIState.STORY_PLAYING):
            self._draw_gameplay()

        elif ui_state == UIState.PAUSED:
            self._draw_gameplay()
            self.ui.draw_pause(self.screen)

        elif ui_state in (UIState.GAME_OVER, UIState.STORY_COMPLETE):
            self._draw_gameplay()
            self.ui.draw_game_over(self.screen)

        elif ui_state == UIState.SETTINGS:
            self.ui.draw_settings(self.screen)

        elif ui_state == UIState.CONTROLS:
            self.ui.draw_controls(self.screen)

        elif ui_state == UIState.SHOP:
            self.shop.update(1 / 60)
            self.shop.draw(self.screen)

        elif ui_state == UIState.ACHIEVEMENTS:
            self.ui.draw_achievements(self.screen, self.achievement_manager)

        elif ui_state == UIState.DAILY_QUESTS:
            self.ui.draw_daily_quests(self.screen)

        elif ui_state == UIState.STATISTICS:
            self.ui.draw_statistics(self.screen)

        elif ui_state == UIState.STORY_SELECT:
            self.ui.draw_story_select(self.screen)

        elif ui_state == UIState.CUSTOM_LEVELS:
            self.ui.draw_custom_levels(self.screen)

        elif ui_state == UIState.LEVEL_EDITOR:
            if self._level_editor:
                self._level_editor.draw(self.screen)

        self.achievement_manager.draw_notifications(self.screen, self.screen_width)

        if save_manager.settings.get("show_fps", False):
            fps_font = font_manager.get_font(12)
            fps_text = f"FPS: {int(self._fps_display)}"
            fps_surf = fps_font.render(fps_text, True, (200, 200, 200))
            self.screen.blit(fps_surf, (self.screen_width - fps_surf.get_width() - 5, 2))

        # Scale virtual screen to actual window size with letterboxing
        self.window.fill((15, 15, 15))  # Dark grey borders

        scale = min(self.window_w / self.virtual_w, self.window_h / self.virtual_h)
        scaled_w = int(self.virtual_w * scale)
        scaled_h = int(self.virtual_h * scale)

        offset_x = (self.window_w - scaled_w) // 2
        offset_y = (self.window_h - scaled_h) // 2

        scaled_surface = pygame.transform.smoothscale(self.screen, (scaled_w, scaled_h))
        self.window.blit(scaled_surface, (offset_x, offset_y))

        pygame.display.flip()

    def _draw_gameplay(self):
        """Draw the game world."""
        theme = save_manager.equipped.get("theme", "day")
        sprite_renderer.draw_background(
            self.screen, theme,
            self.camera.get_y_offset(),
            self.screen_width, self.screen_height
        )

        self.platform_manager.draw(self.screen, self.camera, sprite_renderer)
        self.coin_manager.draw(self.screen, self.camera, sprite_renderer)
        self.powerup_manager.draw(self.screen, self.camera, sprite_renderer)
        self.enemy_manager.draw(self.screen, self.camera, sprite_renderer)
        self.particles.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera, sprite_renderer)

        # Mode Visual Overlays
        mode = getattr(self, "current_mode", "classic")
        if mode == "lava":
            lx, ly = self.camera.world_to_screen(0, self.lava_y)
            if ly < self.screen_height + 50:
                lava_h = max(20, self.screen_height + 100 - int(ly))
                lava_surf = create_surface_with_alpha(self.screen_width, lava_h)
                lava_surf.fill((230, 70, 20, 210))
                pygame.draw.rect(lava_surf, (255, 200, 50, 255), (0, 0, self.screen_width, 6))
                self.screen.blit(lava_surf, (0, int(ly)))

        elif mode == "dark":
            dark_overlay = create_surface_with_alpha(self.screen_width, self.screen_height)
            dark_overlay.fill((12, 12, 22, 235))
            px, py = self.camera.world_to_screen(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height // 2
            )
            pygame.draw.circle(dark_overlay, (0, 0, 0, 0), (int(px), int(py)), 115)
            self.screen.blit(dark_overlay, (0, 0))

        self.combo.draw_popups(self.screen, self.camera, sprite_renderer)

        self.ui.draw_hud(
            self.screen, self.score, self.coins_this_game,
            save_manager.get_mode_high_score(mode),
            abs(int(self.camera.highest_y))
        )

        # Mode HUD Banner
        if mode == "time_attack":
            t_font = font_manager.get_font(20)
            color = (255, 60, 60) if self.time_left < 6 else (255, 215, 0)
            t_surf = t_font.render(f"⏱️ {self.time_left:.1f}s", True, color)
            self.screen.blit(t_surf, (self.screen_width // 2 - t_surf.get_width() // 2, 35))

        elif mode == "gravity":
            g_font = font_manager.get_font(13)
            labels = {
                "normal": "🌀 Normal Gravity",
                "low": "🌕 Moon Gravity (Low)",
                "heavy": "🏋️ Heavy Gravity",
                "hyper": "⚡ Hyper Speed"
            }
            txt = labels.get(self.gravity_mode, "Gravity Chaos")
            g_surf = g_font.render(txt, True, (210, 170, 255))
            self.screen.blit(g_surf, (self.screen_width // 2 - g_surf.get_width() // 2, 38))

        elif mode == "mirror":
            m_font = font_manager.get_font(13)
            m_surf = m_font.render("🪞 MIRROR CONTROLS", True, (140, 220, 255))
            self.screen.blit(m_surf, (self.screen_width // 2 - m_surf.get_width() // 2, 38))

        self.combo.draw_hud(
            self.screen,
            self.screen_width // 2,
            self.screen_height - 60,
            save_manager.get_hud_opacity()
        )

        if self.booster_manager.has_any_booster():
            self._draw_booster_hud()

        if self.state == GameState.STORY_PLAYING and self.story_finish_y:
            self._draw_finish_line()

    def _draw_booster_hud(self):
        """Draw booster slots at bottom of screen."""
        opacity = save_manager.get_hud_opacity()
        slot_size = 45
        gap = 8
        total_w = 4 * slot_size + 3 * gap
        start_x = self.screen_width // 2 - total_w // 2
        y = self.screen_height - slot_size - 10

        for i in range(4):
            x = start_x + i * (slot_size + gap)
            info = self.booster_manager.get_slot_info(i)

            if info["is_empty"]:
                empty_surf = create_surface_with_alpha(slot_size, slot_size)
                pygame.draw.rect(empty_surf, (40, 40, 55, opacity // 2),
                                 (0, 0, slot_size, slot_size), border_radius=6)
                pygame.draw.rect(empty_surf, (60, 60, 75, opacity // 2),
                                 (0, 0, slot_size, slot_size), width=1, border_radius=6)
                self.screen.blit(empty_surf, (x, y))
            else:
                cd_pct = info["cooldown_pct"] if info["on_cooldown"] else 0
                sprite_renderer.draw_booster_icon(
                    self.screen, x, y, slot_size,
                    info["booster_id"], cd_pct
                )

                if info["uses"] > 0:
                    uses_font = font_manager.get_font(10)
                    uses_surf = uses_font.render(str(info["uses"]), True, (255, 255, 255))
                    uses_surf.set_alpha(opacity)
                    self.screen.blit(uses_surf, (x + slot_size - 12, y + 2))

                controls = save_manager.get_controls()
                key_name = controls.get(f"booster_{i + 1}", [""])[0]
                if key_name:
                    from localization import get_key_display_name
                    key_display = get_key_display_name(key_name)
                    key_font = font_manager.get_font(9)
                    key_surf = key_font.render(key_display, True, (180, 180, 200))
                    key_surf.set_alpha(opacity)
                    self.screen.blit(key_surf, (x + 2, y + slot_size - 12))

                if info["is_flashing"]:
                    flash_surf = create_surface_with_alpha(slot_size, slot_size)
                    pygame.draw.rect(flash_surf, (255, 255, 255, 80),
                                     (0, 0, slot_size, slot_size), border_radius=6)
                    self.screen.blit(flash_surf, (x, y))

    def _draw_finish_line(self):
        """Draw the finish line for story mode."""
        _, finish_screen_y = self.camera.world_to_screen(0, self.story_finish_y)
        finish_screen_y = int(finish_screen_y)

        if -50 < finish_screen_y < self.screen_height + 50:
            for x_pos in range(0, self.screen_width, 16):
                color = (255, 255, 255) if (x_pos // 16) % 2 == 0 else (0, 0, 0)
                pygame.draw.rect(self.screen, color, (x_pos, finish_screen_y, 16, 8))

            finish_font = font_manager.get_font(14)
            finish_text = "FINISH"
            finish_surf = finish_font.render(finish_text, True, (255, 255, 100))
            self.screen.blit(finish_surf,
                              (self.screen_width // 2 - finish_surf.get_width() // 2,
                               finish_screen_y - 20))

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.VIDEORESIZE:
                    self.handle_event(event)
                    continue

                # Translate mouse coordinates to virtual space
                if hasattr(event, 'pos'):
                    event.pos = self._map_mouse_coords(event.pos)

                self.handle_event(event)

            self.update(dt)
            self.draw()

        save_manager.save()
        pygame.quit()
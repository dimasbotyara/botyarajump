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

        # Screen setup
        self.screen_width, self.screen_height = save_manager.get_resolution()
        flags = pygame.RESIZABLE
        if save_manager.is_fullscreen():
            flags |= pygame.FULLSCREEN

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), flags
        )
        pygame.display.set_caption("botyarajump")

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

    def start_new_game(self):
        """Start a new endless game."""
        self.state = GameState.PLAYING
        self.ui.state = UIState.PLAYING
        self.score = 0
        self.coins_this_game = 0
        self.game_start_time = time.time()
        self.session_playtime = 0
        self.story_level = None
        self.story_level_data = None
        self.custom_level_data = None

        # Reset all systems
        self.camera.reset()
        self.player.reset(
            self.screen_width // 2 - 20,
            self.screen_height - 100
        )
        self.platform_manager.reset()
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
            # No level file - can't play
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

        self.camera.reset()

        # Find start position
        grid_size = level_data.get("grid_size", 32)
        start_x = self.screen_width // 2 - 20
        start_y = self.screen_height - 100

        # Look for start point in level data
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

        # Story finish line
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
        # Particles
        self.particles.emit_enemy_death(
            enemy.x + enemy.width // 2,
            enemy.y + enemy.height // 2
        )

        # Spawn coins
        self.coin_manager.spawn_from_enemy(
            enemy.x + enemy.width // 2,
            enemy.y + enemy.height // 2,
            count=max(1, enemy.score_value // 50)
        )

        # Combo
        actual_score = self.combo.add_kill(
            enemy.x + enemy.width // 2,
            enemy.y,
            enemy.score_value
        )
        self.score += actual_score

        # Stats
        save_manager.add_stat("total_kills")
        save_manager.add_nested_stat("enemies_killed_by_type", enemy.enemy_type)
        self.player.session_kills += 1
        self.achievement_manager.add_session_kill()

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

        # Update level editor
        if self.ui.state == UIState.LEVEL_EDITOR and self._level_editor:
            self._level_editor.update(dt)

        # FPS counter
        self._fps_timer += dt
        if self._fps_timer >= 0.5:
            self._fps_display = self.clock.get_fps()
            self._fps_timer = 0

    def _update_gameplay(self, dt):
        """Update active gameplay."""
        # Track playtime
        self.session_playtime += dt
        save_manager.add_stat("total_playtime_seconds", dt)

        # Update player
        self.player.update(dt)

        # Update camera
        self.camera.update(self.player.y, dt)

        # Platform collision
        if self.player.alive and self.player.is_falling():
            landed_platform = self.platform_manager.check_collision(self.player)
            if landed_platform:
                # Particles
                self.particles.emit_jump(
                    self.player.x + self.player.width // 2,
                    self.player.y + self.player.height
                )

                # Track moving platform achievement
                if landed_platform.platform_type == "moving":
                    self.achievement_manager.flag("landed_moving")

                # Platform break particles
                if landed_platform.platform_type == "breakable":
                    self.particles.emit_platform_break(
                        landed_platform.x, landed_platform.y,
                        landed_platform.width
                    )

        # Update platforms
        if self.state == GameState.PLAYING:
            self.platform_manager.update(dt, self.camera)
        else:
            # Story mode - don't generate new platforms
            for p in self.platform_manager.platforms:
                if p.alive:
                    p.update(dt)

        # Update enemies
        self.enemy_manager.update(dt, self.player, self.camera)

        # Enemy stomp
        if self.player.alive and self.player.is_falling():
            stomped = self.enemy_manager.check_stomp_collision(self.player)
            for enemy in stomped:
                self._on_enemy_killed(enemy)

        # Bullet hits
        if self.player.bullets:
            bullet_kills = self.enemy_manager.check_bullet_collision(self.player.bullets)
            for enemy in bullet_kills:
                self._on_enemy_killed(enemy)

        # Enemy damage to player
        if self.player.alive:
            took_damage = self.enemy_manager.check_damage_collision(self.player)
            if took_damage:
                died = self.player.take_damage()
                if died:
                    self._on_player_death()
                else:
                    # Shield absorbed hit
                    self.particles.emit_shield_break(
                        self.player.x + self.player.width // 2,
                        self.player.y + self.player.height // 2
                    )
                    self.camera.shake(4, 0.2)

        # Update powerups
        self.powerup_manager.update(dt, self.player, self.camera)

        # Update coins
        self.coin_manager.update(dt, self.player, self.camera)

        # Update boosters
        self.booster_manager.update(dt)

        # Update combo
        self.combo.update(dt)

        # Update particles
        self.particles.update(dt)

        # Trail particles
        trail = save_manager.equipped.get("trail", "none")
        if trail != "none" and self.player.alive:
            self.particles.update_trail(
                dt,
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height,
                trail
            )

        # Update achievements
        self.achievement_manager.update(dt)

        # Score from height
        height_score = self.camera.get_score_from_height()
        diff = save_manager.get_difficulty_settings()
        self.score = max(self.score, int(height_score * diff["score_mult"]))

        # Coins tracking
        self.coins_this_game = self.player.session_coins

        # Check death by falling
        if self.player.alive and self.camera.is_below_death_line(self.player.y):
            self.player.alive = False
            self._on_player_death()

        # Story mode: check if reached finish
        if self.state == GameState.STORY_PLAYING and self.player.alive:
            if self.player.y <= self.story_finish_y:
                self._on_story_level_complete()

        # Periodic achievement check
        if int(self.session_playtime) % 5 == 0 and self.session_playtime > 1:
            self.achievement_manager.check_all(self.score)

    def _on_player_death(self):
        """Handle player death."""
        self.particles.emit_death(
            self.player.x + self.player.width // 2,
            self.player.y + self.player.height // 2
        )
        self.camera.shake(8, 0.4)

        # Delay before showing game over
        self.player.vy = -5  # Small bounce

        # Save stats
        is_new_record = self.score > save_manager.high_score
        if is_new_record:
            save_manager.high_score = self.score

        save_manager.set_stat_max("max_height_reached", abs(int(self.camera.highest_y)))
        save_manager.set_stat_max("highest_combo", self.combo.max_combo_this_game)
        save_manager.save()

        # Calculate coins earned from score
        score_coins = self.score // 100
        total_coins = self.coins_this_game + score_coins
        save_manager.earn_coins(score_coins)

        # Final achievement check
        self.achievement_manager.check_all(self.score)

        # Prepare game over data
        self.ui.game_over_data = {
            "score": self.score,
            "high_score": save_manager.high_score,
            "coins_earned": total_coins,
            "is_new_record": is_new_record,
        }

        self.state = GameState.GAME_OVER
        self.ui.state = UIState.GAME_OVER

    def _on_story_level_complete(self):
        """Handle story level completion."""
        # Calculate stars based on score
        star_scores = self.story_level_data.get("star_scores", [500, 1000, 2000])
        stars = 0
        for threshold in star_scores:
            if self.score >= threshold:
                stars += 1

        stars = max(1, stars)  # At least 1 star for completing

        save_manager.complete_story_level(self.story_level, stars)

        # Achievement checks
        self.achievement_manager.check_all(self.score)

        # Coins from score
        score_coins = self.score // 50
        save_manager.earn_coins(score_coins)

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

    def handle_event(self, event):
        """Handle a single event based on current state."""
        # Global events
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.VIDEORESIZE:
            self.screen_width = event.w
            self.screen_height = event.h
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height), pygame.RESIZABLE
            )
            self.camera.screen_width = self.screen_width
            self.camera.screen_height = self.screen_height
            self.ui.resize(self.screen_width, self.screen_height)
            save_manager.set_resolution(self.screen_width, self.screen_height)
            return

        # Route to current UI state
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
                        # Use STORY_PLAYING so platforms don't generate infinitely
                        self.state = GameState.STORY_PLAYING
                        self.ui.state = UIState.STORY_PLAYING
                        self.story_level = None  # Not a real story level

    def _handle_menu_action(self, action):
        """Handle main menu button press."""
        if action == "play":
            self.start_new_game()
        elif action == "story":
            self.ui.state = UIState.STORY_SELECT
        elif action == "shop":
            self.ui.state = UIState.SHOP
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
        # Pause check
        if event.type == pygame.KEYDOWN:
            if event.key in self._pause_keys:
                self.state = GameState.PAUSED
                self.ui.state = UIState.PAUSED
                return

        # Player input
        self.player.handle_event(event)

        # Booster input
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
                self.start_new_game()
        elif action == "menu":
            self.state = GameState.MENU
            self.ui.state = UIState.MAIN_MENU

    def _handle_gameover_action(self, action):
        """Handle game over action."""
        if action == "retry":
            if self.story_level:
                self.start_story_level(self.story_level)
            else:
                self.start_new_game()
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
            if fs:
                self.screen = pygame.display.set_mode(
                    (self.screen_width, self.screen_height),
                    pygame.RESIZABLE | pygame.FULLSCREEN
                )
            else:
                self.screen = pygame.display.set_mode(
                    (self.screen_width, self.screen_height),
                    pygame.RESIZABLE
                )

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

        elif ui_state == UIState.STATISTICS:
            self.ui.draw_statistics(self.screen)

        elif ui_state == UIState.STORY_SELECT:
            self.ui.draw_story_select(self.screen)

        elif ui_state == UIState.CUSTOM_LEVELS:
            self.ui.draw_custom_levels(self.screen)

        elif ui_state == UIState.LEVEL_EDITOR:
            if self._level_editor:
                self._level_editor.draw(self.screen)

        # Achievement notifications (on top of everything)
        self.achievement_manager.draw_notifications(self.screen, self.screen_width)

        # FPS counter
        if save_manager.settings.get("show_fps", False):
            fps_font = font_manager.get_font(12)
            fps_text = f"FPS: {int(self._fps_display)}"
            fps_surf = fps_font.render(fps_text, True, (200, 200, 200))
            self.screen.blit(fps_surf, (self.screen_width - fps_surf.get_width() - 5, 2))

        pygame.display.flip()

    def _draw_gameplay(self):
        """Draw the game world."""
        # Background
        theme = save_manager.equipped.get("theme", "day")
        sprite_renderer.draw_background(
            self.screen, theme,
            self.camera.get_y_offset(),
            self.screen_width, self.screen_height
        )

        # Platforms
        self.platform_manager.draw(self.screen, self.camera, sprite_renderer)

        # Coins
        self.coin_manager.draw(self.screen, self.camera, sprite_renderer)

        # Powerups
        self.powerup_manager.draw(self.screen, self.camera, sprite_renderer)

        # Enemies
        self.enemy_manager.draw(self.screen, self.camera, sprite_renderer)

        # Particles (behind player)
        self.particles.draw(self.screen, self.camera)

        # Player
        self.player.draw(self.screen, self.camera, sprite_renderer)

        # Combo popups
        self.combo.draw_popups(self.screen, self.camera, sprite_renderer)

        # HUD
        self.ui.draw_hud(
            self.screen, self.score, self.coins_this_game,
            save_manager.high_score,
            abs(int(self.camera.highest_y))
        )

        # Combo HUD
        self.combo.draw_hud(
            self.screen,
            self.screen_width // 2,
            self.screen_height - 60,
            save_manager.get_hud_opacity()
        )

        # Booster HUD
        if self.booster_manager.has_any_booster():
            self._draw_booster_hud()

        # Story mode finish line
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
                # Empty slot
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

                # Uses remaining
                if info["uses"] > 0:
                    uses_font = font_manager.get_font(10)
                    uses_surf = uses_font.render(str(info["uses"]), True, (255, 255, 255))
                    uses_surf.set_alpha(opacity)
                    self.screen.blit(uses_surf, (x + slot_size - 12, y + 2))

                # Key hint
                controls = save_manager.get_controls()
                key_name = controls.get(f"booster_{i + 1}", [""])[0]
                if key_name:
                    from localization import get_key_display_name
                    key_display = get_key_display_name(key_name)
                    key_font = font_manager.get_font(9)
                    key_surf = key_font.render(key_display, True, (180, 180, 200))
                    key_surf.set_alpha(opacity)
                    self.screen.blit(key_surf, (x + 2, y + slot_size - 12))

                # Flash effect
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
            # Checkered line
            for x_pos in range(0, self.screen_width, 16):
                color = (255, 255, 255) if (x_pos // 16) % 2 == 0 else (0, 0, 0)
                pygame.draw.rect(self.screen, color, (x_pos, finish_screen_y, 16, 8))

            # Label
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
            dt = min(dt, 0.05)  # Cap delta time

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)
            self.draw()

        # Save before exit
        save_manager.save()
        pygame.quit()
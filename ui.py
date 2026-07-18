"""
botyarajump - UI System
Main menu, HUD, settings, pause screen, game over, statistics, custom levels.
"""

import pygame
import math
import os
import json

from settings import save_manager, DEFAULT_WIDTH, DEFAULT_HEIGHT, CUSTOM_LEVELS_DIR, STORY_LEVELS_DIR
from localization import get_text, get_key_display_name
from renderer import font_manager, sprite_renderer
from utils import (
    draw_rounded_rect, draw_text_with_alpha, draw_button,
    draw_slider, draw_toggle, point_in_rect, create_surface_with_alpha,
    format_time, open_folder, key_name_to_key, darken_color, lighten_color
)


class UIState:
    """Enum for UI screens."""
    LANGUAGE_SELECT = "language_select"
    MAIN_MENU = "main_menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    SETTINGS = "settings"
    CONTROLS = "controls"
    SHOP = "shop"
    ACHIEVEMENTS = "achievements"
    STATISTICS = "statistics"
    STORY_SELECT = "story_select"
    STORY_PLAYING = "story_playing"
    STORY_COMPLETE = "story_complete"
    LEVEL_EDITOR = "level_editor"
    CUSTOM_LEVELS = "custom_levels"


class Button:
    """Simple button helper."""

    def __init__(self, x, y, w, h, text, color=(80, 100, 140), text_color=(255, 255, 255),
                 font_size=18):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font_size = font_size
        self.hovered = False

    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface, alpha=255):
        draw_button(surface, self.text, font_manager.get_font(self.font_size),
                     (self.rect.x, self.rect.y, self.rect.w, self.rect.h),
                     self.color, self.text_color, self.hovered, alpha)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


class UI:
    """Main UI manager."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = UIState.LANGUAGE_SELECT

        # Settings rebind state
        self._rebinding = False
        self._rebind_action = None
        self._rebind_slot = None

        # Settings scroll
        self.settings_scroll = 0
        self.settings_max_scroll = 0

        # Achievements scroll
        self.ach_scroll = 0
        self.ach_max_scroll = 0

        # Stats scroll
        self.stats_scroll = 0

        # Custom levels list
        self.custom_level_files = []

        # Slider dragging
        self._dragging_slider = None

        # Stored game results for game over screen
        self.game_over_data = {}

        # Animation timers
        self._anim_time = 0
        self._menu_bg_offset = 0

    def update(self, dt):
        """Update UI animations."""
        self._anim_time += dt
        self._menu_bg_offset += dt * 20

    def resize(self, width, height):
        """Handle screen resize."""
        self.screen_width = width
        self.screen_height = height

    # ==================================================
    # LANGUAGE SELECT
    # ==================================================

    def draw_language_select(self, surface):
        """Draw language selection screen."""
        surface.fill((30, 30, 50))

        # Title
        title = "Select Language / Выберите язык"
        title_font = font_manager.get_font(24)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, 100))

        # Game logo text
        logo_font = font_manager.get_font(40)
        logo_surf = logo_font.render("botyarajump", True, (100, 220, 100))
        surface.blit(logo_surf,
                     (self.screen_width // 2 - logo_surf.get_width() // 2, 30))

        # English button
        btn_w = 200
        btn_h = 50
        btn_x = self.screen_width // 2 - btn_w // 2

        mx, my = pygame.mouse.get_pos()
        en_rect = pygame.Rect(btn_x, 200, btn_w, btn_h)
        ru_rect = pygame.Rect(btn_x, 270, btn_w, btn_h)

        draw_button(surface, "English", font_manager.get_font(20),
                     (btn_x, 200, btn_w, btn_h), (60, 100, 160),
                     hover=en_rect.collidepoint(mx, my))

        draw_button(surface, "Русский", font_manager.get_font(20),
                     (btn_x, 270, btn_w, btn_h), (60, 100, 160),
                     hover=ru_rect.collidepoint(mx, my))

    def handle_language_select(self, event):
        """Handle language selection. Returns True if language selected."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            btn_w = 200
            btn_x = self.screen_width // 2 - btn_w // 2

            if pygame.Rect(btn_x, 200, btn_w, 50).collidepoint(mx, my):
                save_manager.set_language("en")
                return True
            elif pygame.Rect(btn_x, 270, btn_w, 50).collidepoint(mx, my):
                save_manager.set_language("ru")
                return True
        return False

    # ==================================================
    # MAIN MENU
    # ==================================================

    def draw_main_menu(self, surface):
        """Draw main menu."""
        # Animated background
        theme = save_manager.equipped.get("theme", "day")
        sprite_renderer.draw_background(surface, theme, self._menu_bg_offset,
                                         self.screen_width, self.screen_height)

        # Darken overlay
        overlay = create_surface_with_alpha(self.screen_width, self.screen_height)
        overlay.fill((0, 0, 0, 80))
        surface.blit(overlay, (0, 0))

        # Title with bounce
        bounce = math.sin(self._anim_time * 2) * 5
        logo_font = font_manager.get_font(42)
        logo_surf = logo_font.render("botyarajump", True, (100, 220, 100))
        surface.blit(logo_surf,
                     (self.screen_width // 2 - logo_surf.get_width() // 2,
                      30 + int(bounce)))

        # High score
        hs_font = font_manager.get_font(16)
        hs_text = f"{get_text('hud_high_score')}: {save_manager.high_score}"
        hs_surf = hs_font.render(hs_text, True, (255, 215, 0))
        surface.blit(hs_surf,
                     (self.screen_width // 2 - hs_surf.get_width() // 2, 80))

        # Coins
        coins_text = f"{save_manager.coins} coins"
        coins_surf = hs_font.render(coins_text, True, (255, 215, 0))
        surface.blit(coins_surf,
                     (self.screen_width // 2 - coins_surf.get_width() // 2, 100))

        # Menu buttons
        btn_w = 220
        btn_h = 42
        btn_x = self.screen_width // 2 - btn_w // 2
        start_y = 140
        gap = 50

        mx, my = pygame.mouse.get_pos()

        buttons = [
            (get_text("menu_play"), (60, 140, 60)),
            (get_text("menu_story"), (60, 100, 140)),
            (get_text("menu_shop"), (140, 100, 40)),
            (get_text("menu_achievements"), (120, 80, 140)),
            (get_text("menu_statistics"), (80, 100, 120)),
            (get_text("menu_editor"), (100, 80, 60)),
            (get_text("menu_custom_levels"), (80, 80, 100)),
            (get_text("menu_settings"), (80, 80, 100)),
            (get_text("menu_quit"), (120, 50, 50)),
        ]

        self._menu_buttons = []
        for i, (text, color) in enumerate(buttons):
            y = start_y + i * gap
            rect = pygame.Rect(btn_x, y, btn_w, btn_h)
            hover = rect.collidepoint(mx, my)
            draw_button(surface, text, font_manager.get_font(16),
                        (btn_x, y, btn_w, btn_h), color, hover=hover)
            self._menu_buttons.append(rect)

    def handle_main_menu(self, event):
        """Handle main menu clicks. Returns action string or None."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            actions = [
                "play", "story", "shop", "achievements", "statistics",
                "editor", "custom_levels", "settings", "quit"
            ]
            for i, rect in enumerate(self._menu_buttons):
                if rect.collidepoint(mx, my):
                    return actions[i]
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "play"
            if event.key == pygame.K_ESCAPE:
                return "quit"
        return None

    # ==================================================
    # HUD (in-game)
    # ==================================================

    def draw_hud(self, surface, score, coins_session, high_score, height):
        """Draw in-game HUD."""
        opacity = save_manager.get_hud_opacity()
        if opacity <= 0:
            return

        font = font_manager.get_font(18)
        small_font = font_manager.get_font(14)

        # Score (top left)
        score_text = f"{get_text('hud_score')}: {score}"
        draw_text_with_alpha(surface, score_text, font, (255, 255, 255),
                              10, 10, opacity)

        # High score
        hs_text = f"{get_text('hud_high_score')}: {high_score}"
        draw_text_with_alpha(surface, hs_text, small_font, (200, 200, 200),
                              10, 32, opacity)

        # Coins (top right)
        coins_text = f"{coins_session}"
        coin_font = font_manager.get_font(18)
        coin_surf = coin_font.render(coins_text, True, (255, 215, 0))
        coin_surf.set_alpha(opacity)
        coin_x = self.screen_width - coin_surf.get_width() - 30
        surface.blit(coin_surf, (coin_x, 10))

        # Small coin icon
        sprite_renderer.draw_coin(surface, self.screen_width - 24, 8, 16)

    # ==================================================
    # PAUSE
    # ==================================================

    def draw_pause(self, surface):
        """Draw pause overlay."""
        # Darken background
        overlay = create_surface_with_alpha(self.screen_width, self.screen_height)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        # Title
        title = get_text("pause_title")
        title_font = font_manager.get_font(36)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, 150))

        # Buttons
        btn_w = 200
        btn_h = 45
        btn_x = self.screen_width // 2 - btn_w // 2
        mx, my = pygame.mouse.get_pos()

        buttons = [
            (get_text("pause_resume"), 260, (60, 140, 60)),
            (get_text("pause_restart"), 320, (140, 120, 40)),
            (get_text("pause_menu"), 380, (120, 50, 50)),
        ]

        self._pause_buttons = []
        for text, y, color in buttons:
            rect = pygame.Rect(btn_x, y, btn_w, btn_h)
            hover = rect.collidepoint(mx, my)
            draw_button(surface, text, font_manager.get_font(18),
                        (btn_x, y, btn_w, btn_h), color, hover=hover)
            self._pause_buttons.append(rect)

    def handle_pause(self, event):
        """Handle pause screen. Returns 'resume', 'restart', 'menu', or None."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            actions = ["resume", "restart", "menu"]
            for i, rect in enumerate(self._pause_buttons):
                if rect.collidepoint(mx, my):
                    return actions[i]

        if event.type == pygame.KEYDOWN:
            controls = save_manager.get_controls()
            pause_keys = controls.get("pause", ["K_ESCAPE", "K_p"])
            for key_name in pause_keys:
                k = key_name_to_key(key_name)
                if k and event.key == k:
                    return "resume"

        return None

    # ==================================================
    # GAME OVER
    # ==================================================

    def draw_game_over(self, surface):
        """Draw game over screen."""
        overlay = create_surface_with_alpha(self.screen_width, self.screen_height)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        data = self.game_over_data
        score = data.get("score", 0)
        high_score = data.get("high_score", 0)
        coins_earned = data.get("coins_earned", 0)
        is_new_record = data.get("is_new_record", False)

        y_pos = 100

        # Title
        title = get_text("gameover_title")
        title_font = font_manager.get_font(36)
        title_surf = title_font.render(title, True, (255, 80, 80))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, y_pos))
        y_pos += 60

        # Score
        score_font = font_manager.get_font(28)
        score_text = f"{get_text('gameover_score')}: {score}"
        score_surf = score_font.render(score_text, True, (255, 255, 255))
        surface.blit(score_surf,
                     (self.screen_width // 2 - score_surf.get_width() // 2, y_pos))
        y_pos += 40

        # New record
        if is_new_record:
            record_font = font_manager.get_font(22)
            record_text = get_text("gameover_new_record")
            # Pulsing color
            pulse = int(200 + 55 * math.sin(self._anim_time * 5))
            record_surf = record_font.render(record_text, True, (255, pulse, 50))
            surface.blit(record_surf,
                         (self.screen_width // 2 - record_surf.get_width() // 2, y_pos))
            y_pos += 35
        else:
            best_font = font_manager.get_font(18)
            best_text = f"{get_text('gameover_best')}: {high_score}"
            best_surf = best_font.render(best_text, True, (200, 200, 200))
            surface.blit(best_surf,
                         (self.screen_width // 2 - best_surf.get_width() // 2, y_pos))
            y_pos += 30

        # Coins earned
        coins_font = font_manager.get_font(20)
        coins_text = f"{get_text('gameover_coins_earned')}: {coins_earned}"
        coins_surf = coins_font.render(coins_text, True, (255, 215, 0))
        surface.blit(coins_surf,
                     (self.screen_width // 2 - coins_surf.get_width() // 2, y_pos))
        y_pos += 50

        # Buttons
        btn_w = 180
        btn_h = 45
        btn_x = self.screen_width // 2 - btn_w // 2
        mx, my = pygame.mouse.get_pos()

        retry_rect = pygame.Rect(btn_x, y_pos, btn_w, btn_h)
        menu_rect = pygame.Rect(btn_x, y_pos + 60, btn_w, btn_h)

        draw_button(surface, get_text("gameover_retry"), font_manager.get_font(18),
                     (btn_x, y_pos, btn_w, btn_h), (60, 140, 60),
                     hover=retry_rect.collidepoint(mx, my))

        draw_button(surface, get_text("gameover_menu"), font_manager.get_font(18),
                     (btn_x, y_pos + 60, btn_w, btn_h), (80, 80, 100),
                     hover=menu_rect.collidepoint(mx, my))

        self._gameover_retry_rect = retry_rect
        self._gameover_menu_rect = menu_rect

    def handle_game_over(self, event):
        """Handle game over screen. Returns 'retry', 'menu', or None."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if hasattr(self, '_gameover_retry_rect'):
                if self._gameover_retry_rect.collidepoint(mx, my):
                    return "retry"
            if hasattr(self, '_gameover_menu_rect'):
                if self._gameover_menu_rect.collidepoint(mx, my):
                    return "menu"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return "retry"
            if event.key == pygame.K_ESCAPE:
                return "menu"

        return None

    # ==================================================
    # SETTINGS
    # ==================================================

    def draw_settings(self, surface):
        """Draw settings screen."""
        surface.fill((30, 30, 50))

        # Title
        title = get_text("settings_title")
        title_font = font_manager.get_font(28)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, 15))

        # Back button
        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(10, 10, 80, 35)
        draw_button(surface, get_text("menu_back"), font_manager.get_font(14),
                     (10, 10, 80, 35), (80, 80, 100),
                     hover=back_rect.collidepoint(mx, my))

        # Settings items
        y = 70 - int(self.settings_scroll)
        item_h = 50
        pad = 5
        content_x = 20
        content_w = self.screen_width - 40
        label_font = font_manager.get_font(15)
        value_font = font_manager.get_font(14)

        self._settings_rects = {}

        # Clip to content area
        content_top = 60
        clip_rect = pygame.Rect(0, content_top, self.screen_width,
                                 self.screen_height - content_top)
        surface.set_clip(clip_rect)

        # --- Language ---
        lang = save_manager.get_language()
        lang_text = "English" if lang == "en" else "Русский"
        self._draw_setting_row(surface, content_x, y, content_w, item_h,
                                get_text("settings_language"), lang_text,
                                "language", label_font, value_font, mx, my)
        y += item_h + pad

        # --- Difficulty ---
        diff = save_manager.get_difficulty()
        diff_text = get_text(f"diff_{diff}")
        self._draw_setting_row(surface, content_x, y, content_w, item_h,
                                get_text("settings_difficulty"), diff_text,
                                "difficulty", label_font, value_font, mx, my)
        y += item_h + pad

        # --- HUD Opacity ---
        opacity = save_manager.get_hud_opacity()
        self._draw_setting_slider(surface, content_x, y, content_w, item_h,
                                   get_text("settings_hud_opacity"),
                                   opacity, 0, 255, "hud_opacity",
                                   label_font, mx, my)
        y += item_h + pad

        # --- Fullscreen ---
        fs = save_manager.is_fullscreen()
        self._draw_setting_toggle(surface, content_x, y, content_w, item_h,
                                   get_text("settings_fullscreen"),
                                   fs, "fullscreen", label_font, mx, my)
        y += item_h + pad

        # --- Show FPS ---
        fps = save_manager.settings.get("show_fps", False)
        self._draw_setting_toggle(surface, content_x, y, content_w, item_h,
                                   get_text("settings_show_fps"),
                                   fps, "show_fps", label_font, mx, my)
        y += item_h + pad

        # --- Controls button ---
        controls_rect = pygame.Rect(content_x, y, content_w, item_h)
        controls_hover = controls_rect.collidepoint(mx, my)
        draw_button(surface, get_text("settings_controls"), font_manager.get_font(16),
                     (content_x, y, content_w, item_h), (70, 80, 120),
                     hover=controls_hover)
        self._settings_rects["controls_btn"] = controls_rect
        y += item_h + pad

        # --- Reset ---
        reset_rect = pygame.Rect(content_x, y, content_w, item_h)
        reset_hover = reset_rect.collidepoint(mx, my)
        draw_button(surface, get_text("settings_reset"), font_manager.get_font(16),
                     (content_x, y, content_w, item_h), (140, 50, 50),
                     hover=reset_hover)
        self._settings_rects["reset_btn"] = reset_rect
        y += item_h + pad

        self.settings_max_scroll = max(0, y + int(self.settings_scroll) - self.screen_height + 20)

        surface.set_clip(None)

    def _draw_setting_row(self, surface, x, y, w, h, label, value,
                           key, label_font, value_font, mx, my):
        """Draw a settings row with clickable value."""
        rect = pygame.Rect(x, y, w, h)
        hover = rect.collidepoint(mx, my)
        bg = (55, 55, 75) if hover else (45, 45, 65)
        draw_rounded_rect(surface, bg, rect, 8)

        label_surf = label_font.render(label, True, (200, 200, 220))
        surface.blit(label_surf, (x + 10, y + h // 2 - label_surf.get_height() // 2))

        value_surf = value_font.render(value, True, (150, 200, 255))
        surface.blit(value_surf, (x + w - value_surf.get_width() - 10,
                                   y + h // 2 - value_surf.get_height() // 2))

        self._settings_rects[key] = rect

    def _draw_setting_slider(self, surface, x, y, w, h, label,
                              value, min_val, max_val, key, label_font, mx, my):
        """Draw a settings slider."""
        rect = pygame.Rect(x, y, w, h)
        bg = (45, 45, 65)
        draw_rounded_rect(surface, bg, rect, 8)

        label_surf = label_font.render(f"{label}: {int(value)}", True, (200, 200, 220))
        surface.blit(label_surf, (x + 10, y + 5))

        slider_x = x + 10
        slider_y = y + 28
        slider_w = w - 20
        slider_rect = draw_slider(surface, slider_x, slider_y, slider_w, 16,
                                   value, min_val, max_val)
        self._settings_rects[key] = pygame.Rect(slider_x, slider_y, slider_w, 16)

    def _draw_setting_toggle(self, surface, x, y, w, h, label,
                              value, key, label_font, mx, my):
        """Draw a settings toggle."""
        rect = pygame.Rect(x, y, w, h)
        hover = rect.collidepoint(mx, my)
        bg = (55, 55, 75) if hover else (45, 45, 65)
        draw_rounded_rect(surface, bg, rect, 8)

        label_surf = label_font.render(label, True, (200, 200, 220))
        surface.blit(label_surf, (x + 10, y + h // 2 - label_surf.get_height() // 2))

        toggle_x = x + w - 55
        toggle_y = y + h // 2 - 12
        draw_toggle(surface, toggle_x, toggle_y, 45, 24, value)

        self._settings_rects[key] = rect

    def handle_settings(self, event):
        """Handle settings interactions. Returns 'back' or None."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Back button
            if pygame.Rect(10, 10, 80, 35).collidepoint(mx, my):
                return "back"

            rects = getattr(self, '_settings_rects', {})

            # Language
            if "language" in rects and rects["language"].collidepoint(mx, my):
                lang = save_manager.get_language()
                new_lang = "ru" if lang == "en" else "en"
                save_manager.set_language(new_lang)
                from achievements import AchievementManager
                return None

            # Difficulty
            if "difficulty" in rects and rects["difficulty"].collidepoint(mx, my):
                diff = save_manager.get_difficulty()
                cycle = ["easy", "normal", "hard"]
                idx = cycle.index(diff) if diff in cycle else 1
                new_diff = cycle[(idx + 1) % len(cycle)]
                save_manager.settings["difficulty"] = new_diff
                save_manager.save()

            # Fullscreen
            if "fullscreen" in rects and rects["fullscreen"].collidepoint(mx, my):
                fs = save_manager.is_fullscreen()
                save_manager.set_fullscreen(not fs)
                return "toggle_fullscreen"

            # Show FPS
            if "show_fps" in rects and rects["show_fps"].collidepoint(mx, my):
                fps = save_manager.settings.get("show_fps", False)
                save_manager.settings["show_fps"] = not fps
                save_manager.save()

            # Controls
            if "controls_btn" in rects and rects["controls_btn"].collidepoint(mx, my):
                return "controls"

            # Reset
            if "reset_btn" in rects and rects["reset_btn"].collidepoint(mx, my):
                from settings import get_default_save_data
                defaults = get_default_save_data()
                save_manager.data["settings"] = defaults["settings"]
                save_manager.save()

            # HUD Opacity slider
            if "hud_opacity" in rects:
                slider_rect = rects["hud_opacity"]
                if slider_rect.collidepoint(mx, my):
                    self._dragging_slider = "hud_opacity"

        elif event.type == pygame.MOUSEBUTTONUP:
            self._dragging_slider = None

        elif event.type == pygame.MOUSEMOTION:
            if self._dragging_slider == "hud_opacity":
                rects = getattr(self, '_settings_rects', {})
                if "hud_opacity" in rects:
                    slider_rect = rects["hud_opacity"]
                    rel_x = event.pos[0] - slider_rect.x
                    pct = max(0, min(1, rel_x / slider_rect.width))
                    val = int(pct * 255)
                    save_manager.set_hud_opacity(val)

        elif event.type == pygame.MOUSEWHEEL:
            self.settings_scroll -= event.y * 20
            self.settings_scroll = max(0, min(self.settings_scroll, self.settings_max_scroll))

        return None

    # ==================================================
    # CONTROLS
    # ==================================================

    def draw_controls(self, surface):
        """Draw controls rebinding screen."""
        surface.fill((30, 30, 50))

        title = get_text("settings_controls")
        title_font = font_manager.get_font(24)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, 15))

        # Back button
        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(10, 10, 80, 35)
        draw_button(surface, get_text("menu_back"), font_manager.get_font(14),
                     (10, 10, 80, 35), (80, 80, 100),
                     hover=back_rect.collidepoint(mx, my))

        controls = save_manager.get_controls()
        actions = ["left", "right", "shoot", "pause",
                   "booster_1", "booster_2", "booster_3", "booster_4"]

        y = 60
        row_h = 45
        label_font = font_manager.get_font(14)
        key_font = font_manager.get_font(13)

        self._control_rects = {}

        for action in actions:
            label_key = f"control_{action}"
            label = get_text(label_key)

            bindings = controls.get(action, ["", ""])
            while len(bindings) < 2:
                bindings.append("")

            # Row background
            row_rect = pygame.Rect(10, y, self.screen_width - 20, row_h)
            draw_rounded_rect(surface, (45, 45, 65), row_rect, 6)

            # Label
            label_surf = label_font.render(label, True, (200, 200, 220))
            surface.blit(label_surf, (20, y + row_h // 2 - label_surf.get_height() // 2))

            # Slot buttons
            slot_w = 80
            for slot in range(2):
                slot_x = self.screen_width - 20 - (2 - slot) * (slot_w + 10)
                slot_rect = pygame.Rect(slot_x, y + 6, slot_w, row_h - 12)

                is_rebinding = (self._rebinding and self._rebind_action == action
                                and self._rebind_slot == slot)
                slot_hover = slot_rect.collidepoint(mx, my)

                if is_rebinding:
                    bg_color = (120, 80, 40)
                    text = get_text("press_key")
                elif slot_hover:
                    bg_color = (70, 70, 100)
                    text = get_key_display_name(bindings[slot])
                else:
                    bg_color = (55, 55, 80)
                    text = get_key_display_name(bindings[slot])

                draw_button(surface, text, key_font,
                             (slot_x, y + 6, slot_w, row_h - 12),
                             bg_color, border_radius=6)

                # Slot label
                slot_label = f"{get_text('slot')} {slot + 1}"
                slot_label_font = font_manager.get_font(9)
                slot_label_surf = slot_label_font.render(slot_label, True, (120, 120, 140))
                surface.blit(slot_label_surf, (slot_x + 2, y + 2))

                self._control_rects[(action, slot)] = slot_rect

            y += row_h + 4

    def handle_controls(self, event):
        """Handle controls screen. Returns 'back' or None."""
        if self._rebinding:
            if event.type == pygame.KEYDOWN:
                key_name = f"K_{pygame.key.name(event.key)}"
                # Normalize
                key_name = key_name.upper().replace(" ", "_")

                # Special keys
                key_map = {
                    "K_LEFT": "K_LEFT",
                    "K_RIGHT": "K_RIGHT",
                    "K_UP": "K_UP",
                    "K_DOWN": "K_DOWN",
                    "K_SPACE": "K_SPACE",
                    "K_RETURN": "K_RETURN",
                    "K_ESCAPE": "K_ESCAPE",
                    "K_TAB": "K_TAB",
                    "K_BACKSPACE": "K_BACKSPACE",
                    "K_LSHIFT": "K_LSHIFT",
                    "K_RSHIFT": "K_RSHIFT",
                    "K_LCTRL": "K_LCTRL",
                    "K_RCTRL": "K_RCTRL",
                    "K_LALT": "K_LALT",
                    "K_RALT": "K_RALT",
                }

                # Try to get proper name
                proper_name = pygame.key.name(event.key)
                final_name = f"K_{proper_name}"

                # Check known names
                for known_key, known_val in key_map.items():
                    if known_key.lower() == final_name.lower():
                        final_name = known_val
                        break

                save_manager.set_control(self._rebind_action, self._rebind_slot, final_name)
                self._rebinding = False
                self._rebind_action = None
                self._rebind_slot = None
                return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._rebinding:
                    self._rebinding = False
                else:
                    return "back"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Back button
            if pygame.Rect(10, 10, 80, 35).collidepoint(mx, my):
                return "back"

            # Slot buttons
            for (action, slot), rect in getattr(self, '_control_rects', {}).items():
                if rect.collidepoint(mx, my):
                    self._rebinding = True
                    self._rebind_action = action
                    self._rebind_slot = slot
                    return None

        return None

    # ==================================================
    # ACHIEVEMENTS SCREEN
    # ==================================================

    def draw_achievements(self, surface, achievement_manager):
        """Draw achievements screen."""
        surface.fill((30, 30, 50))

        # Title
        total = achievement_manager.get_total_count()
        unlocked = achievement_manager.get_unlocked_count()
        pct = achievement_manager.get_progress_percent()

        title = f"{get_text('achievements_title')} ({unlocked}/{total} - {pct}%)"
        title_font = font_manager.get_font(20)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, 15))

        # Back button
        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(10, 10, 80, 35)
        draw_button(surface, get_text("menu_back"), font_manager.get_font(14),
                     (10, 10, 80, 35), (80, 80, 100),
                     hover=back_rect.collidepoint(mx, my))

        # Progress bar
        bar_x = 20
        bar_y = 45
        bar_w = self.screen_width - 40
        bar_h = 8
        pygame.draw.rect(surface, (60, 60, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * pct / 100)
        if fill_w > 0:
            pygame.draw.rect(surface, (255, 200, 50), (bar_x, bar_y, fill_w, bar_h),
                              border_radius=4)

        # Achievement list
        by_category = achievement_manager.get_achievements_by_category()
        y = 65 - int(self.ach_scroll)
        item_h = 55
        pad = 4
        name_font = font_manager.get_font(14)
        desc_font = font_manager.get_font(11)

        clip_rect = pygame.Rect(0, 60, self.screen_width, self.screen_height - 60)
        surface.set_clip(clip_rect)

        for cat_id, cat_data in by_category.items():
            achievements = cat_data["achievements"]
            if not achievements:
                continue

            # Category header
            cat_font = font_manager.get_font(13)
            cat_surf = cat_font.render(cat_data["name"], True, (150, 150, 180))
            surface.blit(cat_surf, (15, y))
            y += 20

            for ach_def in achievements:
                ach_id = ach_def["id"]
                is_unlocked = save_manager.is_achievement_unlocked(ach_id)

                if y + item_h < 60 or y > self.screen_height:
                    y += item_h + pad
                    continue

                # Background
                bg_color = (50, 60, 45) if is_unlocked else (40, 40, 55)
                draw_rounded_rect(surface, bg_color,
                                   (10, y, self.screen_width - 20, item_h), 6)

                # Icon
                sprite_renderer.draw_achievement_icon(surface, 18, y + 8, 35, is_unlocked)

                # Name
                name = get_text(ach_id)
                name_color = (255, 255, 255) if is_unlocked else (130, 130, 140)
                name_surf = name_font.render(name, True, name_color)
                surface.blit(name_surf, (60, y + 8))

                # Description
                desc = get_text(f"{ach_id}_desc")
                desc_color = (180, 180, 180) if is_unlocked else (100, 100, 110)
                desc_surf = desc_font.render(desc, True, desc_color)
                surface.blit(desc_surf, (60, y + 30))

                # Status
                if is_unlocked:
                    check_surf = name_font.render("✓", True, (100, 255, 100))
                    surface.blit(check_surf, (self.screen_width - 35, y + 15))

                y += item_h + pad

            y += 10  # Gap between categories

        self.ach_max_scroll = max(0, y + int(self.ach_scroll) - self.screen_height + 20)

        surface.set_clip(None)

    def handle_achievements(self, event):
        """Handle achievements screen. Returns 'back' or None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(10, 10, 80, 35).collidepoint(event.pos):
                return "back"
        if event.type == pygame.MOUSEWHEEL:
            self.ach_scroll -= event.y * 25
            self.ach_scroll = max(0, min(self.ach_scroll, self.ach_max_scroll))
        return None

    # ==================================================
    # STATISTICS SCREEN
    # ==================================================

    def draw_statistics(self, surface):
        """Draw statistics screen."""
        surface.fill((30, 30, 50))

        title = get_text("stats_title")
        title_font = font_manager.get_font(24)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, 15))

        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(10, 10, 80, 35)
        draw_button(surface, get_text("menu_back"), font_manager.get_font(14),
                     (10, 10, 80, 35), (80, 80, 100),
                     hover=back_rect.collidepoint(mx, my))

        stats = save_manager.statistics
        y = 60 - int(self.stats_scroll)
        row_h = 30
        label_font = font_manager.get_font(14)
        value_font = font_manager.get_font(14)

        clip_rect = pygame.Rect(0, 55, self.screen_width, self.screen_height - 55)
        surface.set_clip(clip_rect)

        stat_rows = [
            (get_text("stats_total_jumps"), str(stats.get("total_jumps", 0))),
            (get_text("stats_total_games"), str(stats.get("total_games", 0))),
            (get_text("stats_total_kills"), str(stats.get("total_kills", 0))),
            (get_text("stats_total_coins"), str(stats.get("total_coins_collected", 0))),
            (get_text("stats_coins_spent"), str(stats.get("total_coins_spent", 0))),
            (get_text("stats_platforms"), str(stats.get("total_platforms_landed", 0))),
            (get_text("stats_breakable"), str(stats.get("total_breakable_broken", 0))),
            (get_text("stats_playtime"),
             format_time(stats.get("total_playtime_seconds", 0))),
            (get_text("stats_best_combo"), str(stats.get("highest_combo", 0))),
            (get_text("stats_max_height"), str(stats.get("max_height_reached", 0))),
            (get_text("stats_deaths"), str(stats.get("deaths", 0))),
            (get_text("stats_boosters_used"), str(stats.get("boosters_used", 0))),
            (f"{get_text('hud_high_score')}", str(save_manager.high_score)),
        ]

        for label, value in stat_rows:
            if y + row_h >= 55 and y < self.screen_height:
                # Alternating row bg
                idx = stat_rows.index((label, value))
                bg_color = (45, 45, 65) if idx % 2 == 0 else (40, 40, 58)
                pygame.draw.rect(surface, bg_color,
                                  (10, y, self.screen_width - 20, row_h),
                                  border_radius=4)

                label_surf = label_font.render(label, True, (180, 180, 200))
                surface.blit(label_surf, (20, y + 5))

                value_surf = value_font.render(value, True, (150, 220, 255))
                surface.blit(value_surf,
                              (self.screen_width - 30 - value_surf.get_width(), y + 5))

            y += row_h + 2

        surface.set_clip(None)

    def handle_statistics(self, event):
        """Handle statistics screen. Returns 'back' or None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(10, 10, 80, 35).collidepoint(event.pos):
                return "back"
        if event.type == pygame.MOUSEWHEEL:
            self.stats_scroll -= event.y * 20
            self.stats_scroll = max(0, self.stats_scroll)
        return None

    # ==================================================
    # STORY MODE SELECT
    # ==================================================

    def draw_story_select(self, surface):
        """Draw story level selection screen."""
        surface.fill((30, 30, 50))

        title = get_text("story_title")
        title_font = font_manager.get_font(24)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, 15))

        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(10, 10, 80, 35)
        draw_button(surface, get_text("menu_back"), font_manager.get_font(14),
                     (10, 10, 80, 35), (80, 80, 100),
                     hover=back_rect.collidepoint(mx, my))

        progress = save_manager.story_progress
        unlocked_level = progress.get("unlocked_level", 1)
        stars = progress.get("stars", {})

        self._story_buttons = []

        for i in range(1, 6):
            y = 70 + (i - 1) * 85
            is_unlocked = i <= unlocked_level
            level_stars = stars.get(str(i), 0)

            rect = pygame.Rect(20, y, self.screen_width - 40, 75)

            if is_unlocked:
                bg_color = (50, 60, 80) if rect.collidepoint(mx, my) else (40, 50, 70)
            else:
                bg_color = (35, 35, 45)

            draw_rounded_rect(surface, bg_color, rect, 10)
            border_color = (100, 120, 180) if is_unlocked else (60, 60, 70)
            pygame.draw.rect(surface, border_color, rect, width=1, border_radius=10)

            # Level number
            num_font = font_manager.get_font(28)
            num_color = (255, 255, 255) if is_unlocked else (80, 80, 80)
            num_surf = num_font.render(str(i), True, num_color)
            surface.blit(num_surf, (35, y + 20))

            # Level name
            name_font = font_manager.get_font(16)
            name = f"{get_text('story_level')} {i}"
            name_color = (200, 200, 220) if is_unlocked else (80, 80, 90)
            name_surf = name_font.render(name, True, name_color)
            surface.blit(name_surf, (70, y + 15))

            # Stars
            if is_unlocked:
                for s in range(3):
                    star_x = 70 + s * 25
                    star_y = y + 40
                    filled = s < level_stars
                    sprite_renderer.draw_star_rating(surface, star_x, star_y, 20, filled)

            # Lock icon
            if not is_unlocked:
                lock_font = font_manager.get_font(14)
                lock_surf = lock_font.render(get_text("story_locked"), True, (80, 80, 90))
                surface.blit(lock_surf, (70, y + 40))

            if is_unlocked:
                self._story_buttons.append((rect, i))
            else:
                self._story_buttons.append((rect, None))

    def handle_story_select(self, event):
        """Handle story level selection. Returns level number or 'back' or None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if pygame.Rect(10, 10, 80, 35).collidepoint(mx, my):
                return "back"
            for rect, level_num in getattr(self, '_story_buttons', []):
                if level_num and rect.collidepoint(mx, my):
                    return level_num
        return None

    # ==================================================
    # CUSTOM LEVELS
    # ==================================================

    def refresh_custom_levels(self):
        """Scan custom levels directory."""
        self.custom_level_files = []
        if os.path.exists(CUSTOM_LEVELS_DIR):
            for fname in sorted(os.listdir(CUSTOM_LEVELS_DIR)):
                if fname.endswith(".json"):
                    filepath = os.path.join(CUSTOM_LEVELS_DIR, fname)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        name = data.get("name", fname.replace(".json", ""))
                        self.custom_level_files.append({
                            "filename": fname,
                            "filepath": filepath,
                            "name": name,
                            "author": data.get("author", "Unknown"),
                        })
                    except Exception:
                        self.custom_level_files.append({
                            "filename": fname,
                            "filepath": filepath,
                            "name": fname,
                            "author": "?",
                        })

    def draw_custom_levels(self, surface):
        """Draw custom levels browser."""
        surface.fill((30, 30, 50))

        title = get_text("custom_title")
        title_font = font_manager.get_font(24)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf,
                     (self.screen_width // 2 - title_surf.get_width() // 2, 15))

        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(10, 10, 80, 35)
        draw_button(surface, get_text("menu_back"), font_manager.get_font(14),
                     (10, 10, 80, 35), (80, 80, 100),
                     hover=back_rect.collidepoint(mx, my))

        # Open folder button
        folder_rect = pygame.Rect(self.screen_width - 140, 10, 130, 35)
        draw_button(surface, get_text("custom_open_folder"), font_manager.get_font(12),
                     (folder_rect.x, folder_rect.y, folder_rect.w, folder_rect.h),
                     (80, 100, 80), hover=folder_rect.collidepoint(mx, my))

        self._custom_buttons = []
        self._custom_folder_btn = folder_rect

        if not self.custom_level_files:
            no_levels = get_text("custom_no_levels")
            nl_font = font_manager.get_font(16)
            nl_surf = nl_font.render(no_levels, True, (120, 120, 140))
            surface.blit(nl_surf,
                         (self.screen_width // 2 - nl_surf.get_width() // 2, 200))
            return

        y = 60
        for i, level_info in enumerate(self.custom_level_files):
            row_h = 60
            rect = pygame.Rect(10, y, self.screen_width - 20, row_h)
            hover = rect.collidepoint(mx, my)
            bg_color = (55, 55, 75) if hover else (45, 45, 65)
            draw_rounded_rect(surface, bg_color, rect, 8)

            # Name
            name_font = font_manager.get_font(16)
            name_surf = name_font.render(level_info["name"], True, (255, 255, 255))
            surface.blit(name_surf, (20, y + 8))

            # Author
            author_font = font_manager.get_font(12)
            author_surf = author_font.render(f"by {level_info['author']}", True, (150, 150, 170))
            surface.blit(author_surf, (20, y + 32))

            # Play button
            play_btn = pygame.Rect(self.screen_width - 90, y + 12, 70, 36)
            draw_button(surface, get_text("custom_play"), font_manager.get_font(13),
                         (play_btn.x, play_btn.y, play_btn.w, play_btn.h),
                         (60, 120, 60), hover=play_btn.collidepoint(mx, my),
                         border_radius=6)

            self._custom_buttons.append((play_btn, level_info))

            y += row_h + 5

    def handle_custom_levels(self, event):
        """Handle custom levels screen. Returns level_info dict, 'back', or None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if pygame.Rect(10, 10, 80, 35).collidepoint(mx, my):
                return "back"
            if hasattr(self, '_custom_folder_btn') and self._custom_folder_btn.collidepoint(mx, my):
                open_folder(CUSTOM_LEVELS_DIR)
                return None
            for play_btn, level_info in getattr(self, '_custom_buttons', []):
                if play_btn.collidepoint(mx, my):
                    return level_info
        return None
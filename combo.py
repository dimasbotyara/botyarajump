"""
botyarajump - Combo System
Tracks kill combos and score multipliers.
"""

import pygame
import math

from settings import save_manager
from utils import clamp, create_surface_with_alpha


class ComboSystem:
    """Tracks consecutive kills for combo multiplier."""

    def __init__(self):
        self.current_combo = 0
        self.combo_timer = 0
        self.combo_timeout = 3.0  # Seconds before combo resets
        self.max_combo_this_game = 0

        # Score multiplier
        self.base_multiplier = 1.0

        # Visual feedback
        self.display_combo = 0  # For display (stays a bit after reset)
        self.display_timer = 0
        self.display_duration = 1.5

        # Popup text
        self.popup_texts = []  # List of (text, x, y, timer, color)

        # Combo thresholds for achievements
        self.thresholds_hit = set()

    def reset(self):
        """Reset for new game."""
        self.current_combo = 0
        self.combo_timer = 0
        self.max_combo_this_game = 0
        self.display_combo = 0
        self.display_timer = 0
        self.popup_texts.clear()
        self.thresholds_hit.clear()

    def add_kill(self, enemy_x=0, enemy_y=0, score_value=100):
        """Register a kill. Returns the actual score earned (with multiplier)."""
        self.current_combo += 1
        self.combo_timer = self.combo_timeout

        # Track max combo
        if self.current_combo > self.max_combo_this_game:
            self.max_combo_this_game = self.current_combo

        # Update display
        self.display_combo = self.current_combo
        self.display_timer = self.display_duration

        # Calculate multiplied score
        multiplier = self.get_multiplier()
        actual_score = int(score_value * multiplier)

        # Create popup text
        if self.current_combo >= 2:
            color = self._get_combo_color()
            text = f"x{self.current_combo}! +{actual_score}"
            self.popup_texts.append({
                "text": text,
                "x": enemy_x,
                "y": enemy_y,
                "timer": 0,
                "duration": 1.2,
                "color": color
            })

        # Check achievement thresholds
        self._check_thresholds()

        return actual_score

    def get_multiplier(self):
        """Get current score multiplier based on combo."""
        if self.current_combo <= 1:
            return self.base_multiplier

        # Multiplier increases: x1, x1.5, x2, x2.5, x3, etc.
        return self.base_multiplier + (self.current_combo - 1) * 0.5

    def update(self, dt):
        """Update combo timer and popups."""
        # Combo timeout
        if self.current_combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self._end_combo()

        # Display timer
        if self.display_timer > 0:
            self.display_timer -= dt

        # Update popup texts
        for popup in self.popup_texts:
            popup["timer"] += dt

        # Remove expired popups
        self.popup_texts = [
            p for p in self.popup_texts
            if p["timer"] < p["duration"]
        ]

    def _end_combo(self):
        """End current combo."""
        if self.current_combo > 0:
            # Save max combo
            save_manager.set_stat_max("highest_combo", self.max_combo_this_game)

        self.current_combo = 0
        self.combo_timer = 0

    def _check_thresholds(self):
        """Check combo thresholds for achievements."""
        thresholds = {3: "ach_combo_3", 5: "ach_combo_5", 10: "ach_combo_10"}
        for threshold, ach_id in thresholds.items():
            if self.current_combo >= threshold and threshold not in self.thresholds_hit:
                self.thresholds_hit.add(threshold)
                save_manager.unlock_achievement(ach_id)

    def _get_combo_color(self):
        """Get color based on combo level."""
        if self.current_combo >= 10:
            return (255, 50, 255)   # Purple
        elif self.current_combo >= 7:
            return (255, 50, 50)    # Red
        elif self.current_combo >= 5:
            return (255, 150, 0)    # Orange
        elif self.current_combo >= 3:
            return (255, 255, 0)    # Yellow
        else:
            return (255, 255, 255)  # White

    def draw_popups(self, surface, camera, renderer):
        """Draw combo popup texts."""
        from renderer import font_manager

        for popup in self.popup_texts:
            progress = popup["timer"] / popup["duration"]
            alpha = int(255 * (1 - progress))

            sx, sy = camera.world_to_screen(popup["x"], popup["y"])

            # Float upward
            sy -= progress * 40

            # Scale effect
            if progress < 0.2:
                scale = 0.5 + progress * 2.5  # Grow in
            else:
                scale = 1.0

            font_size = max(8, int(20 * scale))
            font = font_manager.get_font(font_size)

            text_surf = font.render(popup["text"], True, popup["color"])
            text_surf.set_alpha(alpha)

            text_rect = text_surf.get_rect(center=(int(sx), int(sy)))
            surface.blit(text_surf, text_rect)

    def draw_hud(self, surface, x, y, hud_opacity=255):
        """Draw combo counter in HUD."""
        if self.display_combo < 2 and self.display_timer <= 0:
            return

        from renderer import font_manager

        combo_value = self.display_combo if self.display_combo >= 2 else self.current_combo

        if combo_value < 2:
            return

        color = self._get_combo_color()

        # Pulsing effect
        pulse = 1.0
        if self.combo_timer > self.combo_timeout - 0.3:
            t = (self.combo_timeout - self.combo_timer) / 0.3
            pulse = 1.0 + 0.3 * (1 - t)

        # Fading when timer is running out
        fade_alpha = hud_opacity
        if self.display_timer <= 0.5 and self.display_timer > 0:
            fade_alpha = int(hud_opacity * (self.display_timer / 0.5))
        elif self.current_combo < 2:
            fade_alpha = int(hud_opacity * max(0, self.display_timer / self.display_duration))

        if fade_alpha <= 0:
            return

        font_size = max(16, int(28 * pulse))
        font = font_manager.get_font(font_size)

        multiplier = self.get_multiplier()
        combo_text = f"COMBO x{combo_value}"
        mult_text = f"Score x{multiplier:.1f}"

        combo_surf = font.render(combo_text, True, color)
        combo_surf.set_alpha(fade_alpha)

        mult_font = font_manager.get_font(max(12, font_size - 6))
        mult_surf = mult_font.render(mult_text, True, color)
        mult_surf.set_alpha(fade_alpha)

        combo_rect = combo_surf.get_rect(center=(x, y))
        mult_rect = mult_surf.get_rect(center=(x, y + font_size + 2))

        surface.blit(combo_surf, combo_rect)
        surface.blit(mult_surf, mult_rect)

        # Timer bar
        if self.current_combo >= 2:
            bar_width = 80
            bar_height = 4
            bar_x = x - bar_width // 2
            bar_y = y + font_size + 22

            remaining = clamp(self.combo_timer / self.combo_timeout, 0, 1)

            # Background bar
            bar_bg = create_surface_with_alpha(bar_width, bar_height)
            pygame.draw.rect(bar_bg, (50, 50, 50, fade_alpha),
                             (0, 0, bar_width, bar_height), border_radius=2)
            surface.blit(bar_bg, (bar_x, bar_y))

            # Fill bar
            fill_width = int(bar_width * remaining)
            if fill_width > 0:
                bar_fill = create_surface_with_alpha(fill_width, bar_height)
                pygame.draw.rect(bar_fill, (*color, fade_alpha),
                                 (0, 0, fill_width, bar_height), border_radius=2)
                surface.blit(bar_fill, (bar_x, bar_y))
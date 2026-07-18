"""
botyarajump - Renderer
Draws all game sprites programmatically (no external assets needed).
Handles fonts with emoji support and Cyrillic support.
"""

import pygame
import math
import random
import os
import platform as platform_module

from utils import (
    create_surface_with_alpha, darken_color, lighten_color,
    get_system_font_path, get_emoji_font_path, SKIN_COLORS, THEME_COLORS,
    clamp
)


class FontManager:
    """Manages fonts with Cyrillic and emoji support."""

    def __init__(self):
        self.fonts = {}
        self.emoji_fonts = {}
        self._init_font_paths()

    def _init_font_paths(self):
        """Find available font paths."""
        self.main_font_path = get_system_font_path()
        self.emoji_font_path = get_emoji_font_path()

        if self.main_font_path is None:
            print("Warning: No system font found, using pygame default")

    def get_font(self, size):
        """Get a font that supports Cyrillic."""
        if size not in self.fonts:
            try:
                if self.main_font_path:
                    self.fonts[size] = pygame.font.Font(self.main_font_path, size)
                else:
                    # Fallback to pygame default
                    self.fonts[size] = pygame.font.Font(None, size)
            except Exception:
                self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size]

    def get_emoji_font(self, size):
        """Get a font that supports emoji."""
        if size not in self.emoji_fonts:
            try:
                if self.emoji_font_path:
                    self.emoji_fonts[size] = pygame.font.Font(self.emoji_font_path, size)
                else:
                    self.emoji_fonts[size] = self.get_font(size)
            except Exception:
                self.emoji_fonts[size] = self.get_font(size)
        return self.emoji_fonts[size]

    def render_text(self, text, size, color, alpha=255):
        """Render text with proper font, returns surface."""
        font = self.get_font(size)
        surf = font.render(text, True, color)
        if alpha < 255:
            surf.set_alpha(alpha)
        return surf

    def render_text_with_emoji(self, text, size, color, alpha=255):
        """Render text that might contain emoji."""
        # Check if text contains emoji-range characters
        has_emoji = any(ord(c) > 0x2600 for c in text)

        if has_emoji and self.emoji_font_path:
            font = self.get_emoji_font(size)
        else:
            font = self.get_font(size)

        try:
            surf = font.render(text, True, color)
        except Exception:
            # Fallback: strip emoji and render with main font
            clean_text = ''.join(c for c in text if ord(c) < 0x2600)
            font = self.get_font(size)
            surf = font.render(clean_text, True, color)

        if alpha < 255:
            surf.set_alpha(alpha)
        return surf


# Global font manager
font_manager = FontManager()


class SpriteRenderer:
    """Renders all game sprites programmatically."""

    def __init__(self):
        self._cache = {}
        self._animation_time = 0

    def update(self, dt):
        """Update animation time."""
        self._animation_time += dt

    def clear_cache(self):
        """Clear sprite cache."""
        self._cache = {}

    # ==========================================
    # PLAYER SPRITE
    # ==========================================

    def draw_player(self, surface, x, y, width, height, skin_id="default",
                    facing_right=True, velocity_y=0, is_shooting=False,
                    has_shield=False, has_jetpack=False, has_blaster=False):
        """Draw the player character (doodler)."""
        colors = SKIN_COLORS.get(skin_id, SKIN_COLORS["default"])

        # Rainbow skin: cycle colors
        if skin_id == "rainbow":
            hue = (self._animation_time * 100) % 360
            colors = self._rainbow_colors(hue)

        body_color = colors["body"]
        eye_color = colors["eyes"]
        nose_color = colors["nose"]
        feet_color = colors["feet"]
        outline_color = colors["outline"]

        # Ghost skin: semi-transparent
        alpha = 160 if skin_id == "ghost" else 255

        # Create surface
        sprite_w = width + 10
        sprite_h = height + 10
        sprite = create_surface_with_alpha(sprite_w, sprite_h)

        cx = sprite_w // 2
        cy = sprite_h // 2

        # Squash and stretch based on velocity
        stretch_y = 1.0
        stretch_x = 1.0
        if velocity_y < -5:
            stretch_y = 1.15
            stretch_x = 0.85
        elif velocity_y > 5:
            stretch_y = 0.85
            stretch_x = 1.15

        body_w = int(width * 0.7 * stretch_x)
        body_h = int(height * 0.7 * stretch_y)

        # Body (ellipse)
        body_rect = pygame.Rect(cx - body_w // 2, cy - body_h // 2, body_w, body_h)

        if skin_id == "pixel":
            # Pixel skin: draw as blocks
            block_size = 4
            for bx in range(body_rect.left, body_rect.right, block_size):
                for by in range(body_rect.top, body_rect.bottom, block_size):
                    rel_x = (bx - body_rect.left) / body_w - 0.5
                    rel_y = (by - body_rect.top) / body_h - 0.5
                    if rel_x * rel_x + rel_y * rel_y < 0.25:
                        shade = random.randint(-20, 20)
                        c = tuple(clamp(body_color[i] + shade, 0, 255) for i in range(3))
                        pygame.draw.rect(sprite, (*c, alpha), (bx, by, block_size, block_size))
        elif skin_id == "robot":
            # Robot: rectangular body
            pygame.draw.rect(sprite, (*body_color, alpha), body_rect, border_radius=4)
            pygame.draw.rect(sprite, (*outline_color, alpha), body_rect, width=2, border_radius=4)
            # Antenna
            ant_x = cx
            ant_y = body_rect.top - 8
            pygame.draw.line(sprite, (*outline_color, alpha), (ant_x, body_rect.top), (ant_x, ant_y), 2)
            pygame.draw.circle(sprite, (255, 50, 50, alpha), (ant_x, ant_y), 3)
            # Panel lines
            pygame.draw.line(sprite, (*outline_color, alpha),
                             (body_rect.left + 4, cy), (body_rect.right - 4, cy), 1)
        else:
            # Normal: ellipse body
            pygame.draw.ellipse(sprite, (*body_color, alpha), body_rect)
            pygame.draw.ellipse(sprite, (*outline_color, alpha), body_rect, 2)

        # Eyes
        eye_offset_x = int(body_w * 0.2)
        eye_y = cy - int(body_h * 0.15)
        eye_size = max(3, int(width * 0.08))
        pupil_size = max(2, eye_size - 2)

        if facing_right:
            eye1_x = cx + eye_offset_x - eye_size
            eye2_x = cx + eye_offset_x + eye_size + 2
        else:
            eye1_x = cx - eye_offset_x - eye_size - 2
            eye2_x = cx - eye_offset_x + eye_size

        # Eye whites
        pygame.draw.circle(sprite, (255, 255, 255, alpha), (eye1_x, eye_y), eye_size)
        pygame.draw.circle(sprite, (255, 255, 255, alpha), (eye2_x, eye_y), eye_size)

        # Pupils - look in movement direction
        pupil_offset = 1 if facing_right else -1
        pygame.draw.circle(sprite, (*eye_color, alpha),
                           (eye1_x + pupil_offset, eye_y), pupil_size)
        pygame.draw.circle(sprite, (*eye_color, alpha),
                           (eye2_x + pupil_offset, eye_y), pupil_size)

        # Ninja skin: headband
        if skin_id == "ninja":
            band_y = eye_y - eye_size - 2
            pygame.draw.rect(sprite, (200, 30, 30, alpha),
                             (body_rect.left - 3, band_y, body_w + 6, 4))
            # Trailing band
            tail_x = body_rect.left - 3 if facing_right else body_rect.right + 3
            tail_dir = -1 if facing_right else 1
            for i in range(3):
                tx = tail_x + tail_dir * (i * 3 + 3)
                ty = band_y - i + int(math.sin(self._animation_time * 5 + i) * 2)
                pygame.draw.rect(sprite, (200, 30, 30, alpha), (tx, ty, 3, 3))

        # Nose/mouth
        if skin_id != "ninja":
            nose_x = cx + (int(body_w * 0.3) if facing_right else -int(body_w * 0.3))
            nose_y = cy + int(body_h * 0.05)
            nose_size = max(2, int(width * 0.06))
            pygame.draw.circle(sprite, (*nose_color, alpha), (nose_x, nose_y), nose_size)

        # Feet
        feet_y = cy + body_h // 2 - 2
        foot_w = max(6, int(width * 0.2))
        foot_h = max(4, int(height * 0.08))
        foot_offset = int(body_w * 0.25)

        left_foot = pygame.Rect(cx - foot_offset - foot_w // 2, feet_y, foot_w, foot_h)
        right_foot = pygame.Rect(cx + foot_offset - foot_w // 2, feet_y, foot_w, foot_h)

        # Animate feet
        if velocity_y < 0:
            left_foot.y -= 2
            right_foot.y -= 2
        elif velocity_y > 0:
            left_foot.y += 1
            right_foot.y += 1

        pygame.draw.ellipse(sprite, (*feet_color, alpha), left_foot)
        pygame.draw.ellipse(sprite, (*feet_color, alpha), right_foot)
        pygame.draw.ellipse(sprite, (*outline_color, alpha), left_foot, 1)
        pygame.draw.ellipse(sprite, (*outline_color, alpha), right_foot, 1)

        # Shooting animation
        if is_shooting:
            if facing_right:
                gun_x = cx + body_w // 2
            else:
                gun_x = cx - body_w // 2 - 10
            gun_y = cy - 2
            pygame.draw.rect(sprite, (100, 100, 100, alpha), (gun_x, gun_y, 10, 5))
            pygame.draw.circle(sprite, (255, 200, 50, alpha), (gun_x + (10 if facing_right else 0), gun_y + 2), 3)

        # Blaster powerup
        if has_blaster:
            if facing_right:
                bx = cx + body_w // 2 + 2
            else:
                bx = cx - body_w // 2 - 14
            by = cy - 4
            pygame.draw.rect(sprite, (80, 80, 120, alpha), (bx, by, 12, 8), border_radius=2)
            pygame.draw.rect(sprite, (150, 50, 50, alpha), (bx + (10 if facing_right else 0), by + 1, 4, 6))

        # Jetpack
        if has_jetpack:
            jp_x = cx - body_w // 2 - 6 if facing_right else cx + body_w // 2 + 2
            jp_y = cy - body_h // 4
            pygame.draw.rect(sprite, (80, 80, 80, alpha), (jp_x, jp_y, 8, int(body_h * 0.6)),
                             border_radius=2)
            # Flame
            flame_y = jp_y + int(body_h * 0.6)
            flame_colors = [
                (255, 200, 50, alpha),
                (255, 130, 30, alpha),
                (255, 60, 20, alpha)
            ]
            for i, fc in enumerate(flame_colors):
                fh = int(8 + math.sin(self._animation_time * 15 + i) * 4)
                fw = max(2, 6 - i * 2)
                pygame.draw.ellipse(sprite, fc,
                                    (jp_x + 4 - fw // 2, flame_y + i * 3, fw, fh))

        # Shield
        if has_shield:
            shield_radius = max(body_w, body_h) // 2 + 8
            shield_alpha = int(80 + 40 * math.sin(self._animation_time * 3))
            shield_surf = create_surface_with_alpha(shield_radius * 2 + 4, shield_radius * 2 + 4)
            pygame.draw.circle(shield_surf, (100, 180, 255, shield_alpha),
                               (shield_radius + 2, shield_radius + 2), shield_radius, 3)
            sprite.blit(shield_surf, (cx - shield_radius - 2, cy - shield_radius - 2))

        # Neon skin: glow effect
        if skin_id == "neon":
            glow_alpha = int(30 + 20 * math.sin(self._animation_time * 4))
            glow_surf = create_surface_with_alpha(sprite_w, sprite_h)
            glow_rect = body_rect.inflate(10, 10)
            pygame.draw.ellipse(glow_surf, (0, 255, 150, glow_alpha), glow_rect)
            sprite.blit(glow_surf, (0, 0))

        # Draw to main surface
        surface.blit(sprite, (x - 5, y - 5))

    def _rainbow_colors(self, hue):
        """Generate rainbow skin colors from hue."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.8, 0.9)
        body = (int(r * 255), int(g * 255), int(b * 255))
        r2, g2, b2 = colorsys.hsv_to_rgb(((hue + 30) % 360) / 360, 0.7, 0.7)
        accent = (int(r2 * 255), int(g2 * 255), int(b2 * 255))
        r3, g3, b3 = colorsys.hsv_to_rgb(((hue + 60) % 360) / 360, 0.6, 0.6)
        outline = (int(r3 * 255), int(g3 * 255), int(b3 * 255))
        return {
            "body": body,
            "eyes": (40, 40, 40),
            "nose": accent,
            "feet": accent,
            "outline": outline
        }

    # ==========================================
    # PLATFORM SPRITES
    # ==========================================

    def draw_platform_normal(self, surface, x, y, width, height, theme="day"):
        """Draw normal (green) platform."""
        colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        color = colors["platform_normal"]
        dark = darken_color(color, 0.7)
        light = lighten_color(color, 1.3)

        # Main body
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color, rect, border_radius=4)

        # Top highlight
        highlight = pygame.Rect(x + 2, y + 1, width - 4, height // 3)
        pygame.draw.rect(surface, light, highlight, border_radius=2)

        # Bottom shadow
        shadow = pygame.Rect(x + 1, y + height - 3, width - 2, 3)
        pygame.draw.rect(surface, dark, shadow, border_radius=2)

        # Grass tufts on top
        for i in range(0, width - 4, 8):
            grass_x = x + i + 2
            grass_h = random.Random(int(x + i)).randint(2, 5)
            pygame.draw.line(surface, lighten_color(color, 1.4),
                             (grass_x, y), (grass_x - 1, y - grass_h), 1)
            pygame.draw.line(surface, lighten_color(color, 1.2),
                             (grass_x + 2, y), (grass_x + 3, y - grass_h + 1), 1)

    def draw_platform_moving(self, surface, x, y, width, height, theme="day"):
        """Draw moving (blue) platform."""
        colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        color = colors["platform_moving"]
        dark = darken_color(color, 0.7)
        light = lighten_color(color, 1.3)

        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color, rect, border_radius=4)

        # Top highlight
        highlight = pygame.Rect(x + 2, y + 1, width - 4, height // 3)
        pygame.draw.rect(surface, light, highlight, border_radius=2)

        # Arrow indicators on sides
        arrow_y = y + height // 2
        arrow_size = 4
        # Left arrow
        pygame.draw.polygon(surface, (255, 255, 255),
                            [(x + 4, arrow_y),
                             (x + 4 + arrow_size, arrow_y - arrow_size),
                             (x + 4 + arrow_size, arrow_y + arrow_size)])
        # Right arrow
        pygame.draw.polygon(surface, (255, 255, 255),
                            [(x + width - 4, arrow_y),
                             (x + width - 4 - arrow_size, arrow_y - arrow_size),
                             (x + width - 4 - arrow_size, arrow_y + arrow_size)])

        # Bottom shadow
        pygame.draw.rect(surface, dark,
                         (x + 1, y + height - 3, width - 2, 3), border_radius=2)

    def draw_platform_breakable(self, surface, x, y, width, height, theme="day",
                                crack_level=0):
        """Draw breakable (brown) platform. crack_level 0-2."""
        colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        color = colors["platform_breakable"]
        dark = darken_color(color, 0.6)
        light = lighten_color(color, 1.2)

        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color, rect, border_radius=3)

        # Top highlight
        pygame.draw.rect(surface, light,
                         (x + 2, y + 1, width - 4, height // 3), border_radius=2)

        # Cracks based on damage level
        if crack_level >= 1:
            # Small cracks
            cx = x + width // 3
            cy = y + height // 2
            pygame.draw.line(surface, dark, (cx, y + 2), (cx + 5, cy), 2)
            pygame.draw.line(surface, dark, (cx + 5, cy), (cx + 2, y + height - 2), 2)

        if crack_level >= 2:
            # More cracks
            cx2 = x + width * 2 // 3
            pygame.draw.line(surface, dark, (cx2, y + 1), (cx2 - 3, y + height - 1), 2)
            pygame.draw.line(surface, dark, (x + 5, cy), (x + width - 5, cy + 2), 1)

        # Bottom shadow
        pygame.draw.rect(surface, dark,
                         (x + 1, y + height - 2, width - 2, 2), border_radius=2)

    def draw_platform_disappearing(self, surface, x, y, width, height, theme="day",
                                   fade_progress=0.0):
        """Draw disappearing platform. fade_progress 0.0 (solid) to 1.0 (gone)."""
        colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        color = colors["platform_disappearing"]
        alpha = int(255 * (1.0 - fade_progress))

        if alpha <= 0:
            return

        temp = create_surface_with_alpha(width + 4, height + 4)

        body_color = (*color, alpha)
        dark_color = (*darken_color(color, 0.7), alpha)
        light_color = (*lighten_color(color, 1.2), alpha)

        pygame.draw.rect(temp, body_color, (2, 2, width, height), border_radius=4)
        pygame.draw.rect(temp, light_color, (4, 3, width - 4, height // 3), border_radius=2)

        # Dotted border
        dash_len = 4
        gap = 3
        for i in range(0, width, dash_len + gap):
            pygame.draw.line(temp, dark_color, (2 + i, 2), (2 + min(i + dash_len, width), 2), 1)
            pygame.draw.line(temp, dark_color,
                             (2 + i, 2 + height), (2 + min(i + dash_len, width), 2 + height), 1)

        surface.blit(temp, (x - 2, y - 2))

    def draw_platform_spring(self, surface, x, y, width, height, theme="day",
                             compressed=False):
        """Draw platform with spring on top."""
        colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        color = colors["platform_spring"]
        dark = darken_color(color, 0.7)

        # Draw base platform
        self.draw_platform_normal(surface, x, y, width, height, theme)

        # Draw spring
        spring_x = x + width // 2
        spring_w = 12
        spring_h = 10 if not compressed else 4

        # Spring coils
        coil_color = (200, 200, 200)
        coil_dark = (150, 150, 150)
        num_coils = 3
        coil_height = spring_h / num_coils

        for i in range(num_coils):
            cy = y - spring_h + i * coil_height
            cw = spring_w - i * 1
            pygame.draw.ellipse(surface, coil_color,
                                (spring_x - cw // 2, int(cy), cw, int(coil_height + 1)))
            pygame.draw.ellipse(surface, coil_dark,
                                (spring_x - cw // 2, int(cy), cw, int(coil_height + 1)), 1)

        # Top cap
        cap_w = spring_w + 4
        cap_h = 4
        cap_color = color
        pygame.draw.rect(surface, cap_color,
                         (spring_x - cap_w // 2, y - spring_h - cap_h, cap_w, cap_h),
                         border_radius=2)
        pygame.draw.rect(surface, dark,
                         (spring_x - cap_w // 2, y - spring_h - cap_h, cap_w, cap_h),
                         width=1, border_radius=2)

    def draw_platform_breaking_pieces(self, surface, x, y, width, height,
                                      progress, theme="day"):
        """Draw breaking platform pieces (animation)."""
        colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        color = colors["platform_breakable"]
        dark = darken_color(color, 0.7)

        num_pieces = 5
        piece_w = width // num_pieces

        for i in range(num_pieces):
            px = x + i * piece_w
            # Each piece falls and rotates
            seed = int(x * 100 + i * 37)
            rng = random.Random(seed)
            dx = rng.uniform(-2, 2) * progress * 10
            dy = progress * progress * 80 + rng.uniform(0, 20) * progress
            rot = progress * rng.uniform(-90, 90)
            alpha = int(255 * (1 - progress))

            if alpha <= 0:
                continue

            piece = create_surface_with_alpha(piece_w + 4, height + 4)
            pygame.draw.rect(piece, (*color, alpha), (2, 2, piece_w, height), border_radius=2)
            pygame.draw.rect(piece, (*dark, alpha), (2, 2, piece_w, height),
                             width=1, border_radius=2)

            # Rotate
            rotated = pygame.transform.rotate(piece, rot)
            new_rect = rotated.get_rect(center=(px + piece_w // 2 + dx,
                                                y + height // 2 + dy))
            surface.blit(rotated, new_rect.topleft)

    # ==========================================
    # ENEMY SPRITES
    # ==========================================

    def draw_enemy_slug(self, surface, x, y, width, height, facing_right=True):
        """Draw slug enemy."""
        body_color = (120, 180, 50)
        dark = darken_color(body_color, 0.7)
        eye_color = (255, 50, 50)

        # Body blob
        pygame.draw.ellipse(surface, body_color, (x, y + height // 3, width, height * 2 // 3))
        pygame.draw.ellipse(surface, dark, (x, y + height // 3, width, height * 2 // 3), 2)

        # Head bump
        head_x = x + width - width // 3 if facing_right else x
        pygame.draw.ellipse(surface, body_color,
                            (head_x, y, width // 3, height * 2 // 3))

        # Eyes (angry)
        eye_x = head_x + width // 6
        eye_y = y + height // 4
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, eye_y), 4)
        pygame.draw.circle(surface, eye_color, (eye_x, eye_y), 2)

        # Slime trail
        trail_y = y + height - 2
        for i in range(3):
            tx = x + (width - 15 if facing_right else 5) - i * 6 * (1 if facing_right else -1)
            alpha = 150 - i * 40
            slime_surf = create_surface_with_alpha(5, 3)
            pygame.draw.ellipse(slime_surf, (150, 220, 80, alpha), (0, 0, 5, 3))
            surface.blit(slime_surf, (tx, trail_y))

    def draw_enemy_bat(self, surface, x, y, width, height):
        """Draw bat enemy."""
        body_color = (80, 40, 100)
        wing_color = (100, 50, 130)
        eye_color = (255, 255, 0)

        # Wing animation
        wing_angle = math.sin(self._animation_time * 10) * 20

        # Body
        body_w = width // 3
        body_h = height // 2
        body_x = x + width // 2 - body_w // 2
        body_y = y + height // 2 - body_h // 2

        pygame.draw.ellipse(surface, body_color, (body_x, body_y, body_w, body_h))

        # Wings
        wing_w = width // 3
        wing_h = height // 2 + int(wing_angle)

        # Left wing
        left_points = [
            (body_x, body_y + body_h // 3),
            (x, y + max(0, int(height // 4 - wing_angle))),
            (x + wing_w // 2, body_y + body_h // 2),
        ]
        pygame.draw.polygon(surface, wing_color, left_points)

        # Right wing
        right_points = [
            (body_x + body_w, body_y + body_h // 3),
            (x + width, y + max(0, int(height // 4 - wing_angle))),
            (x + width - wing_w // 2, body_y + body_h // 2),
        ]
        pygame.draw.polygon(surface, wing_color, right_points)

        # Eyes
        eye_y_pos = body_y + body_h // 3
        pygame.draw.circle(surface, eye_color, (body_x + body_w // 3, eye_y_pos), 3)
        pygame.draw.circle(surface, eye_color, (body_x + body_w * 2 // 3, eye_y_pos), 3)
        pygame.draw.circle(surface, (0, 0, 0), (body_x + body_w // 3, eye_y_pos), 1)
        pygame.draw.circle(surface, (0, 0, 0), (body_x + body_w * 2 // 3, eye_y_pos), 1)

        # Ears
        pygame.draw.polygon(surface, body_color, [
            (body_x + 2, body_y),
            (body_x - 2, body_y - 6),
            (body_x + 6, body_y + 2)
        ])
        pygame.draw.polygon(surface, body_color, [
            (body_x + body_w - 2, body_y),
            (body_x + body_w + 2, body_y - 6),
            (body_x + body_w - 6, body_y + 2)
        ])

    def draw_enemy_black_hole(self, surface, x, y, size):
        """Draw black hole enemy."""
        cx = x + size // 2
        cy = y + size // 2

        # Accretion disk
        for i in range(5, 0, -1):
            radius = size // 2 + i * 4
            alpha = 30 + i * 15
            ring_surf = create_surface_with_alpha(radius * 2 + 4, radius * 2 + 4)
            angle_offset = self._animation_time * (1 + i * 0.5)
            ring_color = (
                int(100 + 30 * math.sin(angle_offset)),
                int(50 + 20 * math.sin(angle_offset + 2)),
                int(150 + 50 * math.sin(angle_offset + 4)),
                alpha
            )
            pygame.draw.circle(ring_surf, ring_color,
                               (radius + 2, radius + 2), radius, 2)
            surface.blit(ring_surf, (cx - radius - 2, cy - radius - 2))

        # Core
        pygame.draw.circle(surface, (10, 0, 20), (cx, cy), size // 2)
        pygame.draw.circle(surface, (30, 0, 50), (cx, cy), size // 2, 2)

        # Swirl particles
        for i in range(8):
            angle = self._animation_time * 3 + i * math.pi / 4
            dist = size // 2 + 3 + int(5 * math.sin(self._animation_time * 2 + i))
            px = cx + int(math.cos(angle) * dist)
            py = cy + int(math.sin(angle) * dist)
            pygame.draw.circle(surface, (180, 100, 255), (px, py), 2)

    def draw_enemy_ghost(self, surface, x, y, width, height):
        """Draw ghost enemy."""
        alpha = int(150 + 50 * math.sin(self._animation_time * 3))
        ghost_surf = create_surface_with_alpha(width + 4, height + 8)

        body_color = (200, 200, 230, alpha)
        eye_color = (20, 20, 60, alpha)

        # Body (rounded top, wavy bottom)
        # Top half circle
        pygame.draw.ellipse(ghost_surf, body_color, (2, 2, width, height))

        # Wavy bottom
        wave_points = [(2, 2 + height * 3 // 4)]
        num_waves = 4
        for i in range(num_waves + 1):
            wx = 2 + i * width // num_waves
            wy = 2 + height + int(math.sin(self._animation_time * 4 + i * 2) * 4) - 4
            wave_points.append((wx, wy))
        wave_points.append((2 + width, 2 + height * 3 // 4))
        pygame.draw.polygon(ghost_surf, body_color, wave_points)

        # Eyes
        eye_y_pos = 2 + height // 3
        pygame.draw.circle(ghost_surf, (255, 255, 255, alpha),
                           (2 + width // 3, eye_y_pos), 5)
        pygame.draw.circle(ghost_surf, (255, 255, 255, alpha),
                           (2 + width * 2 // 3, eye_y_pos), 5)
        pygame.draw.circle(ghost_surf, eye_color,
                           (2 + width // 3 + 1, eye_y_pos), 3)
        pygame.draw.circle(ghost_surf, eye_color,
                           (2 + width * 2 // 3 + 1, eye_y_pos), 3)

        # Mouth (spooky O)
        mouth_y = eye_y_pos + 10
        pygame.draw.ellipse(ghost_surf, eye_color,
                            (2 + width // 2 - 4, mouth_y, 8, 6))

        surface.blit(ghost_surf, (x - 2, y - 2))

    def draw_enemy_red_ball(self, surface, x, y, size):
        """Draw red ball enemy."""
        cx = x + size // 2
        cy = y + size // 2

        # Body
        pygame.draw.circle(surface, (220, 40, 40), (cx, cy), size // 2)
        pygame.draw.circle(surface, (180, 20, 20), (cx, cy), size // 2, 2)

        # Highlight
        pygame.draw.circle(surface, (255, 120, 120),
                           (cx - size // 6, cy - size // 6), size // 6)

        # Angry eyes
        eye_y_pos = cy - 2
        # Left eye
        pygame.draw.circle(surface, (255, 255, 255), (cx - 5, eye_y_pos), 4)
        pygame.draw.circle(surface, (0, 0, 0), (cx - 5, eye_y_pos), 2)
        # Right eye
        pygame.draw.circle(surface, (255, 255, 255), (cx + 5, eye_y_pos), 4)
        pygame.draw.circle(surface, (0, 0, 0), (cx + 5, eye_y_pos), 2)

        # Angry eyebrows
        pygame.draw.line(surface, (0, 0, 0),
                         (cx - 9, eye_y_pos - 5), (cx - 3, eye_y_pos - 3), 2)
        pygame.draw.line(surface, (0, 0, 0),
                         (cx + 9, eye_y_pos - 5), (cx + 3, eye_y_pos - 3), 2)

        # Mouth
        pygame.draw.arc(surface, (0, 0, 0),
                        (cx - 6, cy + 2, 12, 6), 3.14, 2 * 3.14, 2)

    def draw_enemy_snake(self, surface, x, y, width, height, facing_right=True):
        """Draw snake enemy."""
        body_color = (60, 140, 60)
        belly_color = (100, 200, 80)
        eye_color = (255, 200, 0)

        # Body segments
        num_segments = 6
        seg_w = width // num_segments

        for i in range(num_segments):
            sx = x + i * seg_w
            sy = y + int(math.sin(self._animation_time * 5 + i * 0.8) * 3)
            seg_color = body_color if i % 2 == 0 else lighten_color(body_color, 1.2)
            pygame.draw.ellipse(surface, seg_color, (sx, sy, seg_w + 2, height))

        # Head
        head_x = x + width - seg_w if facing_right else x
        head_y = y + int(math.sin(self._animation_time * 5 + 5) * 3)

        pygame.draw.ellipse(surface, body_color, (head_x, head_y - 2, seg_w + 4, height + 4))

        # Eyes
        eye_x = head_x + seg_w - 3 if facing_right else head_x + 3
        eye_y_pos = head_y + height // 3
        pygame.draw.circle(surface, eye_color, (eye_x, eye_y_pos), 3)
        pygame.draw.circle(surface, (0, 0, 0), (eye_x, eye_y_pos), 1)

        # Tongue
        tongue_x = head_x + seg_w + 2 if facing_right else head_x - 6
        tongue_y = head_y + height // 2
        tongue_dir = 1 if facing_right else -1
        flick = int(math.sin(self._animation_time * 12) * 2)
        pygame.draw.line(surface, (255, 50, 50),
                         (tongue_x, tongue_y),
                         (tongue_x + tongue_dir * 6, tongue_y + flick), 1)
        pygame.draw.line(surface, (255, 50, 50),
                         (tongue_x + tongue_dir * 6, tongue_y + flick),
                         (tongue_x + tongue_dir * 8, tongue_y + flick - 2), 1)
        pygame.draw.line(surface, (255, 50, 50),
                         (tongue_x + tongue_dir * 6, tongue_y + flick),
                         (tongue_x + tongue_dir * 8, tongue_y + flick + 2), 1)

    def draw_enemy_evil_cloud(self, surface, x, y, width, height):
        """Draw evil cloud enemy."""
        cloud_color = (80, 80, 100)
        dark_color = (50, 50, 70)

        # Cloud puffs
        puffs = [
            (x + width * 0.2, y + height * 0.4, width * 0.3, height * 0.5),
            (x + width * 0.5, y + height * 0.2, width * 0.35, height * 0.55),
            (x + width * 0.75, y + height * 0.35, width * 0.28, height * 0.45),
            (x + width * 0.35, y + height * 0.15, width * 0.32, height * 0.5),
        ]

        for px, py, pw, ph in puffs:
            pygame.draw.ellipse(surface, cloud_color, (int(px), int(py), int(pw), int(ph)))

        # Flat bottom
        pygame.draw.rect(surface, cloud_color,
                         (x + int(width * 0.1), y + int(height * 0.55),
                          int(width * 0.8), int(height * 0.15)))

        # Angry eyes
        eye_y_pos = y + int(height * 0.4)
        eye_x1 = x + int(width * 0.35)
        eye_x2 = x + int(width * 0.6)

        pygame.draw.circle(surface, (255, 255, 0), (eye_x1, eye_y_pos), 4)
        pygame.draw.circle(surface, (255, 255, 0), (eye_x2, eye_y_pos), 4)
        pygame.draw.circle(surface, (200, 50, 50), (eye_x1, eye_y_pos), 2)
        pygame.draw.circle(surface, (200, 50, 50), (eye_x2, eye_y_pos), 2)

        # Lightning underneath
        if int(self._animation_time * 4) % 3 == 0:
            bolt_x = x + int(width * 0.4 + math.sin(self._animation_time * 7) * width * 0.2)
            bolt_y = y + int(height * 0.7)
            self._draw_lightning(surface, bolt_x, bolt_y, 20)

    def draw_enemy_ufo(self, surface, x, y, width, height):
        """Draw UFO enemy."""
        body_color = (160, 170, 180)
        dome_color = (100, 200, 255)
        light_color = (255, 255, 100)

        # Hover bob
        bob = int(math.sin(self._animation_time * 3) * 3)
        y = y + bob

        # Body (ellipse)
        body_h = height // 3
        body_y = y + height // 2 - body_h // 2
        pygame.draw.ellipse(surface, body_color, (x, body_y, width, body_h))
        pygame.draw.ellipse(surface, darken_color(body_color, 0.7),
                            (x, body_y, width, body_h), 2)

        # Dome
        dome_w = width // 2
        dome_h = height // 2
        dome_x = x + width // 2 - dome_w // 2
        dome_y = body_y - dome_h + 4

        dome_surf = create_surface_with_alpha(dome_w + 4, dome_h + 4)
        pygame.draw.ellipse(dome_surf, (*dome_color, 150), (2, 2, dome_w, dome_h))
        pygame.draw.ellipse(dome_surf, (*lighten_color(dome_color, 1.3), 100),
                            (dome_w // 4, dome_h // 4, dome_w // 2, dome_h // 2))
        surface.blit(dome_surf, (dome_x - 2, dome_y - 2))

        # Lights around body
        num_lights = 5
        for i in range(num_lights):
            angle = self._animation_time * 3 + i * (2 * math.pi / num_lights)
            lx = int(x + width // 2 + math.cos(angle) * (width // 2 - 5))
            ly = int(body_y + body_h // 2 + math.sin(angle) * (body_h // 4))
            brightness = int(200 + 55 * math.sin(self._animation_time * 5 + i * 2))
            pygame.draw.circle(surface, (brightness, brightness, 100), (lx, ly), 3)

        # Beam (occasionally)
        if int(self._animation_time * 2) % 4 == 0:
            beam_surf = create_surface_with_alpha(width, height)
            beam_points = [
                (width // 2 - 8, body_h),
                (width // 2 + 8, body_h),
                (width // 2 + 20, height),
                (width // 2 - 20, height)
            ]
            pygame.draw.polygon(beam_surf, (255, 255, 100, 40), beam_points)
            surface.blit(beam_surf, (x, y))

    def _draw_lightning(self, surface, x, y, length):
        """Draw a small lightning bolt."""
        color = (255, 255, 100)
        bright = (255, 255, 200)

        points = [(x, y)]
        cx, cy = x, y
        segments = 4
        for i in range(segments):
            cx += random.randint(-4, 4)
            cy += length // segments
            points.append((cx, cy))

        if len(points) >= 2:
            pygame.draw.lines(surface, bright, False, points, 2)
            pygame.draw.lines(surface, color, False, points, 1)

    # ==========================================
    # POWERUP SPRITES
    # ==========================================

    def draw_powerup_spring(self, surface, x, y, width, height):
        """Draw spring powerup (just the spring, no platform)."""
        coil_color = (200, 200, 200)
        cap_color = (220, 200, 50)

        # Coils
        num_coils = 4
        coil_h = height / num_coils
        for i in range(num_coils):
            cy = y + i * coil_h
            cw = width - i * 1
            pygame.draw.ellipse(surface, coil_color,
                                (x + (width - cw) // 2, int(cy), cw, int(coil_h + 1)))
            pygame.draw.ellipse(surface, darken_color(coil_color, 0.7),
                                (x + (width - cw) // 2, int(cy), cw, int(coil_h + 1)), 1)

        # Cap
        pygame.draw.rect(surface, cap_color, (x - 2, y - 3, width + 4, 4), border_radius=2)

    def draw_powerup_jetpack(self, surface, x, y, width, height):
        """Draw jetpack powerup."""
        body_color = (100, 100, 120)
        rocket_color = (180, 60, 40)
        flame_color = (255, 180, 50)

        # Body
        pygame.draw.rect(surface, body_color, (x + 2, y, width - 4, height), border_radius=3)

        # Rockets
        rocket_w = width // 3
        pygame.draw.rect(surface, rocket_color,
                         (x, y + height // 3, rocket_w, height * 2 // 3), border_radius=2)
        pygame.draw.rect(surface, rocket_color,
                         (x + width - rocket_w, y + height // 3, rocket_w, height * 2 // 3),
                         border_radius=2)

        # Flames
        fh = int(5 + math.sin(self._animation_time * 12) * 3)
        pygame.draw.ellipse(surface, flame_color,
                            (x + 1, y + height, rocket_w - 2, fh))
        pygame.draw.ellipse(surface, flame_color,
                            (x + width - rocket_w + 1, y + height, rocket_w - 2, fh))

        # Straps
        pygame.draw.line(surface, (60, 60, 60),
                         (x + width // 2, y + 2), (x + width // 2, y + height - 2), 2)

    def draw_powerup_blaster(self, surface, x, y, width, height):
        """Draw blaster powerup."""
        body_color = (80, 80, 120)
        barrel_color = (150, 50, 50)
        highlight = (100, 100, 150)

        pygame.draw.rect(surface, body_color, (x, y + height // 3, width * 2 // 3, height // 2),
                         border_radius=2)
        pygame.draw.rect(surface, barrel_color,
                         (x + width * 2 // 3, y + height // 3 + 2, width // 3, height // 3))
        pygame.draw.rect(surface, highlight,
                         (x + 2, y + height // 3 + 2, width // 4, height // 6), border_radius=1)

        # Handle
        pygame.draw.rect(surface, darken_color(body_color, 0.7),
                         (x + width // 4, y + height // 3 + height // 2, width // 5, height // 4),
                         border_radius=2)

    def draw_powerup_shield(self, surface, x, y, size):
        """Draw shield powerup."""
        alpha = int(180 + 50 * math.sin(self._animation_time * 3))
        shield_surf = create_surface_with_alpha(size + 4, size + 4)

        # Shield shape
        pygame.draw.circle(shield_surf, (100, 180, 255, alpha),
                           (size // 2 + 2, size // 2 + 2), size // 2)
        pygame.draw.circle(shield_surf, (150, 210, 255, alpha),
                           (size // 2 + 2, size // 2 + 2), size // 2, 2)

        # Star in center
        star_x = size // 2 + 2
        star_y = size // 2 + 2
        star_size = size // 4
        self._draw_star(shield_surf, star_x, star_y, star_size, (255, 255, 255, alpha))

        surface.blit(shield_surf, (x - 2, y - 2))

    def draw_powerup_magnet(self, surface, x, y, width, height):
        """Draw magnet powerup."""
        # U-shape magnet
        body_color = (180, 40, 40)
        tip_color = (200, 200, 200)

        # U shape
        thickness = width // 3
        pygame.draw.rect(surface, body_color, (x, y, thickness, height))
        pygame.draw.rect(surface, body_color, (x + width - thickness, y, thickness, height))
        pygame.draw.rect(surface, body_color, (x, y, width, thickness))

        # Tips
        pygame.draw.rect(surface, tip_color,
                         (x, y + height - thickness, thickness, thickness))
        pygame.draw.rect(surface, tip_color,
                         (x + width - thickness, y + height - thickness, thickness, thickness))

        # Magnetic field lines
        for i in range(3):
            arc_size = width + i * 8
            arc_alpha = 120 - i * 30
            arc_surf = create_surface_with_alpha(arc_size + 4, height // 2 + 4)
            pygame.draw.arc(arc_surf, (100, 100, 255, arc_alpha),
                            (2, 2, arc_size, height // 2), 0, math.pi, 2)
            surface.blit(arc_surf, (x + width // 2 - arc_size // 2 - 2, y + height - 2))

    # ==========================================
    # COIN SPRITE
    # ==========================================

    def draw_coin(self, surface, x, y, size, theme="day"):
        """Draw a coin."""
        colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        color = colors["coin_color"]
        dark = darken_color(color, 0.7)
        light = lighten_color(color, 1.3)

        # Rotation effect
        squeeze = abs(math.sin(self._animation_time * 3))
        draw_w = max(2, int(size * squeeze))

        cx = x + size // 2
        cy = y + size // 2

        # Coin body
        pygame.draw.ellipse(surface, color,
                            (cx - draw_w // 2, cy - size // 2, draw_w, size))

        if draw_w > 4:
            # Inner circle
            inner_w = max(1, draw_w - 4)
            pygame.draw.ellipse(surface, dark,
                                (cx - inner_w // 2, cy - size // 2 + 2, inner_w, size - 4), 1)

            # Dollar/coin symbol
            if draw_w > 8:
                font = font_manager.get_font(size - 4)
                text_surf = font.render("$", True, dark)
                text_rect = text_surf.get_rect(center=(cx, cy))
                # Scale text to match coin squeeze
                if squeeze < 0.9:
                    text_surf = pygame.transform.scale(text_surf,
                                                       (max(1, int(text_surf.get_width() * squeeze)),
                                                        text_surf.get_height()))
                    text_rect = text_surf.get_rect(center=(cx, cy))
                surface.blit(text_surf, text_rect)

        # Sparkle
        sparkle_time = (self._animation_time * 2 + x * 0.1) % 2
        if sparkle_time < 0.3:
            sp_x = cx + int(size * 0.3)
            sp_y = cy - int(size * 0.3)
            sp_size = int(3 * (1 - sparkle_time / 0.3))
            pygame.draw.circle(surface, (255, 255, 255), (sp_x, sp_y), sp_size)

    # ==========================================
    # PROJECTILE SPRITES
    # ==========================================

    def draw_bullet(self, surface, x, y, size=4):
        """Draw player bullet."""
        pygame.draw.circle(surface, (255, 200, 50), (int(x), int(y)), size)
        pygame.draw.circle(surface, (255, 255, 200), (int(x), int(y)), size - 1)
        # Glow
        glow_surf = create_surface_with_alpha(size * 4, size * 4)
        pygame.draw.circle(glow_surf, (255, 200, 50, 50), (size * 2, size * 2), size * 2)
        surface.blit(glow_surf, (int(x) - size * 2, int(y) - size * 2))

    def draw_enemy_projectile(self, surface, x, y, proj_type="bolt"):
        """Draw enemy projectile."""
        if proj_type == "bolt":
            # Lightning bolt
            self._draw_lightning(surface, int(x), int(y), 12)
        elif proj_type == "beam":
            # Laser beam
            pygame.draw.circle(surface, (255, 50, 50), (int(x), int(y)), 4)
            glow_surf = create_surface_with_alpha(16, 16)
            pygame.draw.circle(glow_surf, (255, 50, 50, 60), (8, 8), 8)
            surface.blit(glow_surf, (int(x) - 8, int(y) - 8))
        elif proj_type == "venom":
            # Poison spit
            pygame.draw.circle(surface, (100, 200, 50), (int(x), int(y)), 3)
            pygame.draw.circle(surface, (150, 255, 80), (int(x), int(y)), 2)

    # ==========================================
    # BOOSTER ICONS
    # ==========================================

    def draw_booster_icon(self, surface, x, y, size, booster_type, cooldown_pct=0):
        """Draw booster icon for HUD."""
        rect = pygame.Rect(x, y, size, size)

        # Background
        bg_color = (60, 60, 80)
        pygame.draw.rect(surface, bg_color, rect, border_radius=6)

        # Icon
        icon_margin = 6
        icon_rect = rect.inflate(-icon_margin * 2, -icon_margin * 2)
        cx = x + size // 2
        cy = y + size // 2
        icon_s = size - icon_margin * 2

        if booster_type == "super_jump":
            # Up arrow
            pygame.draw.polygon(surface, (100, 255, 100), [
                (cx, cy - icon_s // 3),
                (cx - icon_s // 3, cy + icon_s // 6),
                (cx + icon_s // 3, cy + icon_s // 6)
            ])
            pygame.draw.rect(surface, (100, 255, 100),
                             (cx - icon_s // 6, cy + icon_s // 6, icon_s // 3, icon_s // 4))
        elif booster_type == "shield":
            # Shield icon
            self.draw_powerup_shield(surface, cx - icon_s // 3,
                                     cy - icon_s // 3, icon_s * 2 // 3)
        elif booster_type == "slowmo":
            # Clock icon
            pygame.draw.circle(surface, (100, 180, 255), (cx, cy), icon_s // 3, 2)
            # Clock hands
            pygame.draw.line(surface, (100, 180, 255), (cx, cy),
                             (cx, cy - icon_s // 4), 2)
            pygame.draw.line(surface, (100, 180, 255), (cx, cy),
                             (cx + icon_s // 5, cy), 2)
        elif booster_type == "bomb":
            # Bomb icon
            pygame.draw.circle(surface, (60, 60, 60), (cx, cy + 2), icon_s // 3)
            pygame.draw.line(surface, (200, 150, 50), (cx, cy - icon_s // 3 + 2),
                             (cx + 3, cy - icon_s // 3 - 3), 2)
            # Spark
            if self._animation_time % 0.5 < 0.25:
                pygame.draw.circle(surface, (255, 200, 50),
                                   (cx + 3, cy - icon_s // 3 - 3), 2)

        # Cooldown overlay
        if cooldown_pct > 0:
            cd_surf = create_surface_with_alpha(size, size)
            pygame.draw.rect(cd_surf, (0, 0, 0, 150), (0, 0, size, size), border_radius=6)

            # Pie reveal (draw filled arc for cooldown)
            cooldown_height = int(size * cooldown_pct)
            pygame.draw.rect(cd_surf, (0, 0, 0, 0),
                             (0, cooldown_height, size, size - cooldown_height))
            surface.blit(cd_surf, (x, y))

        # Border
        border_color = (120, 120, 140)
        if cooldown_pct <= 0 and booster_type:
            border_color = (180, 200, 255)
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=6)

    # ==========================================
    # BACKGROUND
    # ==========================================

    def draw_background(self, surface, theme="day", camera_y=0, width=480, height=800):
        """Draw themed background with gradient and decorations."""
        colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        top = colors["bg_top"]
        bottom = colors["bg_bottom"]

        # Gradient
        for y_pos in range(height):
            t = y_pos / height
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y_pos), (width, y_pos))

        # Stars for night/space themes
        if colors.get("stars", False):
            self._draw_stars(surface, camera_y, width, height)

        # Clouds for day themes
        if theme in ("day", "sunset", "forest"):
            self._draw_clouds(surface, camera_y, width, height, theme)

        # Bubbles for ocean
        if theme == "ocean":
            self._draw_bubbles_bg(surface, camera_y, width, height)

        # Candy decorations
        if theme == "candy":
            self._draw_candy_bg(surface, camera_y, width, height)

        # Lava particles
        if theme == "lava":
            self._draw_lava_bg(surface, camera_y, width, height)

    def _draw_stars(self, surface, camera_y, width, height):
        """Draw background stars."""
        rng = random.Random(42)
        num_stars = 50
        for i in range(num_stars):
            sx = rng.randint(0, width)
            sy = (rng.randint(0, height * 3) + int(camera_y * 0.1)) % (height + 20) - 10
            brightness = rng.randint(150, 255)
            size = rng.choice([1, 1, 1, 2])
            twinkle = int(brightness * (0.7 + 0.3 * math.sin(self._animation_time * 2 + i)))
            color = (twinkle, twinkle, twinkle)
            if size == 1:
                surface.set_at((sx % width, sy % height), color)
            else:
                pygame.draw.circle(surface, color, (sx % width, sy % height), size)

    def _draw_clouds(self, surface, camera_y, width, height, theme):
        """Draw background clouds."""
        rng = random.Random(123)
        num_clouds = 6

        if theme == "sunset":
            cloud_color = (255, 180, 150)
        elif theme == "forest":
            cloud_color = (180, 200, 180)
        else:
            cloud_color = (255, 255, 255)

        for i in range(num_clouds):
            cx = (rng.randint(-50, width + 50) + int(self._animation_time * (5 + i * 2))) % (width + 100) - 50
            cy = (rng.randint(0, height) + int(camera_y * 0.05 * (i + 1))) % height
            cloud_w = rng.randint(60, 120)
            cloud_h = rng.randint(20, 40)
            alpha = rng.randint(40, 80)

            cloud_surf = create_surface_with_alpha(cloud_w + 20, cloud_h + 20)
            # Multiple puffs
            for j in range(4):
                px = 10 + j * cloud_w // 4
                py = 10 + rng.randint(-5, 5)
                pw = cloud_w // 3 + rng.randint(-5, 10)
                ph = cloud_h // 2 + rng.randint(-3, 5)
                pygame.draw.ellipse(cloud_surf, (*cloud_color, alpha),
                                    (px, py, pw, ph))

            surface.blit(cloud_surf, (cx - 10, cy - 10))

    def _draw_bubbles_bg(self, surface, camera_y, width, height):
        """Draw ocean bubbles in background."""
        rng = random.Random(77)
        for i in range(15):
            bx = rng.randint(0, width)
            speed = rng.uniform(0.5, 2)
            by = (rng.randint(0, height * 2) - int(self._animation_time * speed * 30 + camera_y * 0.1)) % (height + 40) - 20
            size = rng.randint(3, 8)
            alpha = rng.randint(20, 50)
            bubble_surf = create_surface_with_alpha(size * 2 + 4, size * 2 + 4)
            pygame.draw.circle(bubble_surf, (200, 230, 255, alpha),
                               (size + 2, size + 2), size, 1)
            surface.blit(bubble_surf, (bx - size - 2, by - size - 2))

    def _draw_candy_bg(self, surface, camera_y, width, height):
        """Draw candy-themed background decorations."""
        rng = random.Random(55)
        colors_list = [(255, 100, 150), (150, 100, 255), (100, 255, 200), (255, 255, 100)]
        for i in range(10):
            sx = rng.randint(0, width)
            sy = (rng.randint(0, height * 2) + int(camera_y * 0.08)) % (height + 20) - 10
            size = rng.randint(4, 10)
            color = rng.choice(colors_list)
            alpha = rng.randint(30, 60)
            candy_surf = create_surface_with_alpha(size * 2 + 4, size * 2 + 4)
            pygame.draw.circle(candy_surf, (*color, alpha), (size + 2, size + 2), size)
            surface.blit(candy_surf, (sx - size - 2, sy - size - 2))

    def _draw_lava_bg(self, surface, camera_y, width, height):
        """Draw lava-themed background particles."""
        rng = random.Random(99)
        for i in range(12):
            px = rng.randint(0, width)
            speed = rng.uniform(1, 3)
            py = (rng.randint(0, height * 2) - int(self._animation_time * speed * 20)) % (height + 30) - 15
            size = rng.randint(2, 5)
            r = rng.randint(200, 255)
            g = rng.randint(50, 150)
            alpha = rng.randint(60, 120)
            part_surf = create_surface_with_alpha(size * 2 + 4, size * 2 + 4)
            pygame.draw.circle(part_surf, (r, g, 0, alpha), (size + 2, size + 2), size)
            surface.blit(part_surf, (px - size - 2, py - size - 2))

    # ==========================================
    # HELPERS
    # ==========================================

    def _draw_star(self, surface, cx, cy, size, color):
        """Draw a 5-pointed star."""
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = size if i % 2 == 0 else size // 2
            points.append((
                int(cx + math.cos(angle) * r),
                int(cy - math.sin(angle) * r)
            ))
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)

    def draw_achievement_icon(self, surface, x, y, size, unlocked=False):
        """Draw achievement icon."""
        color = (255, 200, 50) if unlocked else (100, 100, 100)
        dark = darken_color(color, 0.7)

        # Trophy shape
        pygame.draw.rect(surface, color, (x + size // 4, y + size * 2 // 3, size // 2, size // 6))
        pygame.draw.rect(surface, dark, (x + size // 3, y + size * 5 // 6, size // 3, size // 8))

        # Cup
        pygame.draw.ellipse(surface, color, (x + 2, y + 2, size - 4, size * 2 // 3))
        if unlocked:
            pygame.draw.ellipse(surface, lighten_color(color, 1.3),
                                (x + size // 4, y + size // 6, size // 3, size // 4))

        # Lock for locked
        if not unlocked:
            lock_size = size // 3
            lx = x + size // 2 - lock_size // 2
            ly = y + size // 3
            pygame.draw.rect(surface, (60, 60, 60), (lx, ly, lock_size, lock_size), border_radius=2)
            pygame.draw.arc(surface, (80, 80, 80),
                            (lx + 2, ly - lock_size // 2, lock_size - 4, lock_size),
                            0, math.pi, 2)

    def draw_star_rating(self, surface, x, y, size, filled=True):
        """Draw a single star for rating."""
        color = (255, 200, 50) if filled else (100, 100, 100)
        self._draw_star(surface, x + size // 2, y + size // 2, size // 2, color)
        if not filled:
            # Outline only for empty star
            points = []
            for i in range(10):
                angle = math.pi / 2 + i * math.pi / 5
                r = size // 2 if i % 2 == 0 else size // 4
                points.append((
                    int(x + size // 2 + math.cos(angle) * r),
                    int(y + size // 2 - math.sin(angle) * r)
                ))
            if len(points) >= 3:
                pygame.draw.polygon(surface, (150, 150, 100), points, 1)


# Global renderer instance
sprite_renderer = SpriteRenderer()
"""
botyarajump - Powerups
Collectible powerups that appear in the game world.
"""

import pygame
import math
import random

from settings import save_manager
from utils import create_surface_with_alpha


class Powerup:
    """Base powerup class."""

    SPRING = "spring"
    JETPACK = "jetpack"
    BLASTER = "blaster"
    SHIELD = "shield"
    MAGNET = "magnet"

    ALL_TYPES = [SPRING, JETPACK, BLASTER, SHIELD, MAGNET]

    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.powerup_type = powerup_type
        self.alive = True
        self.collected = False

        # Size based on type
        if powerup_type == self.SPRING:
            self.width = 16
            self.height = 16
        elif powerup_type == self.JETPACK:
            self.width = 20
            self.height = 28
        elif powerup_type == self.BLASTER:
            self.width = 22
            self.height = 16
        elif powerup_type == self.SHIELD:
            self.width = 22
            self.height = 22
        elif powerup_type == self.MAGNET:
            self.width = 20
            self.height = 20
        else:
            self.width = 20
            self.height = 20

        # Floating animation
        self.float_phase = random.uniform(0, math.pi * 2)
        self.float_amplitude = 4
        self.float_speed = 2.0
        self.base_y = y

        # Collection animation
        self.collect_timer = 0
        self.collect_duration = 0.3

    def update(self, dt):
        """Update powerup floating animation."""
        if self.collected:
            self.collect_timer += dt
            if self.collect_timer >= self.collect_duration:
                self.alive = False
            return

        self.float_phase += self.float_speed * dt
        self.y = self.base_y + math.sin(self.float_phase) * self.float_amplitude

    def collect(self, player):
        """Collect this powerup and apply to player."""
        if self.collected:
            return

        self.collected = True
        self.collect_timer = 0

        if self.powerup_type == self.SPRING:
            player.apply_spring()
        elif self.powerup_type == self.JETPACK:
            player.apply_jetpack()
        elif self.powerup_type == self.BLASTER:
            player.apply_blaster()
        elif self.powerup_type == self.SHIELD:
            player.apply_shield()
        elif self.powerup_type == self.MAGNET:
            player.apply_magnet()

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface, camera, renderer):
        if not self.alive:
            return

        sx, sy = camera.world_to_screen(self.x, self.y)

        if self.collected:
            # Collection animation - float up and fade
            progress = self.collect_timer / self.collect_duration
            sy -= progress * 20
            alpha = int(255 * (1 - progress))
            scale = 1.0 + progress * 0.5

            w = max(1, int(self.width * scale))
            h = max(1, int(self.height * scale))

            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            self._draw_specific(temp, 0, 0, w, h, renderer)
            temp.set_alpha(alpha)
            surface.blit(temp, (int(sx) - (w - self.width) // 2,
                                int(sy) - (h - self.height) // 2))
            return

        # Glow effect
        glow_alpha = int(30 + 20 * math.sin(self.float_phase * 2))
        glow_size = max(self.width, self.height) + 10
        glow_surf = create_surface_with_alpha(glow_size, glow_size)
        glow_color = self._get_glow_color()
        pygame.draw.circle(glow_surf, (*glow_color, glow_alpha),
                           (glow_size // 2, glow_size // 2), glow_size // 2)
        surface.blit(glow_surf, (int(sx) + self.width // 2 - glow_size // 2,
                                  int(sy) + self.height // 2 - glow_size // 2))

        self._draw_specific(surface, int(sx), int(sy), self.width, self.height, renderer)

    def _get_glow_color(self):
        """Get glow color for this powerup type."""
        colors = {
            self.SPRING: (255, 255, 100),
            self.JETPACK: (255, 100, 50),
            self.BLASTER: (100, 100, 255),
            self.SHIELD: (100, 200, 255),
            self.MAGNET: (255, 50, 50),
        }
        return colors.get(self.powerup_type, (255, 255, 255))

    def _draw_specific(self, surface, x, y, w, h, renderer):
        """Draw specific powerup type."""
        if self.powerup_type == self.SPRING:
            renderer.draw_powerup_spring(surface, x, y, w, h)
        elif self.powerup_type == self.JETPACK:
            renderer.draw_powerup_jetpack(surface, x, y, w, h)
        elif self.powerup_type == self.BLASTER:
            renderer.draw_powerup_blaster(surface, x, y, w, h)
        elif self.powerup_type == self.SHIELD:
            renderer.draw_powerup_shield(surface, x, y, min(w, h))
        elif self.powerup_type == self.MAGNET:
            renderer.draw_powerup_magnet(surface, x, y, w, h)


class PowerupManager:
    """Manages powerup spawning and collection."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.powerups = []
        self.highest_spawn_y = screen_height
        self.spawn_interval = 300  # Pixels between spawn checks

        # Spawn chances per type
        self.spawn_chances = {
            Powerup.JETPACK: 0.02,
            Powerup.BLASTER: 0.02,
            Powerup.SHIELD: 0.025,
            Powerup.MAGNET: 0.02,
            # Springs are handled by SpringPlatform, not spawned as items
        }

    def reset(self):
        """Reset for new game."""
        self.powerups.clear()
        self.highest_spawn_y = self.screen_height

    def update(self, dt, player, camera):
        """Update all powerups."""
        for powerup in self.powerups:
            if powerup.alive:
                powerup.update(dt)

        # Check collection
        if player.alive:
            self._check_collection(player)

        # Remove dead/off-screen
        visible_top, visible_bottom = camera.get_visible_range(margin=200)
        self.powerups = [
            p for p in self.powerups
            if p.alive and p.base_y < visible_bottom
        ]

        # Spawn new
        self._try_spawn(camera)

    def _check_collection(self, player):
        """Check if player collects any powerup."""
        player_rect = player.get_rect()

        for powerup in self.powerups:
            if not powerup.alive or powerup.collected:
                continue

            if player_rect.colliderect(powerup.get_rect()):
                powerup.collect(player)

    def _try_spawn(self, camera):
        """Try to spawn new powerups."""
        visible_top, _ = camera.get_visible_range()

        while self.highest_spawn_y > visible_top - 500:
            self.highest_spawn_y -= self.spawn_interval

            for ptype, chance in self.spawn_chances.items():
                if random.random() < chance:
                    x = random.randint(20, self.screen_width - 40)
                    powerup = Powerup(x, self.highest_spawn_y, ptype)
                    self.powerups.append(powerup)
                    break  # Only one powerup per interval

    def draw(self, surface, camera, renderer):
        """Draw all visible powerups."""
        for powerup in self.powerups:
            if powerup.alive and camera.is_visible(powerup.base_y, powerup.height):
                powerup.draw(surface, camera, renderer)

    def load_from_level_data(self, level_data):
        """Load powerups from level JSON data."""
        self.powerups.clear()
        grid_size = level_data.get("grid_size", 32)

        for pdata in level_data.get("powerups", []):
            ptype = pdata.get("type", "shield")
            x = pdata.get("x", 0) * grid_size
            y = pdata.get("y", 0) * grid_size

            if ptype in Powerup.ALL_TYPES:
                powerup = Powerup(x, y, ptype)
                self.powerups.append(powerup)
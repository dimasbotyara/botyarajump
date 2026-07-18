"""
botyarajump - Coins
Collectible coins for the in-game economy.
"""

import pygame
import math
import random

from settings import save_manager
from utils import distance, create_surface_with_alpha


class Coin:
    """A collectible coin."""

    def __init__(self, x, y, value=1):
        self.x = x
        self.y = y
        self.value = value
        self.size = 14
        self.alive = True
        self.collected = False

        # Floating animation
        self.float_phase = random.uniform(0, math.pi * 2)
        self.float_speed = 2.5
        self.float_amplitude = 5
        self.base_y = y

        # Collection animation
        self.collect_timer = 0
        self.collect_duration = 0.4
        self.collect_start_x = x
        self.collect_start_y = y
        self.collect_target_x = 0  # Will be set to HUD position
        self.collect_target_y = 0

        # Magnet attraction
        self.being_attracted = False
        self.attract_speed = 8

    def update(self, dt, player=None):
        """Update coin state."""
        if self.collected:
            self.collect_timer += dt
            if self.collect_timer >= self.collect_duration:
                self.alive = False
            return

        # Floating animation
        self.float_phase += self.float_speed * dt
        self.y = self.base_y + math.sin(self.float_phase) * self.float_amplitude

        # Magnet attraction
        if self.being_attracted and player and player.alive:
            px = player.x + player.width // 2
            py = player.y + player.height // 2
            cx = self.x + self.size // 2
            cy = self.y + self.size // 2

            dist = distance(cx, cy, px, py)
            if dist > 3:
                speed = self.attract_speed * dt * 60
                self.x += (px - cx) / dist * speed
                self.y += (py - cy) / dist * speed
                self.base_y += (py - cy) / dist * speed

    def collect(self):
        """Mark coin as collected."""
        if self.collected:
            return 0

        self.collected = True
        self.collect_timer = 0
        self.collect_start_x = self.x
        self.collect_start_y = self.y

        return self.value

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, surface, camera, renderer):
        if not self.alive:
            return

        sx, sy = camera.world_to_screen(self.x, self.y)

        if self.collected:
            # Collection animation - fly to HUD and fade
            progress = self.collect_timer / self.collect_duration

            # Eased progress
            eased = 1 - (1 - progress) ** 3

            # Fly toward top-right (coins counter)
            target_sx = self.collect_target_x
            target_sy = self.collect_target_y
            start_sx, start_sy = camera.world_to_screen(self.collect_start_x,
                                                         self.collect_start_y)

            draw_x = start_sx + (target_sx - start_sx) * eased
            draw_y = start_sy + (target_sy - start_sy) * eased

            alpha = int(255 * (1 - progress))
            scale = 1.0 - progress * 0.5

            size = max(1, int(self.size * scale))

            temp = pygame.Surface((size, size), pygame.SRCALPHA)
            theme = save_manager.equipped.get("theme", "day")
            renderer.draw_coin(temp, 0, 0, size, theme)
            temp.set_alpha(alpha)
            surface.blit(temp, (int(draw_x), int(draw_y)))
            return

        theme = save_manager.equipped.get("theme", "day")
        renderer.draw_coin(surface, int(sx), int(sy), self.size, theme)


class CoinManager:
    """Manages coin spawning and collection."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.coins = []
        self.highest_spawn_y = screen_height
        self.spawn_interval = 80  # Pixels between spawn checks

        # Coin counter HUD position (set by game/UI)
        self.hud_x = screen_width - 60
        self.hud_y = 10

        self._update_difficulty()

    def _update_difficulty(self):
        """Update from difficulty settings."""
        diff = save_manager.get_difficulty_settings()
        self.spawn_chance = diff["coin_spawn_chance"]

    def reset(self):
        """Reset for new game."""
        self.coins.clear()
        self.highest_spawn_y = self.screen_height
        self._update_difficulty()

    def update(self, dt, player, camera):
        """Update all coins."""
        for coin in self.coins:
            if coin.alive:
                coin.update(dt, player)

        # Magnet attraction
        if player and player.alive and player.has_magnet:
            self._apply_magnet(player)

        # Check collection
        if player and player.alive:
            self._check_collection(player)

        # Remove dead/off-screen
        visible_top, visible_bottom = camera.get_visible_range(margin=200)
        self.coins = [
            c for c in self.coins
            if c.alive and c.base_y < visible_bottom
        ]

        # Spawn new
        self._try_spawn(camera)

    def _apply_magnet(self, player):
        """Apply magnet attraction to nearby coins."""
        px = player.x + player.width // 2
        py = player.y + player.height // 2

        for coin in self.coins:
            if not coin.alive or coin.collected:
                continue

            cx = coin.x + coin.size // 2
            cy = coin.y + coin.size // 2

            dist = distance(px, py, cx, cy)
            if dist < player.magnet_range:
                coin.being_attracted = True
            else:
                coin.being_attracted = False

    def _check_collection(self, player):
        """Check if player collects coins."""
        player_rect = player.get_rect()
        collected_total = 0

        for coin in self.coins:
            if not coin.alive or coin.collected:
                continue

            if player_rect.colliderect(coin.get_rect()):
                value = coin.collect()
                coin.collect_target_x = self.hud_x
                coin.collect_target_y = self.hud_y
                collected_total += value

        if collected_total > 0:
            save_manager.earn_coins(collected_total)
            player.session_coins += collected_total

        return collected_total

    def _try_spawn(self, camera):
        """Try to spawn new coins."""
        visible_top, _ = camera.get_visible_range()

        while self.highest_spawn_y > visible_top - 500:
            self.highest_spawn_y -= self.spawn_interval

            if random.random() < self.spawn_chance:
                x = random.randint(15, self.screen_width - 30)
                coin = Coin(x, self.highest_spawn_y)
                self.coins.append(coin)

                # Sometimes spawn a cluster of coins
                if random.random() < 0.3:
                    num_extra = random.randint(1, 3)
                    for i in range(num_extra):
                        cx = x + random.randint(-30, 30)
                        cy = self.highest_spawn_y + random.randint(-20, 20)
                        cx = max(10, min(self.screen_width - 20, cx))
                        extra_coin = Coin(cx, cy)
                        self.coins.append(extra_coin)

    def spawn_from_enemy(self, enemy_x, enemy_y, count=3):
        """Spawn coins when enemy dies."""
        for i in range(count):
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-20, 10)
            coin = Coin(enemy_x + offset_x, enemy_y + offset_y)
            coin.base_y = enemy_y + offset_y
            self.coins.append(coin)

    def draw(self, surface, camera, renderer):
        """Draw all visible coins."""
        for coin in self.coins:
            if coin.alive and camera.is_visible(coin.base_y, coin.size, margin=30):
                coin.draw(surface, camera, renderer)

    def load_from_level_data(self, level_data):
        """Load coins from level JSON data."""
        self.coins.clear()
        grid_size = level_data.get("grid_size", 32)

        for cdata in level_data.get("coins", []):
            x = cdata.get("x", 0) * grid_size
            y = cdata.get("y", 0) * grid_size
            value = cdata.get("value", 1)
            coin = Coin(x, y, value)
            self.coins.append(coin)

        if self.coins:
            self.highest_spawn_y = min(c.base_y for c in self.coins)
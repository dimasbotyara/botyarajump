"""
botyarajump - Player
Player character with movement, jumping, shooting, and powerup states.
"""

import pygame
import math
import time

from settings import (
    GRAVITY, PLAYER_JUMP_VELOCITY, PLAYER_SPEED, PLAYER_MAX_FALL_SPEED,
    save_manager
)
from utils import clamp, key_name_to_key


class Bullet:
    """Player projectile."""

    def __init__(self, x, y, direction_x, direction_y, speed=10):
        self.x = x
        self.y = y
        self.vx = direction_x * speed
        self.vy = direction_y * speed
        self.alive = True
        self.size = 4
        self.lifetime = 2.0  # seconds
        self.timer = 0

    def update(self, dt):
        """Update bullet position."""
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.timer += dt
        if self.timer >= self.lifetime:
            self.alive = False

    def get_rect(self):
        """Get collision rect."""
        return pygame.Rect(self.x - self.size, self.y - self.size,
                           self.size * 2, self.size * 2)


class Player:
    """The player character (doodler)."""

    def __init__(self, x, y, screen_width):
        # Position and size
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.screen_width = screen_width

        # Velocity
        self.vx = 0
        self.vy = 0

        # State
        self.alive = True
        self.facing_right = True
        self.on_platform = False
        self.is_shooting = False
        self._shoot_timer = 0

        # Jump tracking
        self.jump_count = 0
        self.can_double_jump = False

        # Powerup states
        self.has_jetpack = False
        self.jetpack_timer = 0
        self.jetpack_duration = 3.0

        self.has_blaster = False
        self.blaster_timer = 0
        self.blaster_duration = 5.0
        self.blaster_fire_rate = 0.2  # seconds between shots
        self.blaster_fire_timer = 0

        self.has_shield = False
        self.shield_hits = 0

        self.has_magnet = False
        self.magnet_timer = 0
        self.magnet_duration = 5.0
        self.magnet_range = 150

        # Booster states
        self.shield_booster_active = False
        self.shield_booster_timer = 0

        self.slowmo_active = False
        self.slowmo_timer = 0

        # Invincibility frames
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1.5

        # Bullets
        self.bullets = []

        # Input state
        self._move_left = False
        self._move_right = False
        self._shoot_pressed = False

        # Stats tracking for this game session
        self.session_kills = 0
        self.session_coins = 0
        self.session_platforms = 0
        self.session_powerups_used = set()

        # Controls cache
        self._update_controls()

    def _update_controls(self):
        """Cache control key bindings."""
        controls = save_manager.get_controls()
        self._left_keys = []
        self._right_keys = []
        self._shoot_keys = []

        for key_name in controls.get("left", []):
            k = key_name_to_key(key_name)
            if k is not None:
                self._left_keys.append(k)

        for key_name in controls.get("right", []):
            k = key_name_to_key(key_name)
            if k is not None:
                self._right_keys.append(k)

        for key_name in controls.get("shoot", []):
            k = key_name_to_key(key_name)
            if k is not None:
                self._shoot_keys.append(k)

    def reset(self, x, y):
        """Reset player for new game."""
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.facing_right = True
        self.on_platform = False
        self.is_shooting = False
        self._shoot_timer = 0
        self.jump_count = 0

        self.has_jetpack = False
        self.jetpack_timer = 0
        self.has_blaster = False
        self.blaster_timer = 0
        self.blaster_fire_timer = 0
        self.has_shield = False
        self.shield_hits = 0
        self.has_magnet = False
        self.magnet_timer = 0

        self.shield_booster_active = False
        self.shield_booster_timer = 0
        self.slowmo_active = False
        self.slowmo_timer = 0

        self.invincible = False
        self.invincible_timer = 0

        self.bullets.clear()

        # FIX: Reset input state to prevent sticky keys
        self._move_left = False
        self._move_right = False
        self._shoot_pressed = False

        self.session_kills = 0
        self.session_coins = 0
        self.session_platforms = 0
        self.session_powerups_used = set()

        self._update_controls()

    def handle_event(self, event):
        """Handle input events."""
        if event.type == pygame.KEYDOWN:
            if event.key in self._left_keys:
                self._move_left = True
            if event.key in self._right_keys:
                self._move_right = True
            if event.key in self._shoot_keys:
                self._shoot_pressed = True
                self._try_shoot()

        elif event.type == pygame.KEYUP:
            if event.key in self._left_keys:
                self._move_left = False
            if event.key in self._right_keys:
                self._move_right = False
            if event.key in self._shoot_keys:
                self._shoot_pressed = False

    def _try_shoot(self):
        """Attempt to fire a bullet."""
        if self.has_blaster and self.blaster_fire_timer <= 0:
            self._fire_bullet()
            self.blaster_fire_timer = self.blaster_fire_rate
        elif not self.has_blaster:
            # Normal single shot (upward)
            self._fire_bullet()

    def _fire_bullet(self):
        """Fire a bullet upward."""
        bullet_x = self.x + self.width // 2
        bullet_y = self.y
        # Shoot upward
        bullet = Bullet(bullet_x, bullet_y, 0, -1, speed=12)
        self.bullets.append(bullet)
        self.is_shooting = True
        self._shoot_timer = 0.15

    def update(self, dt):
        """Update player physics and state."""
        if not self.alive:
            # Fall off screen
            self.vy += GRAVITY * dt * 60
            self.y += self.vy * dt * 60
            return

        # Horizontal movement
        target_vx = 0
        if self._move_left:
            target_vx -= PLAYER_SPEED
            self.facing_right = False
        if self._move_right:
            target_vx += PLAYER_SPEED
            self.facing_right = True

        # Smooth horizontal acceleration
        accel = 0.3
        if target_vx != 0:
            self.vx += (target_vx - self.vx) * accel
        else:
            self.vx *= 0.8
            if abs(self.vx) < 0.1:
                self.vx = 0

        # Jetpack
        if self.has_jetpack:
            self.jetpack_timer -= dt
            self.vy = -8  # Strong upward velocity
            if self.jetpack_timer <= 0:
                self.has_jetpack = False

        # Normal gravity
        if not self.has_jetpack:
            gravity_mult = 1.0
            if self.slowmo_active:
                gravity_mult = 0.4

            self.vy += GRAVITY * dt * 60 * gravity_mult
            self.vy = min(self.vy, PLAYER_MAX_FALL_SPEED)

        # Apply velocity
        speed_mult = 0.4 if self.slowmo_active else 1.0
        self.x += self.vx * dt * 60 * speed_mult
        self.y += self.vy * dt * 60 * speed_mult

        # Screen wrapping
        if self.x + self.width < 0:
            self.x = self.screen_width
        elif self.x > self.screen_width:
            self.x = -self.width

        # Update powerup timers
        self._update_powerups(dt)

        # Update bullets
        self._update_bullets(dt)

        # Update shoot animation timer
        if self.is_shooting:
            self._shoot_timer -= dt
            if self._shoot_timer <= 0:
                self.is_shooting = False

        # Invincibility
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False

        # Auto-fire with blaster
        if self.has_blaster and self._shoot_pressed:
            self.blaster_fire_timer -= dt
            if self.blaster_fire_timer <= 0:
                self._fire_bullet()
                self.blaster_fire_timer = self.blaster_fire_rate

        self.on_platform = False

    def _update_powerups(self, dt):
        """Update powerup timers."""
        if self.has_blaster:
            self.blaster_timer -= dt
            if self.blaster_timer <= 0:
                self.has_blaster = False
                self.blaster_fire_timer = 0

        if self.has_magnet:
            self.magnet_timer -= dt
            if self.magnet_timer <= 0:
                self.has_magnet = False

        if self.shield_booster_active:
            self.shield_booster_timer -= dt
            if self.shield_booster_timer <= 0:
                self.shield_booster_active = False

        if self.slowmo_active:
            self.slowmo_timer -= dt
            if self.slowmo_timer <= 0:
                self.slowmo_active = False

    def _update_bullets(self, dt):
        """Update all bullets."""
        for bullet in self.bullets:
            bullet.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]

    def jump(self, velocity=None):
        """Make the player jump."""
        if velocity is None:
            velocity = PLAYER_JUMP_VELOCITY
        self.vy = velocity
        self.jump_count += 1
        save_manager.add_stat("total_jumps")

    def super_jump(self):
        """Spring/super jump."""
        self.vy = PLAYER_JUMP_VELOCITY * 1.8
        self.jump_count += 1
        save_manager.add_stat("total_jumps")

    def apply_jetpack(self):
        """Activate jetpack powerup."""
        self.has_jetpack = True
        self.jetpack_timer = self.jetpack_duration
        self.session_powerups_used.add("jetpack")
        save_manager.add_nested_stat("powerups_used", "jetpack")

    def apply_blaster(self):
        """Activate blaster powerup."""
        self.has_blaster = True
        self.blaster_timer = self.blaster_duration
        self.blaster_fire_timer = 0
        self.session_powerups_used.add("blaster")
        save_manager.add_nested_stat("powerups_used", "blaster")

    def apply_shield(self):
        """Activate shield powerup."""
        self.has_shield = True
        self.shield_hits = 1
        self.session_powerups_used.add("shield")
        save_manager.add_nested_stat("powerups_used", "shield")

    def apply_magnet(self):
        """Activate magnet powerup."""
        self.has_magnet = True
        self.magnet_timer = self.magnet_duration
        self.session_powerups_used.add("magnet")
        save_manager.add_nested_stat("powerups_used", "magnet")

    def apply_spring(self):
        """Use a spring for super jump."""
        self.super_jump()
        self.session_powerups_used.add("spring")
        save_manager.add_nested_stat("powerups_used", "spring")

    # Booster activations
    def activate_super_jump_booster(self):
        """Booster: one-time super jump."""
        self.vy = PLAYER_JUMP_VELOCITY * 2.5

    def activate_shield_booster(self, duration=5.0):
        """Booster: temporary shield."""
        self.shield_booster_active = True
        self.shield_booster_timer = duration

    def activate_slowmo(self, duration=3.0):
        """Booster: slow motion."""
        self.slowmo_active = True
        self.slowmo_timer = duration

    def take_damage(self):
        """Player takes damage. Returns True if player dies."""
        if self.invincible:
            return False

        # Check shield (powerup)
        if self.has_shield and self.shield_hits > 0:
            self.shield_hits -= 1
            if self.shield_hits <= 0:
                self.has_shield = False
            self.invincible = True
            self.invincible_timer = self.invincible_duration
            return False

        # Check shield booster
        if self.shield_booster_active:
            self.shield_booster_active = False
            self.shield_booster_timer = 0
            self.invincible = True
            self.invincible_timer = self.invincible_duration
            return False

        # Player dies
        self.alive = False
        self.vy = PLAYER_JUMP_VELOCITY * 0.5  # Small bounce up on death
        save_manager.add_stat("deaths")
        return True

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_feet_rect(self):
        """Get feet rectangle for platform collision (bottom part of player)."""
        feet_height = 10
        return pygame.Rect(self.x + 4, self.y + self.height - feet_height,
                           self.width - 8, feet_height)

    def get_head_rect(self):
        """Get head rectangle for stomp detection on enemies."""
        head_height = 10
        return pygame.Rect(self.x + 4, self.y, self.width - 8, head_height)

    def get_body_rect(self):
        """Get body rectangle (excluding feet) for enemy damage collision."""
        return pygame.Rect(self.x + 2, self.y + 5, self.width - 4, self.height - 15)

    def get_center(self):
        """Get center position."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def is_falling(self):
        """Check if player is falling (moving downward)."""
        return self.vy > 0

    def is_visible(self):
        """Check if player should be drawn (handles invincibility flicker)."""
        if self.invincible:
            # Flicker effect
            return int(self.invincible_timer * 10) % 2 == 0
        return True

    def draw(self, surface, camera, renderer):
        """Draw player and bullets."""
        if not self.is_visible() and self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        skin_id = save_manager.equipped.get("skin", "default")

        renderer.draw_player(
            surface,
            int(screen_x), int(screen_y),
            self.width, self.height,
            skin_id=skin_id,
            facing_right=self.facing_right,
            velocity_y=self.vy,
            is_shooting=self.is_shooting,
            has_shield=self.has_shield or self.shield_booster_active,
            has_jetpack=self.has_jetpack,
            has_blaster=self.has_blaster
        )

        # Draw wrapping ghost (if near edge)
        if self.x < 0:
            renderer.draw_player(
                surface,
                int(screen_x + self.screen_width), int(screen_y),
                self.width, self.height,
                skin_id=skin_id,
                facing_right=self.facing_right,
                velocity_y=self.vy,
                is_shooting=self.is_shooting,
                has_shield=self.has_shield or self.shield_booster_active,
                has_jetpack=self.has_jetpack,
                has_blaster=self.has_blaster
            )
        elif self.x + self.width > self.screen_width:
            renderer.draw_player(
                surface,
                int(screen_x - self.screen_width), int(screen_y),
                self.width, self.height,
                skin_id=skin_id,
                facing_right=self.facing_right,
                velocity_y=self.vy,
                is_shooting=self.is_shooting,
                has_shield=self.has_shield or self.shield_booster_active,
                has_jetpack=self.has_jetpack,
                has_blaster=self.has_blaster
            )

        # Draw bullets
        for bullet in self.bullets:
            bx, by = camera.world_to_screen(bullet.x, bullet.y)
            renderer.draw_bullet(surface, bx, by, bullet.size)
"""
botyarajump - Enemies
All enemy types with AI, physics, and rendering.
"""

import pygame
import math
import random

from settings import save_manager
from utils import clamp, distance


class EnemyProjectile:
    """Projectile fired by enemies."""

    def __init__(self, x, y, vx, vy, proj_type="bolt", damage=1):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.proj_type = proj_type
        self.damage = damage
        self.alive = True
        self.size = 5
        self.lifetime = 4.0
        self.timer = 0

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.timer += dt
        if self.timer >= self.lifetime:
            self.alive = False

    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size,
                           self.size * 2, self.size * 2)

    def draw(self, surface, camera, renderer):
        sx, sy = camera.world_to_screen(self.x, self.y)
        renderer.draw_enemy_projectile(surface, sx, sy, self.proj_type)


class Enemy:
    """Base enemy class."""

    SLUG = "slug"
    BAT = "bat"
    BLACK_HOLE = "black_hole"
    GHOST = "ghost"
    RED_BALL = "red_ball"
    SNAKE = "snake"
    EVIL_CLOUD = "evil_cloud"
    UFO = "ufo"

    ALL_TYPES = [SLUG, BAT, BLACK_HOLE, GHOST, RED_BALL, SNAKE, EVIL_CLOUD, UFO]

    def __init__(self, x, y, width, height, enemy_type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.enemy_type = enemy_type
        self.alive = True
        self.health = 1
        self.facing_right = True
        self.speed_mult = 1.0

        # Score value
        self.score_value = 100

        # Projectiles this enemy has fired
        self.projectiles = []

        # Death animation
        self.dying = False
        self.death_timer = 0
        self.death_duration = 0.4

    def update(self, dt, player=None):
        """Update enemy. Override in subclasses."""
        # Update projectiles
        for proj in self.projectiles:
            proj.update(dt)
        self.projectiles = [p for p in self.projectiles if p.alive]

        # Death animation
        if self.dying:
            self.death_timer += dt
            if self.death_timer >= self.death_duration:
                self.alive = False

    def take_hit(self):
        """Enemy takes a hit. Returns True if killed."""
        self.health -= 1
        if self.health <= 0:
            self.dying = True
            self.death_timer = 0
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_stomp_rect(self):
        """Top area where player can stomp to kill."""
        stomp_h = max(8, self.height // 3)
        return pygame.Rect(self.x, self.y, self.width, stomp_h)

    def get_damage_rect(self):
        """Area that damages the player."""
        return pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4)

    def draw(self, surface, camera, renderer):
        if not self.alive:
            return

        sx, sy = camera.world_to_screen(self.x, self.y)

        if self.dying:
            # Death animation - shrink and fade
            progress = clamp(self.death_timer / self.death_duration, 0, 1)
            scale = 1.0 - progress
            alpha = int(255 * (1.0 - progress))

            if scale > 0.05:
                w = max(1, int(self.width * scale))
                h = max(1, int(self.height * scale))
                dx = (self.width - w) // 2
                dy = (self.height - h) // 2
                # Draw with death effect
                death_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                self._draw_specific(death_surf, 0, 0, w, h, renderer)
                death_surf.set_alpha(alpha)
                surface.blit(death_surf, (sx + dx, sy + dy))

                # Death particles (stars)
                for i in range(3):
                    px = sx + self.width // 2 + int(math.cos(progress * 10 + i * 2) * 20 * progress)
                    py = sy + self.height // 2 + int(math.sin(progress * 10 + i * 2) * 20 * progress)
                    star_size = max(1, int(4 * (1 - progress)))
                    pygame.draw.circle(surface, (255, 255, 100), (int(px), int(py)), star_size)
            return

        self._draw_specific(surface, int(sx), int(sy), self.width, self.height, renderer)

        # Draw projectiles
        for proj in self.projectiles:
            proj.draw(surface, camera, renderer)

    def _draw_specific(self, surface, x, y, w, h, renderer):
        """Override to draw specific enemy type."""
        pass


class Slug(Enemy):
    """Slug enemy - sits on platform, patrols left-right."""

    def __init__(self, x, y, patrol_range=60):
        super().__init__(x, y, 30, 20, Enemy.SLUG)
        self.start_x = x
        self.patrol_range = patrol_range
        self.speed = 1.0
        self.direction = 1
        self.score_value = 50

    def update(self, dt, player=None):
        super().update(dt, player)
        if self.dying:
            return

        self.x += self.speed * self.direction * self.speed_mult * dt * 60

        if self.x > self.start_x + self.patrol_range:
            self.direction = -1
            self.facing_right = False
        elif self.x < self.start_x - self.patrol_range:
            self.direction = 1
            self.facing_right = True

    def _draw_specific(self, surface, x, y, w, h, renderer):
        renderer.draw_enemy_slug(surface, x, y, w, h, self.facing_right)


class Bat(Enemy):
    """Bat enemy - flies horizontally with sine wave pattern."""

    def __init__(self, x, y, fly_range=120):
        super().__init__(x, y, 35, 25, Enemy.BAT)
        self.start_x = x
        self.start_y = y
        self.fly_range = fly_range
        self.speed = 1.5
        self.phase = random.uniform(0, math.pi * 2)
        self.wave_amplitude = 20
        self.wave_speed = 3.0
        self.score_value = 80

    def update(self, dt, player=None):
        super().update(dt, player)
        if self.dying:
            return

        self.phase += self.speed * self.speed_mult * dt

        # Horizontal movement
        self.x = self.start_x + math.sin(self.phase) * self.fly_range / 2

        # Vertical sine wave
        self.y = self.start_y + math.sin(self.phase * self.wave_speed) * self.wave_amplitude

        self.facing_right = math.cos(self.phase) > 0

    def _draw_specific(self, surface, x, y, w, h, renderer):
        renderer.draw_enemy_bat(surface, x, y, w, h)


class BlackHole(Enemy):
    """Black hole - pulls player toward its center."""

    def __init__(self, x, y, pull_range=120, pull_strength=2.0):
        super().__init__(x, y, 40, 40, Enemy.BLACK_HOLE)
        self.pull_range = pull_range
        self.pull_strength = pull_strength
        self.score_value = 150
        self.health = 2  # Takes 2 hits

    def update(self, dt, player=None):
        super().update(dt, player)
        if self.dying or player is None or not player.alive:
            return

        # Pull player toward center
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        px = player.x + player.width // 2
        py = player.y + player.height // 2

        dist = distance(cx, cy, px, py)

        if dist < self.pull_range and dist > 5:
            # Calculate pull force (stronger when closer)
            force = self.pull_strength * (1 - dist / self.pull_range) * self.speed_mult
            dx = (cx - px) / dist * force
            dy = (cy - py) / dist * force

            player.vx += dx * dt * 60
            player.vy += dy * dt * 60 * 0.5  # Less vertical pull for balance

    def _draw_specific(self, surface, x, y, w, h, renderer):
        renderer.draw_enemy_black_hole(surface, x, y, min(w, h))


class Ghost(Enemy):
    """Ghost enemy - slowly follows the player, passes through platforms."""

    def __init__(self, x, y):
        super().__init__(x, y, 30, 35, Enemy.GHOST)
        self.speed = 0.8
        self.score_value = 120
        self.phase = random.uniform(0, math.pi * 2)

    def update(self, dt, player=None):
        super().update(dt, player)
        if self.dying or player is None or not player.alive:
            return

        self.phase += dt * 2

        # Move toward player
        px = player.x + player.width // 2
        py = player.y + player.height // 2
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2

        dist = distance(cx, cy, px, py)

        if dist > 5:
            dx = (px - cx) / dist * self.speed * self.speed_mult * dt * 60
            dy = (py - cy) / dist * self.speed * self.speed_mult * dt * 60

            self.x += dx
            self.y += dy

            # Slight wave motion
            self.x += math.sin(self.phase) * 0.5
            self.y += math.cos(self.phase * 0.7) * 0.3

            self.facing_right = dx > 0

    def _draw_specific(self, surface, x, y, w, h, renderer):
        renderer.draw_enemy_ghost(surface, x, y, w, h)


class RedBall(Enemy):
    """Red ball - bounces up and down between platforms."""

    def __init__(self, x, y, bounce_height=80):
        super().__init__(x, y, 25, 25, Enemy.RED_BALL)
        self.start_y = y
        self.bounce_height = bounce_height
        self.vy = -4
        self.gravity = 0.3
        self.score_value = 90
        self.phase = random.uniform(0, math.pi * 2)

    def update(self, dt, player=None):
        super().update(dt, player)
        if self.dying:
            return

        self.vy += self.gravity * self.speed_mult * dt * 60
        self.y += self.vy * self.speed_mult * dt * 60

        # Bounce at original position
        if self.y >= self.start_y:
            self.y = self.start_y
            self.vy = -4 * (0.8 + random.uniform(0, 0.4))

        # Slight horizontal wobble
        self.phase += dt * 3
        self.x += math.sin(self.phase) * 0.5

    def _draw_specific(self, surface, x, y, w, h, renderer):
        renderer.draw_enemy_red_ball(surface, x, y, min(w, h))


class Snake(Enemy):
    """Snake enemy - occupies platform, shoots venom."""

    def __init__(self, x, y, platform_width=70):
        super().__init__(x, y, 35, 15, Enemy.SNAKE)
        self.start_x = x
        self.platform_width = platform_width
        self.shoot_cooldown = 3.0
        self.shoot_timer = random.uniform(0, self.shoot_cooldown)
        self.speed = 0.6
        self.direction = 1
        self.score_value = 110

    def update(self, dt, player=None):
        super().update(dt, player)
        if self.dying:
            return

        # Patrol on platform
        self.x += self.speed * self.direction * self.speed_mult * dt * 60

        # Proper patrol bounds
        max_x = self.start_x + self.platform_width - self.width
        if self.x >= max_x:
            self.direction = -1
            self.x = max_x
        elif self.x <= self.start_x:
            self.direction = 1
            self.x = self.start_x

        self.facing_right = self.direction > 0

        # Shooting
        if player and player.alive:
            self.shoot_timer -= dt
            if self.shoot_timer <= 0:
                self._shoot_at_player(player)
                self.shoot_timer = self.shoot_cooldown

    def _shoot_at_player(self, player):
        """Shoot venom at player."""
        cx = self.x + self.width // 2
        cy = self.y
        px = player.x + player.width // 2
        py = player.y + player.height // 2

        dist = distance(cx, cy, px, py)
        if dist < 300 and dist > 5:
            vx = (px - cx) / dist * 3
            vy = (py - cy) / dist * 3
            proj = EnemyProjectile(cx, cy, vx, vy, "venom")
            self.projectiles.append(proj)

    def _draw_specific(self, surface, x, y, w, h, renderer):
        renderer.draw_enemy_snake(surface, x, y, w, h, self.facing_right)


class EvilCloud(Enemy):
    """Evil cloud - appears above, shoots lightning down."""

    def __init__(self, x, y):
        super().__init__(x, y, 60, 40, Enemy.EVIL_CLOUD)
        self.speed = 1.2
        self.direction = 1
        self.move_range = 100
        self.start_x = x
        self.shoot_cooldown = 2.5
        self.shoot_timer = random.uniform(1.0, self.shoot_cooldown)
        self.score_value = 130
        self.health = 2

    def update(self, dt, player=None):
        super().update(dt, player)
        if self.dying:
            return

        # Horizontal patrol
        self.x += self.speed * self.direction * self.speed_mult * dt * 60

        if self.x > self.start_x + self.move_range:
            self.direction = -1
        elif self.x < self.start_x - self.move_range:
            self.direction = 1

        # Shoot lightning downward
        if player and player.alive:
            self.shoot_timer -= dt
            if self.shoot_timer <= 0:
                self._shoot_lightning()
                self.shoot_timer = self.shoot_cooldown

    def _shoot_lightning(self):
        """Fire lightning bolt downward."""
        cx = self.x + self.width // 2
        cy = self.y + self.height
        proj = EnemyProjectile(cx, cy, 0, 4, "bolt")
        self.projectiles.append(proj)

    def _draw_specific(self, surface, x, y, w, h, renderer):
        renderer.draw_enemy_evil_cloud(surface, x, y, w, h)


class UFO(Enemy):
    """UFO enemy - flies above, shoots beams down."""

    def __init__(self, x, y):
        super().__init__(x, y, 50, 30, Enemy.UFO)
        self.speed = 1.8
        self.direction = 1
        self.move_range = 150
        self.start_x = x
        self.shoot_cooldown = 3.0
        self.shoot_timer = random.uniform(1.5, self.shoot_cooldown)
        self.score_value = 200
        self.health = 3
        self.phase = random.uniform(0, math.pi * 2)

    def update(self, dt, player=None):
        super().update(dt, player)
        if self.dying:
            return

        self.phase += dt * 2

        # Smooth horizontal movement
        self.x = self.start_x + math.sin(self.phase * 0.5) * self.move_range / 2

        # Slight vertical bob
        self.y += math.sin(self.phase * 1.5) * 0.3

        # Shoot beam toward player
        if player and player.alive:
            self.shoot_timer -= dt
            if self.shoot_timer <= 0:
                self._shoot_beam(player)
                self.shoot_timer = self.shoot_cooldown

    def _shoot_beam(self, player):
        """Fire beam toward player."""
        cx = self.x + self.width // 2
        cy = self.y + self.height
        px = player.x + player.width // 2
        py = player.y + player.height // 2

        dist = distance(cx, cy, px, py)
        if dist < 400 and dist > 5:
            vx = (px - cx) / dist * 3.5
            vy = (py - cy) / dist * 3.5
            proj = EnemyProjectile(cx, cy, vx, vy, "beam")
            self.projectiles.append(proj)

    def _draw_specific(self, surface, x, y, w, h, renderer):
        renderer.draw_enemy_ufo(surface, x, y, w, h)


# ==================================================
# ENEMY FACTORY
# ==================================================

def create_enemy(enemy_type, x, y, **kwargs):
    """Factory function to create an enemy by type string."""
    if enemy_type == Enemy.SLUG:
        return Slug(x, y, patrol_range=kwargs.get("patrol_range", 60))
    elif enemy_type == Enemy.BAT:
        return Bat(x, y, fly_range=kwargs.get("fly_range", 120))
    elif enemy_type == Enemy.BLACK_HOLE:
        return BlackHole(x, y,
                         pull_range=kwargs.get("pull_range", 120),
                         pull_strength=kwargs.get("pull_strength", 2.0))
    elif enemy_type == Enemy.GHOST:
        return Ghost(x, y)
    elif enemy_type == Enemy.RED_BALL:
        return RedBall(x, y, bounce_height=kwargs.get("bounce_height", 80))
    elif enemy_type == Enemy.SNAKE:
        return Snake(x, y, platform_width=kwargs.get("platform_width", 70))
    elif enemy_type == Enemy.EVIL_CLOUD:
        return EvilCloud(x, y)
    elif enemy_type == Enemy.UFO:
        return UFO(x, y)
    else:
        return Slug(x, y)


class EnemyManager:
    """Manages enemy spawning and lifecycle."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.enemies = []
        # Removed all_projectiles list as it was unused and created overhead

        # Spawn tracking
        self.highest_spawn_y = screen_height
        self.spawn_check_interval = 100  # Check every 100 pixels of height

        self._update_difficulty()

    def _update_difficulty(self):
        """Update spawn parameters from difficulty."""
        diff = save_manager.get_difficulty_settings()
        self.spawn_chance = diff["enemy_spawn_chance"]
        self.speed_mult = diff["enemy_speed_mult"]

    def reset(self):
        """Reset for new game."""
        self.enemies.clear()
        self.highest_spawn_y = self.screen_height
        self._update_difficulty()

    def update(self, dt, player, camera):
        """Update all enemies."""
        # Update existing enemies
        for enemy in self.enemies:
            if enemy.alive:
                enemy.speed_mult = self.speed_mult
                enemy.update(dt, player)

        # Remove dead/off-screen enemies
        visible_top, visible_bottom = camera.get_visible_range(margin=300)
        self.enemies = [
            e for e in self.enemies
            if e.alive and visible_top - 200 < e.y < visible_bottom
        ]

        # Spawn new enemies
        self._try_spawn(camera)

    def _try_spawn(self, camera):
        """Try to spawn new enemies above the visible area."""
        visible_top, visible_bottom = camera.get_visible_range()

        while self.highest_spawn_y > visible_top - 400:
            self.highest_spawn_y -= self.spawn_check_interval

            if random.random() < self.spawn_chance:
                enemy = self._spawn_random_enemy(self.highest_spawn_y)
                if enemy:
                    self.enemies.append(enemy)

    def _spawn_random_enemy(self, y):
        """Spawn a random enemy at given y."""
        x = random.randint(20, self.screen_width - 60)

        # Weight different enemy types
        # Harder enemies appear less often
        weights = {
            Enemy.SLUG: 25,
            Enemy.BAT: 20,
            Enemy.RED_BALL: 18,
            Enemy.GHOST: 12,
            Enemy.SNAKE: 10,
            Enemy.EVIL_CLOUD: 8,
            Enemy.BLACK_HOLE: 5,
            Enemy.UFO: 2
        }

        # Build weighted list
        choices = []
        for etype, weight in weights.items():
            choices.extend([etype] * weight)

        enemy_type = random.choice(choices)
        enemy = create_enemy(enemy_type, x, y)
        enemy.speed_mult = self.speed_mult

        return enemy

    def check_stomp_collision(self, player):
        """Check if player stomps on an enemy (landing on top).
        Returns list of killed enemies.
        """
        killed = []

        if not player.is_falling() or not player.alive:
            return killed

        feet_rect = player.get_feet_rect()

        for enemy in self.enemies:
            if not enemy.alive or enemy.dying:
                continue

            stomp_rect = enemy.get_stomp_rect()
            if feet_rect.colliderect(stomp_rect):
                was_killed = enemy.take_hit()
                if was_killed:
                    killed.append(enemy)
                # Player bounces off
                player.jump()
                break

        return killed

    def check_damage_collision(self, player):
        """Check if enemy or projectile damages the player.
        Returns True if player took damage.
        """
        if not player.alive or player.invincible:
            return False

        body_rect = player.get_body_rect()

        # Check enemy bodies
        for enemy in self.enemies:
            if not enemy.alive or enemy.dying:
                continue

            damage_rect = enemy.get_damage_rect()
            if body_rect.colliderect(damage_rect):
                return True

        # Check projectiles
        for enemy in self.enemies:
            for proj in enemy.projectiles:
                if not proj.alive:
                    continue
                if body_rect.colliderect(proj.get_rect()):
                    proj.alive = False
                    return True

        return False

    def check_bullet_collision(self, bullets):
        """Check if player bullets hit enemies.
        Returns list of killed enemies.
        """
        killed = []

        for bullet in bullets:
            if not bullet.alive:
                continue

            bullet_rect = bullet.get_rect()

            for enemy in self.enemies:
                if not enemy.alive or enemy.dying:
                    continue

                if bullet_rect.colliderect(enemy.get_rect()):
                    bullet.alive = False
                    was_killed = enemy.take_hit()
                    if was_killed:
                        killed.append(enemy)
                    break

        return killed

    def kill_all_on_screen(self, camera):
        """Kill all visible enemies (bomb booster)."""
        killed = []
        for enemy in self.enemies:
            if not enemy.alive or enemy.dying:
                continue
            if camera.is_visible(enemy.y, enemy.height):
                enemy.take_hit()
                # Force kill regardless of health
                enemy.health = 0
                enemy.dying = True
                enemy.death_timer = 0
                killed.append(enemy)
        return killed

    def draw(self, surface, camera, renderer):
        """Draw all visible enemies and their projectiles."""
        for enemy in self.enemies:
            if camera.is_visible(enemy.y, enemy.height, margin=50):
                enemy.draw(surface, camera, renderer)

    def load_from_level_data(self, level_data):
        """Load enemies from level JSON data."""
        self.enemies.clear()
        grid_size = level_data.get("grid_size", 32)

        for edata in level_data.get("enemies", []):
            etype = edata.get("type", "slug")
            x = edata.get("x", 0) * grid_size
            y = edata.get("y", 0) * grid_size
            kwargs = {k: v for k, v in edata.items() if k not in ("type", "x", "y")}
            enemy = create_enemy(etype, x, y, **kwargs)
            self.enemies.append(enemy)

        if self.enemies:
            self.highest_spawn_y = min(e.y for e in self.enemies)
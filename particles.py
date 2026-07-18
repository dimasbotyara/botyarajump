"""
botyarajump - Particle System
Handles particle effects and player trails.
"""

import pygame
import math
import random
import colorsys

from utils import create_surface_with_alpha, clamp, lerp
from settings import save_manager


class Particle:
    """A single particle."""

    def __init__(self, x, y, vx=0, vy=0, size=3, color=(255, 255, 255),
                 lifetime=1.0, gravity=0, shrink=True, fade=True,
                 shape="circle"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.max_size = size
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.shrink = shrink
        self.fade = fade
        self.shape = shape  # "circle", "square", "star", "line"
        self.alive = True
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-180, 180)

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += self.gravity * dt * 60
        self.lifetime -= dt
        self.rotation += self.rotation_speed * dt

        if self.lifetime <= 0:
            self.alive = False
            return

        progress = 1 - (self.lifetime / self.max_lifetime)

        if self.shrink:
            self.size = self.max_size * (1 - progress)

    def draw(self, surface, camera=None):
        if not self.alive or self.size < 0.5:
            return

        if camera:
            sx, sy = camera.world_to_screen(self.x, self.y)
        else:
            sx, sy = self.x, self.y

        sx, sy = int(sx), int(sy)
        size = max(1, int(self.size))

        # Alpha
        alpha = 255
        if self.fade:
            progress = 1 - (self.lifetime / self.max_lifetime)
            alpha = int(255 * (1 - progress))

        if alpha <= 0:
            return

        if self.shape == "circle":
            if alpha < 255:
                temp = create_surface_with_alpha(size * 2 + 2, size * 2 + 2)
                pygame.draw.circle(temp, (*self.color[:3], alpha),
                                   (size + 1, size + 1), size)
                surface.blit(temp, (sx - size - 1, sy - size - 1))
            else:
                pygame.draw.circle(surface, self.color, (sx, sy), size)

        elif self.shape == "square":
            if alpha < 255:
                temp = create_surface_with_alpha(size * 2, size * 2)
                # Rotated square
                rect = pygame.Rect(0, 0, size * 2, size * 2)
                pygame.draw.rect(temp, (*self.color[:3], alpha), rect)
                rotated = pygame.transform.rotate(temp, self.rotation)
                r = rotated.get_rect(center=(sx, sy))
                surface.blit(rotated, r.topleft)
            else:
                pygame.draw.rect(surface, self.color,
                                 (sx - size, sy - size, size * 2, size * 2))

        elif self.shape == "star":
            if alpha < 255:
                s = size * 3
                temp = create_surface_with_alpha(s, s)
                cx, cy_local = s // 2, s // 2
                points = []
                for i in range(10):
                    angle = math.radians(self.rotation) + i * math.pi / 5
                    r = size if i % 2 == 0 else size // 2
                    points.append((
                        int(cx + math.cos(angle) * r),
                        int(cy_local + math.sin(angle) * r)
                    ))
                if len(points) >= 3:
                    pygame.draw.polygon(temp, (*self.color[:3], alpha), points)
                surface.blit(temp, (sx - s // 2, sy - s // 2))
            else:
                points = []
                for i in range(10):
                    angle = math.radians(self.rotation) + i * math.pi / 5
                    r = size if i % 2 == 0 else size // 2
                    points.append((
                        int(sx + math.cos(angle) * r),
                        int(sy + math.sin(angle) * r)
                    ))
                if len(points) >= 3:
                    pygame.draw.polygon(surface, self.color, points)

        elif self.shape == "line":
            end_x = sx + int(math.cos(math.radians(self.rotation)) * size * 2)
            end_y = sy + int(math.sin(math.radians(self.rotation)) * size * 2)
            if alpha < 255:
                temp = create_surface_with_alpha(abs(end_x - sx) + 4, abs(end_y - sy) + 4)
                ox = min(sx, end_x)
                oy = min(sy, end_y)
                pygame.draw.line(temp, (*self.color[:3], alpha),
                                 (sx - ox + 2, sy - oy + 2),
                                 (end_x - ox + 2, end_y - oy + 2),
                                 max(1, size // 2))
                surface.blit(temp, (ox - 2, oy - 2))
            else:
                pygame.draw.line(surface, self.color,
                                 (sx, sy), (end_x, end_y), max(1, size // 2))


class ParticleSystem:
    """Manages all particles in the game."""

    def __init__(self):
        self.particles = []
        self.max_particles = 500

        # Trail system
        self._trail_timer = 0
        self._trail_interval = 0.03  # Seconds between trail particles

    def reset(self):
        """Clear all particles."""
        self.particles.clear()
        self._trail_timer = 0

    def update(self, dt):
        """Update all particles."""
        for particle in self.particles:
            particle.update(dt)

        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]

        # Enforce particle limit
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]

    def add(self, particle):
        """Add a single particle."""
        self.particles.append(particle)

    def emit(self, x, y, count=10, **kwargs):
        """Emit multiple particles at a position."""
        for _ in range(count):
            vx = kwargs.get("vx", 0) + random.uniform(
                kwargs.get("vx_range", (-2, 2))[0],
                kwargs.get("vx_range", (-2, 2))[1]
            )
            vy = kwargs.get("vy", 0) + random.uniform(
                kwargs.get("vy_range", (-2, 2))[0],
                kwargs.get("vy_range", (-2, 2))[1]
            )
            size = kwargs.get("size", 3) + random.uniform(
                -kwargs.get("size_var", 1),
                kwargs.get("size_var", 1)
            )
            size = max(1, size)

            color = kwargs.get("color", (255, 255, 255))
            if kwargs.get("random_color", False):
                color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )

            lifetime = kwargs.get("lifetime", 1.0) + random.uniform(
                -kwargs.get("lifetime_var", 0.2),
                kwargs.get("lifetime_var", 0.2)
            )
            lifetime = max(0.1, lifetime)

            px = x + random.uniform(
                -kwargs.get("spread", 5),
                kwargs.get("spread", 5)
            )
            py = y + random.uniform(
                -kwargs.get("spread", 5),
                kwargs.get("spread", 5)
            )

            p = Particle(
                px, py, vx, vy,
                size=size,
                color=color,
                lifetime=lifetime,
                gravity=kwargs.get("gravity", 0),
                shrink=kwargs.get("shrink", True),
                fade=kwargs.get("fade", True),
                shape=kwargs.get("shape", "circle")
            )
            self.particles.append(p)

    # ==========================================
    # PRESET EFFECTS
    # ==========================================

    def emit_jump(self, x, y):
        """Emit particles when player jumps off platform."""
        self.emit(x, y, count=6,
                  vx_range=(-3, 3), vy_range=(-1, 1),
                  size=3, size_var=1,
                  color=(200, 255, 200),
                  lifetime=0.5, gravity=0.05,
                  shape="circle")

    def emit_super_jump(self, x, y):
        """Emit particles for spring/super jump."""
        self.emit(x, y, count=12,
                  vx_range=(-4, 4), vy_range=(0, 2),
                  size=4, size_var=2,
                  color=(255, 255, 100),
                  lifetime=0.7, gravity=0.03,
                  shape="star")

    def emit_enemy_death(self, x, y, color=(255, 100, 100)):
        """Emit particles when enemy dies."""
        self.emit(x, y, count=15,
                  vx_range=(-5, 5), vy_range=(-5, 2),
                  size=4, size_var=2,
                  color=color,
                  lifetime=0.8, gravity=0.1,
                  shape="circle")

        # Stars
        self.emit(x, y, count=5,
                  vx_range=(-3, 3), vy_range=(-4, -1),
                  size=5, size_var=1,
                  color=(255, 255, 100),
                  lifetime=0.6,
                  shape="star")

    def emit_coin_collect(self, x, y):
        """Emit particles when coin is collected."""
        self.emit(x, y, count=8,
                  vx_range=(-3, 3), vy_range=(-3, 0),
                  size=2, size_var=1,
                  color=(255, 215, 0),
                  lifetime=0.5, gravity=0.02,
                  shape="circle")

    def emit_powerup_collect(self, x, y, powerup_type="shield"):
        """Emit particles for powerup collection."""
        colors = {
            "spring": (255, 255, 100),
            "jetpack": (255, 150, 50),
            "blaster": (100, 100, 255),
            "shield": (100, 200, 255),
            "magnet": (255, 80, 80),
        }
        color = colors.get(powerup_type, (255, 255, 255))

        self.emit(x, y, count=20,
                  vx_range=(-4, 4), vy_range=(-4, 4),
                  size=4, size_var=2,
                  color=color,
                  lifetime=0.8, gravity=0,
                  shape="star")

    def emit_platform_break(self, x, y, width):
        """Emit particles when breakable platform breaks."""
        for i in range(8):
            px = x + random.uniform(0, width)
            self.add(Particle(
                px, y,
                vx=random.uniform(-2, 2),
                vy=random.uniform(1, 4),
                size=random.uniform(2, 4),
                color=(160, 100, 60),
                lifetime=random.uniform(0.4, 0.8),
                gravity=0.15,
                shape="square"
            ))

    def emit_bomb(self, x, y, radius=150):
        """Emit particles for bomb booster effect."""
        # Shockwave ring
        for i in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 8)
            self.add(Particle(
                x, y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                size=random.uniform(3, 6),
                color=(255, random.randint(100, 200), 0),
                lifetime=random.uniform(0.5, 1.0),
                gravity=0,
                shape="circle"
            ))

        # Center flash
        self.emit(x, y, count=15,
                  vx_range=(-6, 6), vy_range=(-6, 6),
                  size=6, size_var=3,
                  color=(255, 255, 200),
                  lifetime=0.4,
                  shape="star")

    def emit_death(self, x, y):
        """Emit particles when player dies."""
        self.emit(x, y, count=25,
                  vx_range=(-5, 5), vy_range=(-5, 5),
                  size=4, size_var=2,
                  random_color=True,
                  lifetime=1.0, gravity=0.05,
                  shape="circle")

    def emit_shield_break(self, x, y):
        """Emit particles when shield absorbs hit."""
        for i in range(16):
            angle = i * math.pi * 2 / 16
            self.add(Particle(
                x + math.cos(angle) * 20,
                y + math.sin(angle) * 20,
                vx=math.cos(angle) * 3,
                vy=math.sin(angle) * 3,
                size=3,
                color=(100, 200, 255),
                lifetime=0.5,
                shape="line"
            ))

    # ==========================================
    # TRAIL SYSTEM
    # ==========================================

    def update_trail(self, dt, player_x, player_y, trail_type="none"):
        """Update player trail particles."""
        if trail_type == "none" or trail_type == "":
            return

        self._trail_timer += dt
        if self._trail_timer < self._trail_interval:
            return

        self._trail_timer = 0

        cx = player_x
        cy = player_y

        if trail_type == "fire":
            self._trail_fire(cx, cy)
        elif trail_type == "stars":
            self._trail_stars(cx, cy)
        elif trail_type == "rainbow":
            self._trail_rainbow(cx, cy)
        elif trail_type == "bubbles":
            self._trail_bubbles(cx, cy)
        elif trail_type == "snow":
            self._trail_snow(cx, cy)
        elif trail_type == "hearts":
            self._trail_hearts(cx, cy)
        elif trail_type == "lightning":
            self._trail_lightning(cx, cy)

    def _trail_fire(self, x, y):
        for _ in range(2):
            self.add(Particle(
                x + random.uniform(-8, 8), y + random.uniform(5, 15),
                vx=random.uniform(-0.5, 0.5),
                vy=random.uniform(0.5, 2),
                size=random.uniform(3, 6),
                color=random.choice([
                    (255, 200, 50), (255, 150, 30), (255, 80, 20), (255, 50, 10)
                ]),
                lifetime=random.uniform(0.3, 0.6),
                gravity=-0.02,
                shape="circle"
            ))

    def _trail_stars(self, x, y):
        self.add(Particle(
            x + random.uniform(-10, 10), y + random.uniform(0, 15),
            vx=random.uniform(-1, 1),
            vy=random.uniform(0, 1),
            size=random.uniform(2, 5),
            color=(255, 255, random.randint(150, 255)),
            lifetime=random.uniform(0.4, 0.8),
            shape="star"
        ))

    def _trail_rainbow(self, x, y):
        hue = (pygame.time.get_ticks() / 10) % 360
        r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.9, 1.0)
        color = (int(r * 255), int(g * 255), int(b * 255))
        self.add(Particle(
            x + random.uniform(-6, 6), y + random.uniform(5, 15),
            vx=random.uniform(-0.3, 0.3),
            vy=random.uniform(0.5, 1.5),
            size=random.uniform(3, 5),
            color=color,
            lifetime=random.uniform(0.4, 0.7),
            shape="circle"
        ))

    def _trail_bubbles(self, x, y):
        if random.random() < 0.5:
            self.add(Particle(
                x + random.uniform(-8, 8), y + random.uniform(5, 15),
                vx=random.uniform(-0.5, 0.5),
                vy=random.uniform(-0.5, 0.5),
                size=random.uniform(3, 7),
                color=(200, 230, 255),
                lifetime=random.uniform(0.6, 1.2),
                shrink=False,
                shape="circle"
            ))

    def _trail_snow(self, x, y):
        if random.random() < 0.6:
            self.add(Particle(
                x + random.uniform(-10, 10), y + random.uniform(0, 10),
                vx=random.uniform(-1, 1),
                vy=random.uniform(0.5, 1.5),
                size=random.uniform(2, 4),
                color=(220, 230, 255),
                lifetime=random.uniform(0.5, 1.0),
                gravity=0.01,
                shape="circle"
            ))

    def _trail_hearts(self, x, y):
        if random.random() < 0.4:
            self.add(Particle(
                x + random.uniform(-8, 8), y + random.uniform(5, 15),
                vx=random.uniform(-0.5, 0.5),
                vy=random.uniform(0.3, 1.0),
                size=random.uniform(3, 5),
                color=random.choice([
                    (255, 100, 120), (255, 50, 80), (255, 150, 170)
                ]),
                lifetime=random.uniform(0.5, 0.9),
                shape="circle"  # Simplified - could do heart shape
            ))

    def _trail_lightning(self, x, y):
        if random.random() < 0.3:
            self.add(Particle(
                x + random.uniform(-5, 5), y + random.uniform(5, 12),
                vx=random.uniform(-2, 2),
                vy=random.uniform(0, 2),
                size=random.uniform(4, 8),
                color=(150, 200, 255),
                lifetime=random.uniform(0.1, 0.3),
                shape="line"
            ))

    def draw(self, surface, camera=None):
        """Draw all particles."""
        for particle in self.particles:
            particle.draw(surface, camera)

    def get_count(self):
        """Get current particle count."""
        return len(self.particles)
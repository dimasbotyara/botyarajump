"""
botyarajump - Platforms
All platform types with physics and rendering.
"""

import pygame
import math
import random

from settings import PLATFORM_WIDTH, PLATFORM_HEIGHT, save_manager
from utils import clamp


class Platform:
    """Base platform class."""

    NORMAL = "normal"
    MOVING = "moving"
    BREAKABLE = "breakable"
    DISAPPEARING = "disappearing"
    SPRING = "spring"

    def __init__(self, x, y, width=None, height=None, platform_type=None):
        self.x = x
        self.y = y
        self.width = width or PLATFORM_WIDTH
        self.height = height or PLATFORM_HEIGHT
        self.platform_type = platform_type or self.NORMAL
        self.alive = True
        self.active = True  # Can be landed on
        self.landed_on = False  # Has player landed on it this life

    def update(self, dt):
        """Update platform state. Override in subclasses."""
        pass

    def on_land(self, player):
        """Called when player lands on this platform. Returns jump velocity or None."""
        if not self.active:
            return None
        self.landed_on = True
        player.session_platforms += 1
        save_manager.add_stat("total_platforms_landed")
        return None  # Subclasses return actual velocity

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_top_rect(self):
        """Get top surface rectangle for landing detection."""
        return pygame.Rect(self.x, self.y, self.width, 5)

    def draw(self, surface, camera, renderer):
        """Draw the platform."""
        if not self.alive:
            return
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        theme = save_manager.equipped.get("theme", "day")
        self._draw_specific(surface, int(screen_x), int(screen_y), renderer, theme)

    def _draw_specific(self, surface, x, y, renderer, theme):
        """Override to draw specific platform type."""
        renderer.draw_platform_normal(surface, x, y, self.width, self.height, theme)


class NormalPlatform(Platform):
    """Standard green platform."""

    def __init__(self, x, y, width=None, height=None):
        super().__init__(x, y, width, height, Platform.NORMAL)

    def on_land(self, player):
        super().on_land(player)
        return player.jump()

    def _draw_specific(self, surface, x, y, renderer, theme):
        renderer.draw_platform_normal(surface, x, y, self.width, self.height, theme)


class MovingPlatform(Platform):
    """Blue platform that moves horizontally."""

    def __init__(self, x, y, width=None, height=None,
                 move_range=100, speed=2, screen_width=480):
        super().__init__(x, y, width, height, Platform.MOVING)
        self.start_x = x
        self.move_range = move_range
        self.speed = speed
        self.direction = 1
        self.screen_width = screen_width
        self.move_timer = random.uniform(0, math.pi * 2)  # Random phase

    def update(self, dt):
        """Move platform side to side."""
        self.move_timer += self.speed * dt
        self.x = self.start_x + math.sin(self.move_timer) * self.move_range / 2

        # Keep on screen
        if self.x < 0:
            self.x = 0
            self.direction = 1
        elif self.x + self.width > self.screen_width:
            self.x = self.screen_width - self.width
            self.direction = -1

    def on_land(self, player):
        super().on_land(player)
        save_manager.add_stat("total_platforms_landed")
        return player.jump()

    def _draw_specific(self, surface, x, y, renderer, theme):
        renderer.draw_platform_moving(surface, x, y, self.width, self.height, theme)


class BreakablePlatform(Platform):
    """Brown platform that breaks when landed on."""

    def __init__(self, x, y, width=None, height=None):
        super().__init__(x, y, width, height, Platform.BREAKABLE)
        self.crack_level = 0
        self.breaking = False
        self.break_timer = 0
        self.break_duration = 0.5  # seconds for break animation
        self.has_been_jumped_on = False

    def update(self, dt):
        """Update breaking animation."""
        if self.breaking:
            self.break_timer += dt
            if self.break_timer >= self.break_duration:
                self.alive = False
                self.active = False

    def on_land(self, player):
        """Break on landing - player still gets the jump but platform starts breaking."""
        if not self.active:
            return None

        super().on_land(player)

        if not self.has_been_jumped_on:
            self.has_been_jumped_on = True
            self.crack_level = 1
            # Player gets a jump
            player.jump()
            # Start breaking
            self.breaking = True
            self.crack_level = 2
            save_manager.add_stat("total_breakable_broken")
            return None

        return None

    def _draw_specific(self, surface, x, y, renderer, theme):
        if self.breaking:
            progress = clamp(self.break_timer / self.break_duration, 0, 1)
            renderer.draw_platform_breaking_pieces(
                surface, x, y, self.width, self.height, progress, theme
            )
        else:
            renderer.draw_platform_breakable(
                surface, x, y, self.width, self.height, theme, self.crack_level
            )


class DisappearingPlatform(Platform):
    """White platform that fades and disappears after being landed on."""

    def __init__(self, x, y, width=None, height=None, fade_time=2.0):
        super().__init__(x, y, width, height, Platform.DISAPPEARING)
        self.fade_time = fade_time
        self.fade_timer = 0
        self.fading = False
        self.fade_progress = 0.0

    def update(self, dt):
        """Update fade animation."""
        if self.fading:
            self.fade_timer += dt
            self.fade_progress = clamp(self.fade_timer / self.fade_time, 0, 1)

            if self.fade_progress >= 0.7:
                self.active = False  # Can't land on it anymore

            if self.fade_progress >= 1.0:
                self.alive = False

    def on_land(self, player):
        """Start fading when first landed on."""
        if not self.active:
            return None

        super().on_land(player)

        if not self.fading:
            self.fading = True

        return player.jump()

    def _draw_specific(self, surface, x, y, renderer, theme):
        renderer.draw_platform_disappearing(
            surface, x, y, self.width, self.height, theme, self.fade_progress
        )


class SpringPlatform(Platform):
    """Platform with a spring that gives a super jump."""

    def __init__(self, x, y, width=None, height=None):
        super().__init__(x, y, width, height, Platform.SPRING)
        self.spring_compressed = False
        self.spring_timer = 0
        self.spring_anim_duration = 0.3

    def update(self, dt):
        """Update spring animation."""
        if self.spring_compressed:
            self.spring_timer += dt
            if self.spring_timer >= self.spring_anim_duration:
                self.spring_compressed = False
                self.spring_timer = 0

    def on_land(self, player):
        """Super jump from spring."""
        if not self.active:
            return None

        super().on_land(player)

        self.spring_compressed = True
        self.spring_timer = 0
        player.apply_spring()
        return None

    def _draw_specific(self, surface, x, y, renderer, theme):
        renderer.draw_platform_spring(
            surface, x, y, self.width, self.height, theme, self.spring_compressed
        )


class PlatformManager:
    """Manages platform generation and lifecycle."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.platforms = []
        self.highest_platform_y = screen_height

        # Player physics constraints for reachability
        # Max jump height ≈ v² / (2 * g) where v=12, g=0.5 → ~144 pixels
        # With horizontal speed 6 → max horizontal reach ~120 pixels
        self.max_jump_height = 120  # Conservative estimate (less than physics max)
        self.max_horizontal_reach = 160  # Max horizontal distance player can cover in one jump
        self.min_vertical_gap = 35  # Minimum gap so platforms don't overlap

        # Track last placed platform for reachability
        self._last_platform_x = screen_width // 2
        self._last_platform_y = screen_height

        # Generation parameters (modified by difficulty)
        self._update_difficulty()

    def _update_difficulty(self):
        """Update generation parameters from difficulty settings."""
        diff = save_manager.get_difficulty_settings()
        self.breakable_chance = diff["breakable_chance"]
        self.disappearing_chance = diff["disappearing_chance"]
        self.moving_chance = diff["moving_chance"]
        self.spring_chance = diff["spring_chance"]
        self.platform_gap_mult = diff["platform_gap_mult"]

    def reset(self):
        """Reset for new game."""
        self.platforms.clear()
        self.highest_platform_y = self.screen_height
        self._last_platform_x = self.screen_width // 2
        self._last_platform_y = self.screen_height
        self._update_difficulty()
        self._generate_initial_platforms()

    def _generate_initial_platforms(self):
        """Generate starting platforms."""
        # Starting platform (always normal, centered)
        start_x = self.screen_width // 2 - PLATFORM_WIDTH // 2
        start_platform = NormalPlatform(start_x, self.screen_height - 50)
        self.platforms.append(start_platform)

        self._last_platform_x = start_x
        self._last_platform_y = self.screen_height - 50

        # Generate platforms going up
        y = self.screen_height - 120
        while y > -200:
            platform = self._create_reachable_platform(y)
            self.platforms.append(platform)
            self._last_platform_x = platform.x
            self._last_platform_y = platform.y
            gap = self._get_platform_gap(y)
            y -= gap

        self.highest_platform_y = y

    def _get_platform_gap(self, current_y):
        """Get vertical gap between platforms. Increases with height."""
        base_gap = 55

        # Increase gap as player goes higher (but cap it)
        height_factor = max(0, (self.screen_height - current_y) / 8000)
        max_extra = 35
        extra = min(max_extra, height_factor * max_extra)

        gap = base_gap + extra
        gap *= self.platform_gap_mult

        # Add some randomness but keep it reasonable
        gap += random.uniform(-8, 12)

        # SAFETY: Never exceed max jump height
        max_safe_gap = self.max_jump_height - 10
        gap = min(gap, max_safe_gap)

        return max(self.min_vertical_gap, gap)

    def _get_reachable_x_range(self, from_x, from_y, to_y):
        """Calculate the X range that is reachable from a given platform.

        Args:
            from_x: X position of the source platform
            from_y: Y position of the source platform
            to_y: Y position of the target platform

        Returns:
            (min_x, max_x) tuple of valid X positions
        """
        vertical_dist = abs(from_y - to_y)

        # The further up we need to jump, the less horizontal distance we can cover
        # Rough approximation based on parabolic trajectory
        if vertical_dist <= 0:
            horizontal_range = self.max_horizontal_reach
        else:
            # As vertical distance increases, horizontal reach decreases
            height_ratio = vertical_dist / self.max_jump_height
            height_ratio = min(height_ratio, 0.95)  # Don't let it go to 0
            horizontal_range = self.max_horizontal_reach * (1 - height_ratio * 0.5)

        horizontal_range = max(PLATFORM_WIDTH * 2, horizontal_range)

        # Calculate range centered on source platform center
        from_center = from_x + PLATFORM_WIDTH // 2

        min_x = from_center - horizontal_range - PLATFORM_WIDTH // 2
        max_x = from_center + horizontal_range - PLATFORM_WIDTH // 2

        # Account for screen wrapping!
        # Player can wrap around screen, so positions near edges are always reachable
        # But let's keep platforms on screen for clarity
        min_x = max(5, min_x)
        max_x = min(self.screen_width - PLATFORM_WIDTH - 5, max_x)

        # If wrapping makes the other side reachable too
        # (player near left edge can reach right side by wrapping)
        if from_center < horizontal_range:
            # Can wrap from left, so right side is also reachable
            max_x = self.screen_width - PLATFORM_WIDTH - 5
        if from_center > self.screen_width - horizontal_range:
            # Can wrap from right, so left side is also reachable
            min_x = 5

        # Safety: ensure valid range
        if min_x >= max_x:
            min_x = max(5, from_center - PLATFORM_WIDTH * 3)
            max_x = min(self.screen_width - PLATFORM_WIDTH - 5,
                        from_center + PLATFORM_WIDTH * 3)

        if min_x >= max_x:
            min_x = 5
            max_x = self.screen_width - PLATFORM_WIDTH - 5

        return int(min_x), int(max_x)

    def _create_reachable_platform(self, y, force_type=None):
        """Create a platform at y that is guaranteed reachable from the last platform."""
        min_x, max_x = self._get_reachable_x_range(
            self._last_platform_x, self._last_platform_y, y
        )

        x = random.randint(min_x, max_x)

        # Determine type
        if force_type:
            return self._create_platform_of_type(x, y, force_type)

        platform = self._choose_platform_type(x, y)

        # SAFETY: If this is an unreliable platform, spawn a safe neighbor
        if isinstance(platform, (BreakablePlatform, DisappearingPlatform)):
            # Don't place two unreliable platforms in a row
            if self._last_was_unreliable():
                platform = NormalPlatform(x, y)
            else:
                # Spawn a backup safe platform nearby
                self._ensure_safe_neighbor(platform)

        return platform

    def _ensure_safe_neighbor(self, unsafe_platform):
        """Place a safe normal platform near an unsafe one,
        so the player always has an alternative path.

        The safe platform is placed at a similar height but
        different X position, ensuring both are reachable
        from the platform below.
        """
        # Find a valid X position that's different from the unsafe platform
        # but still reachable from the last safe platform
        min_x, max_x = self._get_reachable_x_range(
            self._last_platform_x, self._last_platform_y, unsafe_platform.y
        )

        # Try to place on the opposite side of the screen from the unsafe platform
        unsafe_center = unsafe_platform.x + PLATFORM_WIDTH // 2
        screen_center = self.screen_width // 2

        if unsafe_center < screen_center:
            # Unsafe is on left, try to place safe on right
            preferred_x = min(max_x, unsafe_platform.x + PLATFORM_WIDTH + 40)
        else:
            # Unsafe is on right, try to place safe on left
            preferred_x = max(min_x, unsafe_platform.x - PLATFORM_WIDTH - 40)

        # Clamp to valid range
        safe_x = max(min_x, min(max_x, preferred_x))

        # Make sure it's not overlapping with the unsafe platform
        if abs(safe_x - unsafe_platform.x) < PLATFORM_WIDTH + 10:
            # Try the other side
            if safe_x <= unsafe_platform.x:
                safe_x = min(max_x, unsafe_platform.x + PLATFORM_WIDTH + 30)
            else:
                safe_x = max(min_x, unsafe_platform.x - PLATFORM_WIDTH - 30)

        # Small vertical offset so they're not at exact same height
        y_offset = random.randint(-15, 15)
        safe_y = unsafe_platform.y + y_offset

        safe_platform = NormalPlatform(int(safe_x), int(safe_y))
        self.platforms.append(safe_platform)

    def _last_was_unreliable(self):
        """Check if the last placed platform was breakable/disappearing."""
        if not self.platforms:
            return False
        last = self.platforms[-1]
        return isinstance(last, (BreakablePlatform, DisappearingPlatform))

    def _choose_platform_type(self, x, y):
        """Choose a random platform type based on difficulty settings."""
        roll = random.random()
        cumulative = 0

        cumulative += self.spring_chance
        if roll < cumulative:
            return SpringPlatform(x, y)

        cumulative += self.moving_chance
        if roll < cumulative:
            # Moving platform: make sure move range doesn't go off screen
            max_range = min(150, x * 2, (self.screen_width - x - PLATFORM_WIDTH) * 2)
            move_range = max(40, min(max_range, random.randint(60, 150)))
            return MovingPlatform(x, y, move_range=move_range,
                                  speed=random.uniform(1.5, 3.0),
                                  screen_width=self.screen_width)

        cumulative += self.breakable_chance
        if roll < cumulative:
            return BreakablePlatform(x, y)

        cumulative += self.disappearing_chance
        if roll < cumulative:
            fade_time = random.uniform(1.5, 3.0)
            return DisappearingPlatform(x, y, fade_time=fade_time)

        # Default: normal platform
        return NormalPlatform(x, y)

    def _create_platform_of_type(self, x, y, platform_type):
        """Create a specific type of platform."""
        if platform_type == Platform.NORMAL:
            return NormalPlatform(x, y)
        elif platform_type == Platform.MOVING:
            max_range = min(150, x * 2, (self.screen_width - x - PLATFORM_WIDTH) * 2)
            move_range = max(40, min(max_range, random.randint(60, 150)))
            return MovingPlatform(x, y, move_range=move_range,
                                  speed=random.uniform(1.5, 3.0),
                                  screen_width=self.screen_width)
        elif platform_type == Platform.BREAKABLE:
            return BreakablePlatform(x, y)
        elif platform_type == Platform.DISAPPEARING:
            return DisappearingPlatform(x, y, fade_time=random.uniform(1.5, 3.0))
        elif platform_type == Platform.SPRING:
            return SpringPlatform(x, y)
        else:
            return NormalPlatform(x, y)

    def _create_random_platform(self, y, force_type=None):
        """Create a random platform at given y position. (Legacy, now uses reachable)"""
        return self._create_reachable_platform(y, force_type)

    def update(self, dt, camera):
        """Update all platforms and generate new ones."""
        # Update existing platforms
        for platform in self.platforms:
            if platform.alive:
                platform.update(dt)

        # Remove dead/off-screen platforms
        visible_top, visible_bottom = camera.get_visible_range(margin=200)
        self.platforms = [
            p for p in self.platforms
            if p.alive and p.y < visible_bottom
        ]

        # Generate new platforms above
        while self.highest_platform_y > visible_top - 300:
            gap = self._get_platform_gap(self.highest_platform_y)
            new_y = self.highest_platform_y - gap
            new_platform = self._create_reachable_platform(new_y)
            self.platforms.append(new_platform)

            # Update tracking
            self._last_platform_x = new_platform.x
            self._last_platform_y = new_platform.y
            self.highest_platform_y = new_y

            # SAFETY: Every 5th platform, force a normal wide platform
            # to give player a "rest point"
            platform_count = len([p for p in self.platforms if p.alive])
            if platform_count % 8 == 0:
                safety_gap = self.min_vertical_gap + 10
                safety_y = new_y - safety_gap
                safety_x_min, safety_x_max = self._get_reachable_x_range(
                    new_platform.x, new_platform.y, safety_y
                )
                safety_x = (safety_x_min + safety_x_max) // 2
                safety_platform = NormalPlatform(safety_x, safety_y)
                self.platforms.append(safety_platform)
                self._last_platform_x = safety_x
                self._last_platform_y = safety_y
                self.highest_platform_y = safety_y

    def check_collision(self, player):
        """Check if player is landing on any platform.
        Only triggers when player is falling (vy > 0).
        """
        if not player.is_falling():
            return None

        feet_rect = player.get_feet_rect()
        prev_bottom = feet_rect.bottom - player.vy  # Approximate previous position

        for platform in self.platforms:
            if not platform.alive or not platform.active:
                continue

            plat_rect = platform.get_rect()
            top_rect = platform.get_top_rect()

            # Check if feet overlap with platform top
            if feet_rect.colliderect(top_rect):
                # Make sure player is coming from above
                if prev_bottom <= plat_rect.top + 10:
                    # Land on platform
                    player.y = plat_rect.top - player.height
                    player.on_platform = True
                    platform.on_land(player)
                    return platform

        return None

    def draw(self, surface, camera, renderer):
        """Draw all visible platforms."""
        for platform in self.platforms:
            if platform.alive and camera.is_visible(platform.y, platform.height):
                platform.draw(surface, camera, renderer)

    def get_platforms_near(self, y, margin=200):
        """Get platforms near a Y coordinate."""
        return [p for p in self.platforms
                if p.alive and abs(p.y - y) < margin]

    def load_from_level_data(self, level_data):
        """Load platforms from level JSON data."""
        self.platforms.clear()
        grid_size = level_data.get("grid_size", 32)

        for pdata in level_data.get("platforms", []):
            x = pdata.get("x", 0) * grid_size
            y = pdata.get("y", 0) * grid_size
            ptype = pdata.get("type", "normal")
            width = pdata.get("width", 2) * grid_size

            if ptype == "normal":
                p = NormalPlatform(x, y, width=width)
            elif ptype == "moving":
                move_range = pdata.get("range", 4) * grid_size
                speed = pdata.get("speed", 2)
                p = MovingPlatform(x, y, width=width, move_range=move_range,
                                   speed=speed, screen_width=self.screen_width)
            elif ptype == "breakable":
                p = BreakablePlatform(x, y, width=width)
            elif ptype == "disappearing":
                fade_time = pdata.get("fade_time", 2.0)
                p = DisappearingPlatform(x, y, width=width, fade_time=fade_time)
            elif ptype == "spring":
                p = SpringPlatform(x, y, width=width)
            else:
                p = NormalPlatform(x, y, width=width)

            self.platforms.append(p)

        # Set highest platform Y and last platform tracking
        if self.platforms:
            self.highest_platform_y = min(p.y for p in self.platforms)
            highest = min(self.platforms, key=lambda p: p.y)
            self._last_platform_x = highest.x
            self._last_platform_y = highest.y
        else:
            self.highest_platform_y = self.screen_height
"""
botyarajump - Camera System
Handles vertical scrolling and screen coordinate translation.
"""

from utils import lerp, ease_out


class Camera:
    """
    Camera that follows the player vertically.
    The camera only scrolls upward (the player can't scroll back down).
    Provides methods to convert between world and screen coordinates.
    """

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Camera Y offset in world coordinates
        # Positive = camera has moved up
        self.y_offset = 0

        # Target y for smooth following
        self._target_y = 0

        # The threshold - player must be above this screen Y to trigger scroll
        self.scroll_threshold = screen_height * 0.4  # Top 40% of screen

        # Smoothing factor (higher = more responsive)
        self.smooth_speed = 0.1

        # Shake effect
        self._shake_amount = 0
        self._shake_timer = 0
        self._shake_duration = 0.3
        self._shake_offset_x = 0
        self._shake_offset_y = 0

        # Highest point reached (for score)
        self.highest_y = 0

        # Death line - Y position below which player dies
        # In world coordinates
        self.death_line_world_y = screen_height

    def reset(self):
        """Reset camera for new game."""
        self.y_offset = 0
        self._target_y = 0
        self.highest_y = 0
        self._shake_amount = 0
        self._shake_timer = 0
        self._shake_duration = 0.3
        self._shake_offset_x = 0
        self._shake_offset_y = 0
        self.death_line_world_y = self.screen_height

    def update(self, player_world_y, dt):
        """
        Update camera position based on player position.

        Args:
            player_world_y: Player's Y position in world coordinates (lower = higher up)
            dt: Delta time in seconds
        """
        # Calculate where player is on screen
        player_screen_y = player_world_y - self.y_offset

        # If player is above scroll threshold, move camera up
        if player_screen_y < self.scroll_threshold:
            self._target_y = player_world_y - self.scroll_threshold

        # Smooth camera movement
        if self._target_y < self.y_offset:
            # Camera only moves up, never down
            self.y_offset = lerp(self.y_offset, self._target_y,
                                 self.smooth_speed * dt * 60)

            # Snap if very close
            if abs(self.y_offset - self._target_y) < 0.5:
                self.y_offset = self._target_y

        # Update death line (always at bottom of screen + margin)
        self.death_line_world_y = self.y_offset + self.screen_height + 50

        # Track highest point
        if player_world_y < self.highest_y or self.highest_y == 0:
            self.highest_y = player_world_y

        # Update shake
        self._update_shake(dt)

    def _update_shake(self, dt):
        """Update screen shake effect."""
        if self._shake_timer > 0:
            self._shake_timer -= dt
            progress = max(0.0, self._shake_timer / max(0.001, self._shake_duration))
            intensity = self._shake_amount * progress
            import random
            self._shake_offset_x = random.uniform(-intensity, intensity)
            self._shake_offset_y = random.uniform(-intensity, intensity)
        else:
            self._shake_offset_x = 0
            self._shake_offset_y = 0
            self._shake_amount = 0

    def shake(self, amount=5, duration=0.3):
        """Start screen shake effect."""
        self._shake_amount = amount
        self._shake_timer = duration
        self._shake_duration = duration

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates."""
        screen_x = world_x + self._shake_offset_x
        screen_y = world_y - self.y_offset + self._shake_offset_y
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates."""
        world_x = screen_x - self._shake_offset_x
        world_y = screen_y + self.y_offset - self._shake_offset_y
        return world_x, world_y

    def is_visible(self, world_y, height=0, margin=50):
        """Check if a world Y position is visible on screen."""
        screen_y = world_y - self.y_offset
        return -margin - height <= screen_y <= self.screen_height + margin

    def is_above_screen(self, world_y, margin=50):
        """Check if position is above the visible screen."""
        screen_y = world_y - self.y_offset
        return screen_y < -margin

    def is_below_death_line(self, world_y):
        """Check if position is below the death line."""
        return world_y > self.death_line_world_y

    def get_visible_range(self, margin=100):
        """Get the range of visible world Y coordinates.
        Returns (top_y, bottom_y) in world coordinates.
        """
        top_y = self.y_offset - margin
        bottom_y = self.y_offset + self.screen_height + margin
        return top_y, bottom_y

    def get_score_from_height(self):
        """Calculate score based on highest point reached."""
        # Starting Y is at screen_height (bottom), going up means lower Y
        # Score = how far up from starting position
        initial_y = self.screen_height
        height_climbed = initial_y - self.highest_y
        return max(0, int(height_climbed / 10))

    def set_position(self, y_offset):
        """Directly set camera position (for level editor, story mode)."""
        self.y_offset = y_offset
        self._target_y = y_offset

    def get_y_offset(self):
        """Get current camera Y offset."""
        return self.y_offset

    @property
    def shake_offset(self):
        """Get current shake offset as tuple."""
        return (self._shake_offset_x, self._shake_offset_y)
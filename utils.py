"""
botyarajump - Utility functions
Helper functions used across the project.
"""

import pygame
import math
import random
import os
import sys
import platform


def clamp(value, min_val, max_val):
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def lerp(a, b, t):
    """Linear interpolation between a and b."""
    return a + (b - a) * clamp(t, 0.0, 1.0)


def ease_out(t):
    """Ease out function."""
    return 1 - (1 - t) ** 3


def ease_in(t):
    """Ease in function."""
    return t ** 3


def ease_in_out(t):
    """Ease in-out function."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - (-2 * t + 2) ** 3 / 2


def distance(x1, y1, x2, y2):
    """Calculate distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def angle_between(x1, y1, x2, y2):
    """Calculate angle between two points in radians."""
    return math.atan2(y2 - y1, x2 - x1)


def random_color():
    """Generate a random color."""
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))


def darken_color(color, factor=0.7):
    """Darken a color by factor."""
    return tuple(int(c * factor) for c in color[:3])


def lighten_color(color, factor=1.3):
    """Lighten a color by factor."""
    return tuple(min(255, int(c * factor)) for c in color[:3])


def alpha_blend_color(color, alpha):
    """Return color with alpha (for Surface operations)."""
    if len(color) == 4:
        return (color[0], color[1], color[2], alpha)
    return (color[0], color[1], color[2], alpha)


def create_surface_with_alpha(width, height):
    """Create a surface that supports alpha."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    return surf


def draw_text_with_alpha(surface, text, font, color, x, y, alpha=255, anchor="topleft"):
    """Draw text with alpha transparency."""
    text_surf = font.render(text, True, color)
    if alpha < 255:
        alpha_surf = create_surface_with_alpha(text_surf.get_width(), text_surf.get_height())
        alpha_surf.blit(text_surf, (0, 0))
        alpha_surf.set_alpha(alpha)
        text_surf = alpha_surf

    rect = text_surf.get_rect()
    if anchor == "topleft":
        rect.topleft = (x, y)
    elif anchor == "center":
        rect.center = (x, y)
    elif anchor == "midtop":
        rect.midtop = (x, y)
    elif anchor == "midbottom":
        rect.midbottom = (x, y)
    elif anchor == "midleft":
        rect.midleft = (x, y)
    elif anchor == "midright":
        rect.midright = (x, y)
    elif anchor == "topright":
        rect.topright = (x, y)

    surface.blit(text_surf, rect)
    return rect


def draw_rounded_rect(surface, color, rect, radius=10, alpha=255):
    """Draw a rounded rectangle."""
    if alpha < 255:
        temp = create_surface_with_alpha(rect[2], rect[3])
        pygame.draw.rect(temp, (*color[:3], alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
        surface.blit(temp, (rect[0], rect[1]))
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_button(surface, text, font, rect, color, text_color=(255, 255, 255),
                hover=False, alpha=255, border_radius=12):
    """Draw a styled button."""
    x, y, w, h = rect

    # Background
    bg_color = lighten_color(color, 1.2) if hover else color
    draw_rounded_rect(surface, bg_color, rect, border_radius, alpha)

    # Border
    if hover:
        border_color = lighten_color(color, 1.5)
    else:
        border_color = darken_color(color, 0.7)

    if alpha < 255:
        temp = create_surface_with_alpha(w, h)
        pygame.draw.rect(temp, (*border_color[:3], alpha), (0, 0, w, h),
                         width=2, border_radius=border_radius)
        surface.blit(temp, (x, y))
    else:
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=border_radius)

    # Text
    draw_text_with_alpha(surface, text, font, text_color, x + w // 2, y + h // 2,
                         alpha, anchor="center")

    return pygame.Rect(rect)


def draw_slider(surface, x, y, width, height, value, min_val=0, max_val=1,
                bg_color=(80, 80, 80), fill_color=(100, 180, 255),
                handle_color=(255, 255, 255)):
    """Draw a slider widget. Returns the slider rect for interaction."""
    # Background
    bar_rect = pygame.Rect(x, y + height // 2 - 3, width, 6)
    pygame.draw.rect(surface, bg_color, bar_rect, border_radius=3)

    # Fill
    fill_width = int((value - min_val) / (max_val - min_val) * width)
    fill_rect = pygame.Rect(x, y + height // 2 - 3, fill_width, 6)
    pygame.draw.rect(surface, fill_color, fill_rect, border_radius=3)

    # Handle
    handle_x = x + fill_width
    handle_y = y + height // 2
    pygame.draw.circle(surface, handle_color, (handle_x, handle_y), 8)
    pygame.draw.circle(surface, darken_color(handle_color, 0.7), (handle_x, handle_y), 8, 2)

    return bar_rect


def draw_toggle(surface, x, y, width, height, value, on_color=(100, 200, 100),
                off_color=(150, 60, 60)):
    """Draw a toggle switch. Returns rect."""
    rect = pygame.Rect(x, y, width, height)
    color = on_color if value else off_color
    pygame.draw.rect(surface, darken_color(color, 0.6), rect, border_radius=height // 2)

    # Handle
    handle_radius = height // 2 - 2
    if value:
        handle_x = x + width - handle_radius - 4
    else:
        handle_x = x + handle_radius + 4
    handle_y = y + height // 2

    pygame.draw.circle(surface, (255, 255, 255), (handle_x, handle_y), handle_radius)

    return rect


def point_in_rect(point, rect):
    """Check if point is inside rect (x, y, w, h)."""
    if isinstance(rect, pygame.Rect):
        return rect.collidepoint(point)
    x, y, w, h = rect
    px, py = point
    return x <= px <= x + w and y <= py <= y + h


def get_key_name_from_event(event):
    """Get a string key name from a pygame key event."""
    return pygame.key.name(event.key)


def key_name_to_key(name):
    """Convert key name string like 'K_LEFT' or 'K_a' to pygame key constant."""
    if not name or name == "":
        return None

    try:
        # Direct attribute lookup: K_LEFT, K_a, K_SPACE, etc.
        if hasattr(pygame, name):
            return getattr(pygame, name)

        # Try uppercase: K_A -> K_a (pygame uses lowercase for letters)
        upper_name = name.upper()
        if hasattr(pygame, upper_name):
            return getattr(pygame, upper_name)

        lower_name = name.lower()
        if hasattr(pygame, lower_name):
            return getattr(pygame, lower_name)

        # Strip K_ prefix and use key_code
        if name.startswith("K_"):
            key_part = name[2:]

            # Try as pygame attribute with different cases
            for variant in [f"K_{key_part}", f"K_{key_part.lower()}", f"K_{key_part.upper()}"]:
                if hasattr(pygame, variant):
                    return getattr(pygame, variant)

            # Special arrow keys
            arrow_map = {
                "LEFT": pygame.K_LEFT,
                "RIGHT": pygame.K_RIGHT,
                "UP": pygame.K_UP,
                "DOWN": pygame.K_DOWN,
                "SPACE": pygame.K_SPACE,
                "RETURN": pygame.K_RETURN,
                "ESCAPE": pygame.K_ESCAPE,
                "TAB": pygame.K_TAB,
                "BACKSPACE": pygame.K_BACKSPACE,
                "LSHIFT": pygame.K_LSHIFT,
                "RSHIFT": pygame.K_RSHIFT,
                "LCTRL": pygame.K_LCTRL,
                "RCTRL": pygame.K_RCTRL,
                "LALT": pygame.K_LALT,
                "RALT": pygame.K_RALT,
            }

            upper_part = key_part.upper()
            if upper_part in arrow_map:
                return arrow_map[upper_part]

            # Single letter keys: K_a, K_b, etc.
            if len(key_part) == 1:
                try:
                    return pygame.key.key_code(key_part.lower())
                except ValueError:
                    pass

            # Try pygame.key.key_code with the raw name
            try:
                return pygame.key.key_code(key_part.lower())
            except ValueError:
                pass

        # Last resort: try key_code directly
        try:
            return pygame.key.key_code(name.lower())
        except ValueError:
            pass

    except (AttributeError, ValueError, TypeError):
        pass

    return None


def format_time(seconds):
    """Format seconds into human readable time."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def get_emoji_font_path():
    """Get path to emoji-capable font based on platform."""
    system = platform.system()

    if system == "Windows":
        # Segoe UI Emoji is available on Windows 10+
        candidates = [
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "seguiemj.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "segoeui.ttf"),
        ]
    elif system == "Linux":
        candidates = [
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/noto-cjk/NotoColorEmoji.ttf",
            "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
            "/usr/share/fonts/noto/NotoEmoji-Regular.ttf",
        ]
    elif system == "Darwin":  # macOS
        candidates = [
            "/System/Library/Fonts/Apple Color Emoji.ttc",
            "/System/Library/Fonts/AppleColorEmoji.ttf",
        ]
    else:
        candidates = []

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def get_system_font_path():
    """Get path to a good system font that supports Cyrillic."""
    system = platform.system()

    if system == "Windows":
        candidates = [
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "segoeui.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "tahoma.ttf"),
        ]
    elif system == "Linux":
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]
    elif system == "Darwin":
        candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf",
        ]
    else:
        candidates = []

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def open_folder(path):
    """Open folder in system file manager."""
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        import subprocess
        subprocess.Popen(["open", path])
    else:
        import subprocess
        subprocess.Popen(["xdg-open", path])


def copy_to_clipboard(text):
    """Copy text to system clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        try:
            # Fallback: try pygame scrap
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
            return True
        except Exception:
            return False


def paste_from_clipboard():
    """Paste text from system clipboard."""
    try:
        import pyperclip
        return pyperclip.paste()
    except ImportError:
        try:
            pygame.scrap.init()
            data = pygame.scrap.get(pygame.SCRAP_TEXT)
            if data:
                return data.decode('utf-8').rstrip('\x00')
        except Exception:
            pass
    return ""


# Color constants for themes
THEME_COLORS = {
    "day": {
        "bg_top": (135, 206, 235),
        "bg_bottom": (200, 230, 255),
        "platform_normal": (80, 200, 80),
        "platform_moving": (80, 150, 255),
        "platform_breakable": (160, 100, 60),
        "platform_disappearing": (200, 200, 200),
        "platform_spring": (220, 200, 50),
        "text_color": (40, 40, 40),
        "coin_color": (255, 215, 0),
        "stars": False
    },
    "night": {
        "bg_top": (10, 10, 40),
        "bg_bottom": (30, 30, 80),
        "platform_normal": (60, 160, 60),
        "platform_moving": (60, 120, 220),
        "platform_breakable": (130, 80, 40),
        "platform_disappearing": (150, 150, 150),
        "platform_spring": (200, 180, 30),
        "text_color": (220, 220, 220),
        "coin_color": (255, 215, 0),
        "stars": True
    },
    "sunset": {
        "bg_top": (255, 100, 50),
        "bg_bottom": (255, 180, 100),
        "platform_normal": (100, 180, 60),
        "platform_moving": (80, 130, 200),
        "platform_breakable": (140, 90, 50),
        "platform_disappearing": (180, 170, 150),
        "platform_spring": (230, 200, 40),
        "text_color": (60, 20, 10),
        "coin_color": (255, 230, 50),
        "stars": False
    },
    "space": {
        "bg_top": (5, 5, 20),
        "bg_bottom": (15, 10, 40),
        "platform_normal": (0, 200, 150),
        "platform_moving": (100, 50, 255),
        "platform_breakable": (100, 60, 30),
        "platform_disappearing": (120, 120, 140),
        "platform_spring": (200, 200, 0),
        "text_color": (200, 220, 255),
        "coin_color": (255, 215, 0),
        "stars": True
    },
    "forest": {
        "bg_top": (50, 120, 50),
        "bg_bottom": (80, 160, 80),
        "platform_normal": (60, 140, 40),
        "platform_moving": (70, 130, 180),
        "platform_breakable": (120, 80, 40),
        "platform_disappearing": (160, 180, 140),
        "platform_spring": (200, 180, 50),
        "text_color": (30, 50, 20),
        "coin_color": (255, 200, 0),
        "stars": False
    },
    "ocean": {
        "bg_top": (0, 80, 160),
        "bg_bottom": (0, 140, 200),
        "platform_normal": (0, 180, 120),
        "platform_moving": (0, 100, 200),
        "platform_breakable": (100, 80, 60),
        "platform_disappearing": (150, 200, 200),
        "platform_spring": (220, 200, 0),
        "text_color": (220, 240, 255),
        "coin_color": (255, 215, 0),
        "stars": False
    },
    "candy": {
        "bg_top": (255, 180, 220),
        "bg_bottom": (255, 220, 240),
        "platform_normal": (255, 100, 150),
        "platform_moving": (150, 100, 255),
        "platform_breakable": (200, 150, 100),
        "platform_disappearing": (255, 200, 200),
        "platform_spring": (255, 255, 100),
        "text_color": (100, 30, 60),
        "coin_color": (255, 200, 50),
        "stars": False
    },
    "lava": {
        "bg_top": (60, 10, 0),
        "bg_bottom": (120, 30, 0),
        "platform_normal": (180, 60, 20),
        "platform_moving": (200, 100, 30),
        "platform_breakable": (80, 40, 20),
        "platform_disappearing": (140, 80, 40),
        "platform_spring": (255, 200, 0),
        "text_color": (255, 200, 100),
        "coin_color": (255, 180, 0),
        "stars": False
    }
}

# Skin color palettes
SKIN_COLORS = {
    "default": {
        "body": (100, 200, 100),
        "eyes": (40, 40, 40),
        "nose": (80, 160, 80),
        "feet": (80, 160, 80),
        "outline": (60, 140, 60)
    },
    "red": {
        "body": (220, 60, 60),
        "eyes": (40, 40, 40),
        "nose": (180, 40, 40),
        "feet": (180, 40, 40),
        "outline": (160, 30, 30)
    },
    "blue": {
        "body": (60, 120, 220),
        "eyes": (40, 40, 40),
        "nose": (40, 90, 180),
        "feet": (40, 90, 180),
        "outline": (30, 70, 160)
    },
    "gold": {
        "body": (255, 215, 0),
        "eyes": (60, 40, 0),
        "nose": (220, 180, 0),
        "feet": (220, 180, 0),
        "outline": (200, 160, 0)
    },
    "neon": {
        "body": (0, 255, 150),
        "eyes": (255, 0, 100),
        "nose": (0, 200, 120),
        "feet": (0, 200, 120),
        "outline": (0, 180, 100)
    },
    "pixel": {
        "body": (150, 150, 150),
        "eyes": (0, 0, 0),
        "nose": (120, 120, 120),
        "feet": (100, 100, 100),
        "outline": (80, 80, 80)
    },
    "ghost": {
        "body": (220, 220, 240),
        "eyes": (20, 20, 60),
        "nose": (200, 200, 220),
        "feet": (180, 180, 200),
        "outline": (180, 180, 210)
    },
    "rainbow": {
        "body": (255, 100, 100),  # Changes dynamically
        "eyes": (40, 40, 40),
        "nose": (200, 80, 80),
        "feet": (200, 80, 80),
        "outline": (180, 60, 60)
    },
    "ninja": {
        "body": (40, 40, 40),
        "eyes": (255, 255, 255),
        "nose": (40, 40, 40),
        "feet": (30, 30, 30),
        "outline": (20, 20, 20)
    },
    "robot": {
        "body": (160, 170, 180),
        "eyes": (255, 50, 50),
        "nose": (140, 150, 160),
        "feet": (120, 130, 140),
        "outline": (100, 110, 120)
    }
}
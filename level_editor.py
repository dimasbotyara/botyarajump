"""
botyarajump - Level Editor
Grid-based level editor for creating custom levels.
"""

import pygame
import json
import os
import math

from settings import save_manager, CUSTOM_LEVELS_DIR, PLATFORM_WIDTH, PLATFORM_HEIGHT
from localization import get_text
from renderer import font_manager, sprite_renderer
from utils import (
    draw_rounded_rect, draw_button, create_surface_with_alpha,
    copy_to_clipboard, paste_from_clipboard, point_in_rect,
    darken_color, lighten_color, THEME_COLORS
)
from platforms import Platform
from enemies import Enemy


class EditorTool:
    """Editor tool types."""
    SELECT = "select"
    PLATFORM_NORMAL = "platform_normal"
    PLATFORM_MOVING = "platform_moving"
    PLATFORM_BREAKABLE = "platform_breakable"
    PLATFORM_DISAPPEARING = "platform_disappearing"
    PLATFORM_SPRING = "platform_spring"
    ENEMY_SLUG = "enemy_slug"
    ENEMY_BAT = "enemy_bat"
    ENEMY_BLACK_HOLE = "enemy_black_hole"
    ENEMY_GHOST = "enemy_ghost"
    ENEMY_RED_BALL = "enemy_red_ball"
    ENEMY_SNAKE = "enemy_snake"
    ENEMY_EVIL_CLOUD = "enemy_evil_cloud"
    ENEMY_UFO = "enemy_ufo"
    COIN = "coin"
    POWERUP_JETPACK = "powerup_jetpack"
    POWERUP_BLASTER = "powerup_blaster"
    POWERUP_SHIELD = "powerup_shield"
    POWERUP_MAGNET = "powerup_magnet"
    START = "start"
    FINISH = "finish"
    ERASER = "eraser"


# Tool categories for toolbar
TOOL_CATEGORIES = [
    ("Platforms", [
        (EditorTool.PLATFORM_NORMAL, "Normal", (80, 200, 80)),
        (EditorTool.PLATFORM_MOVING, "Moving", (80, 150, 255)),
        (EditorTool.PLATFORM_BREAKABLE, "Break", (160, 100, 60)),
        (EditorTool.PLATFORM_DISAPPEARING, "Vanish", (200, 200, 200)),
        (EditorTool.PLATFORM_SPRING, "Spring", (220, 200, 50)),
    ]),
    ("Enemies", [
        (EditorTool.ENEMY_SLUG, "Slug", (120, 180, 50)),
        (EditorTool.ENEMY_BAT, "Bat", (80, 40, 100)),
        (EditorTool.ENEMY_BLACK_HOLE, "B.Hole", (30, 0, 50)),
        (EditorTool.ENEMY_GHOST, "Ghost", (200, 200, 230)),
        (EditorTool.ENEMY_RED_BALL, "R.Ball", (220, 40, 40)),
        (EditorTool.ENEMY_SNAKE, "Snake", (60, 140, 60)),
        (EditorTool.ENEMY_EVIL_CLOUD, "Cloud", (80, 80, 100)),
        (EditorTool.ENEMY_UFO, "UFO", (160, 170, 180)),
    ]),
    ("Items", [
        (EditorTool.COIN, "Coin", (255, 215, 0)),
        (EditorTool.POWERUP_JETPACK, "Jetpack", (255, 100, 50)),
        (EditorTool.POWERUP_BLASTER, "Blaster", (100, 100, 255)),
        (EditorTool.POWERUP_SHIELD, "Shield", (100, 200, 255)),
        (EditorTool.POWERUP_MAGNET, "Magnet", (255, 50, 50)),
    ]),
    ("Special", [
        (EditorTool.START, "Start", (50, 255, 50)),
        (EditorTool.FINISH, "Finish", (255, 255, 50)),
        (EditorTool.ERASER, "Erase", (255, 80, 80)),
        (EditorTool.SELECT, "Select", (200, 200, 200)),
    ]),
]


class PlacedObject:
    """An object placed in the editor."""

    def __init__(self, obj_type, grid_x, grid_y, **kwargs):
        self.obj_type = obj_type
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.properties = kwargs

    def to_dict(self):
        """Convert to JSON-serializable dict."""
        d = {
            "type": self.obj_type,
            "x": self.grid_x,
            "y": self.grid_y,
        }
        d.update(self.properties)
        return d


class LevelEditor:
    """Grid-based level editor."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Grid settings
        self.grid_size = 32
        self.grid_width = screen_width // self.grid_size + 2
        self.grid_height = 200

        # Camera / scroll
        self.scroll_y = 0
        self.target_scroll_y = 0
        self.scroll_speed = 500
        self.min_scroll = 0
        self.max_scroll_y = 0
        self._recalc_scroll_bounds()

        # Scroll dragging with middle mouse
        self._middle_mouse_dragging = False
        self._middle_mouse_start_y = 0
        self._middle_mouse_start_scroll = 0

        # Current tool
        self.current_tool = EditorTool.PLATFORM_NORMAL

        # Placed objects
        self.objects = []

        # Start and finish positions (grid coords)
        self.start_pos = (self.grid_width // 2, self.grid_height - 3)
        self.finish_pos = (self.grid_width // 2, 5)

        # Level name
        self.level_name = "My Level"
        self.editing_name = False

        # Toolbar
        self.toolbar_width = 120
        self.toolbar_scroll = 0
        self.toolbar_max_scroll = 0

        # Selected object for dragging
        self.selected_object = None
        self.dragging = False

        # Mouse state
        self.mouse_grid_x = 0
        self.mouse_grid_y = 0
        self.mouse_in_editor = False

        # Keyboard scroll state
        self._scroll_up_held = False
        self._scroll_down_held = False

        # Feedback message
        self.message = ""
        self.message_timer = 0

        # Button rects (computed during draw)
        self._button_rects = {}
        self._tool_rects = {}

    def _recalc_scroll_bounds(self):
        """Recalculate scroll limits."""
        self.max_scroll_y = max(0, self.grid_height * self.grid_size - (self.screen_height - 40))
        self.min_scroll = 0

    def reset(self):
        """Reset editor to empty state."""
        self.objects.clear()
        self._recalc_scroll_bounds()

        # Start at bottom of level
        self.scroll_y = self.max_scroll_y
        self.target_scroll_y = self.scroll_y

        self.current_tool = EditorTool.PLATFORM_NORMAL
        self.level_name = "My Level"
        self.selected_object = None
        self.editing_name = False
        self.message = ""

        self._scroll_up_held = False
        self._scroll_down_held = False

        # Place default start platform
        self._place_object(EditorTool.PLATFORM_NORMAL,
                           self.grid_width // 2 - 1, self.grid_height - 3, width=3)

    def handle_event(self, event):
        """Handle editor events. Returns 'back', 'test', or None."""
        if event.type == pygame.KEYDOWN:
            if self.editing_name:
                if event.key == pygame.K_RETURN:
                    self.editing_name = False
                elif event.key == pygame.K_BACKSPACE:
                    self.level_name = self.level_name[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.editing_name = False
                elif event.unicode and len(self.level_name) < 30:
                    self.level_name += event.unicode
                return None

            if event.key == pygame.K_ESCAPE:
                return "back"
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self._save_level()
            elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                if self.selected_object:
                    if self.selected_object in self.objects:
                        self.objects.remove(self.selected_object)
                    self.selected_object = None

            # Keyboard scrolling
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                self._scroll_up_held = True
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self._scroll_down_held = True
            elif event.key == pygame.K_PAGEUP:
                self.target_scroll_y -= self.screen_height // 2
            elif event.key == pygame.K_PAGEDOWN:
                self.target_scroll_y += self.screen_height // 2
            elif event.key == pygame.K_HOME:
                self.target_scroll_y = 0
            elif event.key == pygame.K_END:
                self.target_scroll_y = self.max_scroll_y

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self._scroll_up_held = False
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self._scroll_down_held = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Middle mouse drag scroll
            if event.button == 2:
                self._middle_mouse_dragging = True
                self._middle_mouse_start_y = my
                self._middle_mouse_start_scroll = self.scroll_y
                return None

            # Check buttons
            for btn_name, btn_rect in self._button_rects.items():
                if btn_rect.collidepoint(mx, my):
                    return self._handle_button(btn_name)

            # Check tool selection
            for tool_id, tool_rect in self._tool_rects.items():
                if tool_rect.collidepoint(mx, my):
                    self.current_tool = tool_id
                    return None

            # Check name click
            if hasattr(self, '_name_rect') and self._name_rect.collidepoint(mx, my):
                self.editing_name = True
                return None

            # Editor area
            editor_x = mx - self.toolbar_width
            if editor_x >= 0 and my >= 40:
                gx = editor_x // self.grid_size
                gy = (my - 40 + int(self.scroll_y)) // self.grid_size

                if event.button == 1:  # Left click
                    if self.current_tool == EditorTool.ERASER:
                        self._erase_at(gx, gy)
                    elif self.current_tool == EditorTool.SELECT:
                        self._select_at(gx, gy)
                    elif self.current_tool == EditorTool.START:
                        self.start_pos = (gx, gy)
                    elif self.current_tool == EditorTool.FINISH:
                        self.finish_pos = (gx, gy)
                    else:
                        self._place_at_grid(gx, gy)

                elif event.button == 3:  # Right click = erase
                    self._erase_at(gx, gy)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self._middle_mouse_dragging = False

        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if mx < self.toolbar_width:
                # Scroll toolbar
                self.toolbar_scroll -= event.y * 20
                self.toolbar_scroll = max(0, min(self.toolbar_scroll,
                                                  self.toolbar_max_scroll))
            else:
                # Scroll editor
                self.target_scroll_y -= event.y * self.grid_size * 2
                self._clamp_scroll()

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos

            # Middle mouse drag
            if self._middle_mouse_dragging:
                delta = self._middle_mouse_start_y - my
                self.target_scroll_y = self._middle_mouse_start_scroll + delta
                self.scroll_y = self.target_scroll_y
                self._clamp_scroll()
                return None

            editor_x = mx - self.toolbar_width
            if editor_x >= 0 and my >= 40:
                self.mouse_grid_x = editor_x // self.grid_size
                self.mouse_grid_y = (my - 40 + int(self.scroll_y)) // self.grid_size
                self.mouse_in_editor = True

                # Drag painting
                if pygame.mouse.get_pressed()[0]:
                    if self.current_tool == EditorTool.ERASER:
                        self._erase_at(self.mouse_grid_x, self.mouse_grid_y)
                    elif self.current_tool not in (EditorTool.SELECT, EditorTool.START,
                                                    EditorTool.FINISH):
                        self._place_at_grid(self.mouse_grid_x, self.mouse_grid_y)
            else:
                self.mouse_in_editor = False

        return None

    def _clamp_scroll(self):
        """Clamp scroll values to valid range."""
        self._recalc_scroll_bounds()
        self.target_scroll_y = max(self.min_scroll,
                                    min(self.target_scroll_y, self.max_scroll_y))
        self.scroll_y = max(self.min_scroll, min(self.scroll_y, self.max_scroll_y))

    def _handle_button(self, btn_name):
        """Handle editor button clicks."""
        if btn_name == "back":
            return "back"
        elif btn_name == "save":
            self._save_level()
        elif btn_name == "test":
            return "test"
        elif btn_name == "clear":
            self.objects.clear()
            self.selected_object = None
            self.message = "Cleared!"
            self.message_timer = 1.5
        elif btn_name == "export":
            data = self.export_level_data()
            if data:
                text = json.dumps(data, indent=2, ensure_ascii=False)
                if copy_to_clipboard(text):
                    self.message = get_text("editor_exported")
                else:
                    self.message = "Clipboard not available"
                self.message_timer = 2.0
        elif btn_name == "import":
            text = paste_from_clipboard()
            if text:
                try:
                    data = json.loads(text)
                    self._import_level_data(data)
                    self.message = get_text("editor_imported")
                except Exception:
                    self.message = get_text("editor_import_error")
                self.message_timer = 2.0
        return None

    def _place_at_grid(self, gx, gy):
        """Place current tool at grid position."""
        for obj in self.objects:
            if obj.grid_x == gx and obj.grid_y == gy:
                if obj.obj_type == self.current_tool:
                    return

        self._place_object(self.current_tool, gx, gy)

    def _place_object(self, tool, gx, gy, **kwargs):
        """Place an object at grid position."""
        properties = dict(kwargs)

        if tool.startswith("platform"):
            if "width" not in properties:
                properties["width"] = 2
        if tool == EditorTool.PLATFORM_MOVING:
            if "range" not in properties:
                properties["range"] = 4
            if "speed" not in properties:
                properties["speed"] = 2

        obj = PlacedObject(tool, gx, gy, **properties)
        self.objects.append(obj)

    def _erase_at(self, gx, gy):
        """Erase objects at grid position."""
        self.objects = [
            obj for obj in self.objects
            if not self._object_at(obj, gx, gy)
        ]
        if self.selected_object and self.selected_object not in self.objects:
            self.selected_object = None

    def _object_at(self, obj, gx, gy):
        """Check if object occupies grid cell."""
        width = obj.properties.get("width", 1)
        if obj.obj_type.startswith("platform"):
            width = obj.properties.get("width", 2)
        return (obj.grid_x <= gx < obj.grid_x + width and obj.grid_y == gy)

    def _select_at(self, gx, gy):
        """Select object at grid position."""
        self.selected_object = None
        for obj in reversed(self.objects):
            if self._object_at(obj, gx, gy):
                self.selected_object = obj
                break

    def _save_level(self):
        """Save level to custom_levels directory."""
        data = self.export_level_data()
        if data:
            filename = self.level_name.replace(" ", "_").lower() + ".json"
            filepath = os.path.join(CUSTOM_LEVELS_DIR, filename)
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.message = get_text("editor_saved")
                self.message_timer = 2.0
            except IOError:
                self.message = "Save error!"
                self.message_timer = 2.0

    def export_level_data(self):
        """Export level as JSON dict."""
        platforms = []
        enemies = []
        coins = []
        powerups = []

        for obj in self.objects:
            d = obj.to_dict()
            t = obj.obj_type

            if t.startswith("platform_"):
                ptype = t.replace("platform_", "")
                d["type"] = ptype
                platforms.append(d)
            elif t.startswith("enemy_"):
                etype = t.replace("enemy_", "")
                d["type"] = etype
                enemies.append(d)
            elif t == "coin":
                d.pop("type", None)
                coins.append(d)
            elif t.startswith("powerup_"):
                ptype = t.replace("powerup_", "")
                d["type"] = ptype
                powerups.append(d)

        return {
            "name": self.level_name,
            "author": "Player",
            "version": 1,
            "height": self.grid_height * self.grid_size,
            "grid_size": self.grid_size,
            "background_theme": save_manager.equipped.get("theme", "day"),
            "platforms": platforms,
            "enemies": enemies,
            "coins": coins,
            "powerups": powerups,
            "start": {"x": self.start_pos[0], "y": self.start_pos[1]},
            "finish_y": self.finish_pos[1],
            "star_scores": [500, 1000, 2000]
        }

    def _import_level_data(self, data):
        """Import level from JSON data."""
        self.objects.clear()
        self.selected_object = None
        self.level_name = data.get("name", "Imported Level")

        for p in data.get("platforms", []):
            tool = f"platform_{p.get('type', 'normal')}"
            gx = p.get("x", 0)
            gy = p.get("y", 0)
            props = {k: v for k, v in p.items() if k not in ("type", "x", "y")}
            self.objects.append(PlacedObject(tool, gx, gy, **props))

        for e in data.get("enemies", []):
            tool = f"enemy_{e.get('type', 'slug')}"
            gx = e.get("x", 0)
            gy = e.get("y", 0)
            props = {k: v for k, v in e.items() if k not in ("type", "x", "y")}
            self.objects.append(PlacedObject(tool, gx, gy, **props))

        for c in data.get("coins", []):
            gx = c.get("x", 0)
            gy = c.get("y", 0)
            self.objects.append(PlacedObject("coin", gx, gy))

        for pw in data.get("powerups", []):
            tool = f"powerup_{pw.get('type', 'shield')}"
            gx = pw.get("x", 0)
            gy = pw.get("y", 0)
            self.objects.append(PlacedObject(tool, gx, gy))

        start = data.get("start", {})
        self.start_pos = (start.get("x", self.grid_width // 2),
                          start.get("y", self.grid_height - 3))
        self.finish_pos = (self.grid_width // 2, data.get("finish_y", 5))

        # Scroll to start position
        self.target_scroll_y = max(0, self.start_pos[1] * self.grid_size - self.screen_height // 2)
        self._clamp_scroll()

    def update(self, dt):
        """Update editor state."""
        # Keyboard scrolling
        if self._scroll_up_held:
            self.target_scroll_y -= self.scroll_speed * dt
        if self._scroll_down_held:
            self.target_scroll_y += self.scroll_speed * dt

        self._clamp_scroll()

        # Smooth scroll
        diff = self.target_scroll_y - self.scroll_y
        if abs(diff) > 0.5:
            self.scroll_y += diff * 0.2
        else:
            self.scroll_y = self.target_scroll_y

        self._clamp_scroll()

        # Message timer
        if self.message_timer > 0:
            self.message_timer -= dt

    def draw(self, surface):
        """Draw the level editor."""
        # Update is called here too for safety
        # (in case game.py doesn't call it separately)

        surface.fill((25, 25, 40))

        # Top bar
        self._draw_top_bar(surface)

        # Toolbar (left side)
        self._draw_toolbar(surface)

        # Editor area
        self._draw_editor_area(surface)

        # Scroll indicator
        self._draw_scroll_indicator(surface)

        # Message
        if self.message_timer > 0 and self.message:
            alpha = min(255, int(self.message_timer * 255))
            msg_font = font_manager.get_font(16)
            msg_surf = msg_font.render(self.message, True, (100, 255, 100))
            msg_surf.set_alpha(alpha)
            msg_rect = msg_surf.get_rect(center=(self.screen_width // 2,
                                                   self.screen_height - 30))
            surface.blit(msg_surf, msg_rect)

    def _draw_top_bar(self, surface):
        """Draw top button bar."""
        bar_h = 38
        pygame.draw.rect(surface, (35, 35, 55), (0, 0, self.screen_width, bar_h))

        mx, my = pygame.mouse.get_pos()
        x = 5
        btn_h = 28
        btn_y = 5

        self._button_rects = {}

        buttons = [
            ("back", get_text("menu_back"), 65, (80, 80, 100)),
            ("save", get_text("editor_save"), 60, (60, 120, 60)),
            ("test", get_text("editor_test"), 55, (120, 100, 40)),
            ("clear", get_text("editor_clear"), 55, (140, 60, 60)),
            ("export", get_text("editor_export"), 65, (80, 80, 120)),
            ("import", get_text("editor_import"), 65, (80, 100, 80)),
        ]

        for btn_id, label, btn_w, color in buttons:
            rect = pygame.Rect(x, btn_y, btn_w, btn_h)
            hover = rect.collidepoint(mx, my)
            draw_button(surface, label, font_manager.get_font(11),
                        (x, btn_y, btn_w, btn_h), color, hover=hover, border_radius=5)
            self._button_rects[btn_id] = rect
            x += btn_w + 4

        # Level name
        name_x = x + 10
        name_font = font_manager.get_font(14)
        name_text = self.level_name
        if self.editing_name:
            name_text += "|"
        name_color = (255, 200, 100) if self.editing_name else (200, 200, 220)
        name_surf = name_font.render(name_text, True, name_color)
        self._name_rect = pygame.Rect(name_x, btn_y,
                                       max(100, name_surf.get_width() + 20), btn_h)
        pygame.draw.rect(surface, (50, 50, 70), self._name_rect, border_radius=4)
        surface.blit(name_surf, (name_x + 5, btn_y + 5))

    def _draw_toolbar(self, surface):
        """Draw tool selection toolbar."""
        toolbar_rect = pygame.Rect(0, 38, self.toolbar_width, self.screen_height - 38)
        pygame.draw.rect(surface, (35, 35, 55), toolbar_rect)

        mx, my = pygame.mouse.get_pos()
        y = 42 - int(self.toolbar_scroll)
        btn_size = 28
        pad = 3

        self._tool_rects = {}
        tool_font = font_manager.get_font(9)

        for cat_name, tools in TOOL_CATEGORIES:
            cat_font = font_manager.get_font(10)
            cat_surf = cat_font.render(cat_name, True, (140, 140, 160))
            if 38 < y < self.screen_height:
                surface.blit(cat_surf, (5, y))
            y += 16

            col = 0
            for tool_id, tool_name, tool_color in tools:
                tx = 4 + col * (btn_size + pad)
                if 38 < y + btn_size < self.screen_height and y > 38:
                    rect = pygame.Rect(tx, y, btn_size, btn_size)
                    is_selected = self.current_tool == tool_id
                    hover = rect.collidepoint(mx, my)

                    if is_selected:
                        pygame.draw.rect(surface, (255, 255, 100),
                                          rect.inflate(4, 4), border_radius=4)
                    bg = lighten_color(tool_color, 1.2) if hover else tool_color
                    pygame.draw.rect(surface, bg, rect, border_radius=3)

                    label = tool_font.render(tool_name[:4], True, (255, 255, 255))
                    label_rect = label.get_rect(center=rect.center)
                    surface.blit(label, label_rect)

                    self._tool_rects[tool_id] = rect

                col += 1
                if col >= 3:
                    col = 0
                    y += btn_size + pad

            if col > 0:
                y += btn_size + pad
            y += 6

        self.toolbar_max_scroll = max(0, y + int(self.toolbar_scroll) - self.screen_height + 50)

    def _draw_editor_area(self, surface):
        """Draw the main editor grid and objects."""
        editor_x = self.toolbar_width
        editor_w = self.screen_width - self.toolbar_width
        editor_y = 38
        editor_h = self.screen_height - editor_y

        # Clip
        clip_rect = pygame.Rect(editor_x, editor_y, editor_w, editor_h)
        surface.set_clip(clip_rect)

        # Background
        theme = save_manager.equipped.get("theme", "day")
        theme_colors = THEME_COLORS.get(theme, THEME_COLORS["day"])
        bg_color = darken_color(theme_colors["bg_bottom"], 0.4)
        pygame.draw.rect(surface, bg_color, clip_rect)

        # Grid lines
        scroll = int(self.scroll_y)
        grid = self.grid_size

        # Vertical lines
        for x in range(0, editor_w + grid, grid):
            screen_x = editor_x + x
            color = (50, 50, 70) if (x // grid) % 5 != 0 else (70, 70, 90)
            pygame.draw.line(surface, color, (screen_x, editor_y),
                              (screen_x, editor_y + editor_h))

        # Horizontal lines
        first_visible_row = scroll // grid
        last_visible_row = (scroll + editor_h) // grid + 1

        for row in range(first_visible_row, last_visible_row + 1):
            screen_y = editor_y + row * grid - scroll
            color = (50, 50, 70) if row % 5 != 0 else (70, 70, 90)
            pygame.draw.line(surface, color, (editor_x, screen_y),
                              (editor_x + editor_w, screen_y))

            # Row numbers every 5 rows
            if row % 5 == 0:
                row_font = font_manager.get_font(9)
                row_surf = row_font.render(str(row), True, (80, 80, 100))
                surface.blit(row_surf, (editor_x + 2, screen_y + 1))

        # Draw placed objects
        for obj in self.objects:
            self._draw_placed_object(surface, obj, editor_x, editor_y, scroll)

        # Draw start and finish markers
        self._draw_marker(surface, self.start_pos[0], self.start_pos[1],
                           "START", (50, 255, 50), editor_x, editor_y, scroll)
        self._draw_marker(surface, self.finish_pos[0], self.finish_pos[1],
                           "FINISH", (255, 255, 50), editor_x, editor_y, scroll)

        # Draw cursor ghost
        if self.mouse_in_editor and self.current_tool not in (EditorTool.SELECT,
                                                                EditorTool.ERASER):
            ghost_x = editor_x + self.mouse_grid_x * grid
            ghost_y = editor_y + self.mouse_grid_y * grid - scroll
            ghost_w = grid * 2 if self.current_tool.startswith("platform") else grid
            ghost_h = grid

            ghost_surf = create_surface_with_alpha(ghost_w, ghost_h)
            pygame.draw.rect(ghost_surf, (255, 255, 255, 60),
                              (0, 0, ghost_w, ghost_h), border_radius=3)
            pygame.draw.rect(ghost_surf, (255, 255, 255, 120),
                              (0, 0, ghost_w, ghost_h), width=1, border_radius=3)
            surface.blit(ghost_surf, (ghost_x, ghost_y))

        # Eraser cursor
        if self.mouse_in_editor and self.current_tool == EditorTool.ERASER:
            ghost_x = editor_x + self.mouse_grid_x * grid
            ghost_y = editor_y + self.mouse_grid_y * grid - scroll
            ghost_surf = create_surface_with_alpha(grid, grid)
            pygame.draw.rect(ghost_surf, (255, 50, 50, 80),
                              (0, 0, grid, grid), border_radius=3)
            pygame.draw.line(ghost_surf, (255, 50, 50, 150),
                              (4, 4), (grid - 4, grid - 4), 2)
            pygame.draw.line(ghost_surf, (255, 50, 50, 150),
                              (grid - 4, 4), (4, grid - 4), 2)
            surface.blit(ghost_surf, (ghost_x, ghost_y))

        # Selected object highlight
        if self.selected_object:
            obj = self.selected_object
            ox = editor_x + obj.grid_x * grid
            oy = editor_y + obj.grid_y * grid - scroll
            ow = obj.properties.get("width", 1) * grid
            if obj.obj_type.startswith("platform"):
                ow = obj.properties.get("width", 2) * grid
            oh = grid
            pygame.draw.rect(surface, (255, 255, 100),
                              (ox - 2, oy - 2, ow + 4, oh + 4), width=2, border_radius=3)

        surface.set_clip(None)

        # Info bar at bottom
        info_font = font_manager.get_font(11)
        scroll_pct = int(self.scroll_y / max(1, self.max_scroll_y) * 100) if self.max_scroll_y > 0 else 0
        info_text = (f"Objects: {len(self.objects)} | "
                     f"Grid: ({self.mouse_grid_x}, {self.mouse_grid_y}) | "
                     f"Scroll: {scroll_pct}% | "
                     f"Tool: {self.current_tool.replace('_', ' ')}")
        info_surf = info_font.render(info_text, True, (150, 150, 170))
        info_bg = pygame.Rect(self.toolbar_width, self.screen_height - 20,
                               self.screen_width - self.toolbar_width, 20)
        pygame.draw.rect(surface, (30, 30, 45), info_bg)
        surface.blit(info_surf, (self.toolbar_width + 5, self.screen_height - 18))

    def _draw_scroll_indicator(self, surface):
        """Draw scroll position indicator on right edge."""
        if self.max_scroll_y <= 0:
            return

        editor_y = 38
        editor_h = self.screen_height - editor_y - 20
        indicator_x = self.screen_width - 8

        # Track
        pygame.draw.rect(surface, (50, 50, 70),
                          (indicator_x, editor_y, 6, editor_h), border_radius=3)

        # Thumb
        view_ratio = (self.screen_height - 58) / (self.grid_height * self.grid_size)
        view_ratio = min(1.0, view_ratio)
        thumb_h = max(20, int(editor_h * view_ratio))

        scroll_ratio = self.scroll_y / self.max_scroll_y if self.max_scroll_y > 0 else 0
        thumb_y = editor_y + int((editor_h - thumb_h) * scroll_ratio)

        pygame.draw.rect(surface, (100, 100, 130),
                          (indicator_x, thumb_y, 6, thumb_h), border_radius=3)

    def _draw_placed_object(self, surface, obj, editor_x, editor_y, scroll):
        """Draw a placed object."""
        grid = self.grid_size
        x = editor_x + obj.grid_x * grid
        y = editor_y + obj.grid_y * grid - scroll

        if y < editor_y - grid * 2 or y > self.screen_height + grid:
            return

        t = obj.obj_type
        width = obj.properties.get("width", 1)

        if t.startswith("platform"):
            if t == EditorTool.PLATFORM_NORMAL:
                color = (80, 200, 80)
            elif t == EditorTool.PLATFORM_MOVING:
                color = (80, 150, 255)
            elif t == EditorTool.PLATFORM_BREAKABLE:
                color = (160, 100, 60)
            elif t == EditorTool.PLATFORM_DISAPPEARING:
                color = (200, 200, 200)
            elif t == EditorTool.PLATFORM_SPRING:
                color = (220, 200, 50)
            else:
                color = (150, 150, 150)

            pw = width * grid
            ph = grid // 2
            py = y + grid // 4
            pygame.draw.rect(surface, color, (x, py, pw, ph), border_radius=3)
            pygame.draw.rect(surface, darken_color(color, 0.7),
                              (x, py, pw, ph), width=1, border_radius=3)

            # Type label
            type_label = t.replace("platform_", "")[:3].upper()
            lf = font_manager.get_font(8)
            ls = lf.render(type_label, True, (255, 255, 255))
            surface.blit(ls, (x + 2, py + 1))

        elif t.startswith("enemy"):
            color = (220, 60, 60)
            size = grid - 4
            pygame.draw.rect(surface, color, (x + 2, y + 2, size, size), border_radius=4)
            pygame.draw.rect(surface, darken_color(color, 0.6),
                              (x + 2, y + 2, size, size), width=1, border_radius=4)
            label = t.replace("enemy_", "")[:3].upper()
            lf = font_manager.get_font(8)
            ls = lf.render(label, True, (255, 255, 255))
            surface.blit(ls, (x + 4, y + 4))

        elif t == "coin":
            cx = x + grid // 2
            cy = y + grid // 2
            pygame.draw.circle(surface, (255, 215, 0), (cx, cy), grid // 3)
            pygame.draw.circle(surface, (200, 170, 0), (cx, cy), grid // 3, 1)
            lf = font_manager.get_font(8)
            ls = lf.render("$", True, (200, 170, 0))
            lr = ls.get_rect(center=(cx, cy))
            surface.blit(ls, lr)

        elif t.startswith("powerup"):
            color = (100, 200, 255)
            size = grid - 6
            pygame.draw.rect(surface, color, (x + 3, y + 3, size, size), border_radius=5)
            pygame.draw.rect(surface, darken_color(color, 0.7),
                              (x + 3, y + 3, size, size), width=1, border_radius=5)
            label = t.replace("powerup_", "")[:3].upper()
            lf = font_manager.get_font(8)
            ls = lf.render(label, True, (255, 255, 255))
            surface.blit(ls, (x + 5, y + 5))

    def _draw_marker(self, surface, gx, gy, label, color, editor_x, editor_y, scroll):
        """Draw start/finish marker."""
        grid = self.grid_size
        x = editor_x + gx * grid
        y = editor_y + gy * grid - scroll

        if y < editor_y - grid * 2 or y > self.screen_height + grid * 2:
            return

        # Flag pole
        pygame.draw.line(surface, color, (x + 3, y + grid), (x + 3, y - grid // 2), 2)

        # Flag triangle
        pygame.draw.polygon(surface, color, [
            (x + 5, y - grid // 2),
            (x + grid, y - grid // 4),
            (x + 5, y)
        ])

        # Label below
        lf = font_manager.get_font(10)
        ls = lf.render(label, True, color)
        surface.blit(ls, (x + 3, y + grid + 2))

        # Horizontal line across screen for finish
        if label == "FINISH":
            for dx in range(0, self.screen_width - self.toolbar_width, 8):
                px = editor_x + dx
                line_color = (255, 255, 50, 80) if (dx // 8) % 2 == 0 else (0, 0, 0, 0)
                if line_color[3] > 0:
                    pygame.draw.line(surface, line_color[:3],
                                      (px, y + grid // 2), (px + 4, y + grid // 2), 1)
"""
botyarajump - Shop
In-game shop for purchasing skins, trails, themes, and boosters.
"""

import pygame
import math

from settings import (
    save_manager, SHOP_SKINS, SHOP_TRAILS, SHOP_THEMES, BOOSTER_TYPES
)
from localization import get_text
from renderer import font_manager, sprite_renderer
from utils import (
    draw_rounded_rect, draw_text_with_alpha, draw_button,
    point_in_rect, create_surface_with_alpha, darken_color, lighten_color,
    SKIN_COLORS, THEME_COLORS
)


class ShopTab:
    """Represents a tab in the shop."""
    SKINS = "skins"
    TRAILS = "trails"
    THEMES = "themes"
    BOOSTERS = "boosters"


class Shop:
    """Shop screen for purchasing items."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.active_tab = ShopTab.SKINS
        self.scroll_y = 0
        self.max_scroll = 0
        self.target_scroll = 0

        # Feedback message
        self.message = ""
        self.message_timer = 0
        self.message_color = (255, 255, 255)

        # Tab definitions
        self.tabs = [
            ShopTab.SKINS,
            ShopTab.TRAILS,
            ShopTab.THEMES,
            ShopTab.BOOSTERS,
        ]

        # Layout
        self.tab_height = 45
        self.header_height = 80
        self.item_height = 70
        self.item_padding = 8
        self.content_y = self.header_height + self.tab_height + 10

        # Mouse tracking
        self.hovered_item = None
        self.hovered_button = None

    def set_message(self, text, color=(255, 255, 255)):
        """Show a temporary message."""
        self.message = text
        self.message_timer = 2.0
        self.message_color = color

    def handle_event(self, event):
        """Handle input events. Returns 'back' if back button pressed."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Back button
            back_rect = pygame.Rect(10, 10, 80, 35)
            if back_rect.collidepoint(mx, my):
                return "back"

            # Tab buttons
            tab_width = self.screen_width // len(self.tabs)
            for i, tab in enumerate(self.tabs):
                tab_rect = pygame.Rect(
                    i * tab_width, self.header_height,
                    tab_width, self.tab_height
                )
                if tab_rect.collidepoint(mx, my):
                    self.active_tab = tab
                    self.scroll_y = 0
                    self.target_scroll = 0
                    return None

            # Item buttons (buy/equip)
            items = self._get_current_items()
            for idx, (item_id, item_data) in enumerate(items):
                item_y = self.content_y + idx * (self.item_height + self.item_padding) - self.scroll_y
                item_rect = pygame.Rect(10, item_y, self.screen_width - 20, self.item_height)

                if not item_rect.collidepoint(mx, my):
                    continue

                # Check button area (right side)
                btn_rect = pygame.Rect(
                    self.screen_width - 110, item_y + 15,
                    90, self.item_height - 30
                )
                if btn_rect.collidepoint(mx, my):
                    self._handle_item_click(item_id, item_data)
                    return None

            # Scroll with mousewheel handled below

        elif event.type == pygame.MOUSEWHEEL:
            self.target_scroll -= event.y * 30
            self.target_scroll = max(0, min(self.target_scroll, self.max_scroll))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"

        return None

    def _handle_item_click(self, item_id, item_data):
        """Handle clicking buy/equip button on an item."""
        category = self._get_category_for_tab()
        equip_category = self._get_equip_category_for_tab()

        is_owned = save_manager.is_unlocked(category, item_id)

        if is_owned:
            # Equip
            if self.active_tab == ShopTab.BOOSTERS:
                # Find empty slot to equip booster
                equipped = save_manager.equipped.get("boosters", ["", "", "", ""])
                slot_found = False
                for i in range(4):
                    if i < len(equipped) and (equipped[i] == "" or equipped[i] == item_id):
                        save_manager.equip_booster(i, item_id)
                        slot_found = True
                        break
                if not slot_found:
                    # Replace first slot
                    save_manager.equip_booster(0, item_id)
                self.set_message(get_text("shop_equipped"), (100, 255, 100))
            else:
                save_manager.equip_item(equip_category, item_id)
                self.set_message(get_text("shop_equipped"), (100, 255, 100))
        else:
            # Buy
            price = item_data.get("price", 0)
            if price == 0:
                # Free item, just unlock
                save_manager.unlock_item(category, item_id)
                save_manager.equip_item(equip_category, item_id)
                self.set_message(get_text("shop_equipped"), (100, 255, 100))
            elif save_manager.spend_coins(price):
                save_manager.unlock_item(category, item_id)
                self.set_message(get_text("shop_equipped"), (100, 255, 100))
                # Achievement check
                save_manager.unlock_achievement("ach_first_purchase")
            else:
                self.set_message(get_text("shop_not_enough"), (255, 80, 80))

    def _get_current_items(self):
        """Get items for current tab."""
        if self.active_tab == ShopTab.SKINS:
            return list(SHOP_SKINS.items())
        elif self.active_tab == ShopTab.TRAILS:
            return list(SHOP_TRAILS.items())
        elif self.active_tab == ShopTab.THEMES:
            return list(SHOP_THEMES.items())
        elif self.active_tab == ShopTab.BOOSTERS:
            return list(BOOSTER_TYPES.items())
        return []

    def _get_category_for_tab(self):
        """Get unlock category name for current tab."""
        mapping = {
            ShopTab.SKINS: "skins",
            ShopTab.TRAILS: "trails",
            ShopTab.THEMES: "themes",
            ShopTab.BOOSTERS: "boosters",
        }
        return mapping.get(self.active_tab, "skins")

    def _get_equip_category_for_tab(self):
        """Get equip category name for current tab."""
        mapping = {
            ShopTab.SKINS: "skin",
            ShopTab.TRAILS: "trail",
            ShopTab.THEMES: "theme",
        }
        return mapping.get(self.active_tab, "skin")

    def update(self, dt):
        """Update shop animations."""
        # Smooth scroll
        self.scroll_y += (self.target_scroll - self.scroll_y) * 0.2

        # Message timer
        if self.message_timer > 0:
            self.message_timer -= dt

        # Calculate max scroll
        items = self._get_current_items()
        total_height = len(items) * (self.item_height + self.item_padding)
        visible_height = self.screen_height - self.content_y - 10
        self.max_scroll = max(0, total_height - visible_height)

        # Update mouse hover
        mx, my = pygame.mouse.get_pos()
        self.hovered_item = None
        for idx, (item_id, _) in enumerate(items):
            item_y = self.content_y + idx * (self.item_height + self.item_padding) - self.scroll_y
            item_rect = pygame.Rect(10, item_y, self.screen_width - 20, self.item_height)
            if item_rect.collidepoint(mx, my):
                self.hovered_item = item_id
                break

    def draw(self, surface):
        """Draw the shop screen."""
        lang = save_manager.get_language()

        # Background
        surface.fill((30, 30, 50))

        # Header
        title = get_text("shop_title")
        title_font = font_manager.get_font(28)
        title_surf = title_font.render(title, True, (255, 255, 255))
        surface.blit(title_surf, (self.screen_width // 2 - title_surf.get_width() // 2, 15))

        # Coins display
        coins_text = f"{get_text('shop_your_coins')}: {save_manager.coins}"
        coins_font = font_manager.get_font(16)
        coins_surf = coins_font.render(coins_text, True, (255, 215, 0))
        surface.blit(coins_surf, (self.screen_width // 2 - coins_surf.get_width() // 2, 50))

        # Back button
        back_text = get_text("menu_back")
        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(10, 10, 80, 35)
        back_hover = back_rect.collidepoint(mx, my)
        draw_button(surface, back_text, font_manager.get_font(14),
                     (10, 10, 80, 35), (80, 80, 100), hover=back_hover)

        # Tabs
        self._draw_tabs(surface)

        # Content area clip
        content_rect = pygame.Rect(0, self.content_y, self.screen_width,
                                    self.screen_height - self.content_y)
        surface.set_clip(content_rect)

        # Items
        self._draw_items(surface)

        surface.set_clip(None)

        # Message
        if self.message_timer > 0 and self.message:
            msg_alpha = min(255, int(self.message_timer * 255))
            msg_font = font_manager.get_font(18)
            msg_surf = msg_font.render(self.message, True, self.message_color)
            msg_surf.set_alpha(msg_alpha)
            msg_rect = msg_surf.get_rect(center=(self.screen_width // 2,
                                                   self.screen_height - 40))
            surface.blit(msg_surf, msg_rect)

    def _draw_tabs(self, surface):
        """Draw tab buttons."""
        tab_width = self.screen_width // len(self.tabs)
        mx, my = pygame.mouse.get_pos()

        tab_names = {
            ShopTab.SKINS: get_text("shop_skins"),
            ShopTab.TRAILS: get_text("shop_trails"),
            ShopTab.THEMES: get_text("shop_themes"),
            ShopTab.BOOSTERS: get_text("shop_boosters"),
        }

        for i, tab in enumerate(self.tabs):
            x = i * tab_width
            y = self.header_height
            rect = pygame.Rect(x, y, tab_width, self.tab_height)

            is_active = tab == self.active_tab
            is_hover = rect.collidepoint(mx, my)

            if is_active:
                color = (80, 100, 160)
            elif is_hover:
                color = (60, 70, 100)
            else:
                color = (45, 45, 65)

            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (100, 100, 140), rect, width=1)

            if is_active:
                pygame.draw.line(surface, (150, 180, 255),
                                 (x, y + self.tab_height - 2),
                                 (x + tab_width, y + self.tab_height - 2), 3)

            name = tab_names.get(tab, tab)
            tab_font = font_manager.get_font(14)
            text_surf = tab_font.render(name, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            surface.blit(text_surf, text_rect)

    def _draw_items(self, surface):
        """Draw shop items."""
        items = self._get_current_items()
        category = self._get_category_for_tab()
        equip_category = self._get_equip_category_for_tab()

        mx, my = pygame.mouse.get_pos()

        for idx, (item_id, item_data) in enumerate(items):
            item_y = self.content_y + idx * (self.item_height + self.item_padding) - int(self.scroll_y)

            # Skip if off screen
            if item_y + self.item_height < self.content_y or item_y > self.screen_height:
                continue

            is_owned = save_manager.is_unlocked(category, item_id)
            is_equipped = False

            if self.active_tab == ShopTab.BOOSTERS:
                equipped_boosters = save_manager.equipped.get("boosters", [])
                is_equipped = item_id in equipped_boosters
            elif self.active_tab != ShopTab.BOOSTERS:
                is_equipped = save_manager.equipped.get(equip_category) == item_id

            is_hovered = self.hovered_item == item_id

            # Background
            if is_equipped:
                bg_color = (50, 80, 60)
            elif is_hovered:
                bg_color = (55, 55, 75)
            else:
                bg_color = (45, 45, 65)

            item_rect = pygame.Rect(10, item_y, self.screen_width - 20, self.item_height)
            draw_rounded_rect(surface, bg_color, item_rect, radius=8)

            border_color = (100, 200, 100) if is_equipped else (80, 80, 100)
            pygame.draw.rect(surface, border_color, item_rect, width=1, border_radius=8)

            # Preview icon
            self._draw_item_preview(surface, 20, item_y + 5, item_id, item_data)

            # Name and price
            name_key = item_data.get("name_key", item_id)
            if self.active_tab == ShopTab.BOOSTERS:
                name_key = f"booster_{item_id}"
            name = get_text(name_key)

            name_font = font_manager.get_font(16)
            name_surf = name_font.render(name, True, (255, 255, 255))
            surface.blit(name_surf, (75, item_y + 8))

            # Price or status
            price = item_data.get("price", 0)
            price_font = font_manager.get_font(12)

            if is_owned:
                if is_equipped:
                    status_text = get_text("shop_equipped")
                    status_color = (100, 255, 100)
                else:
                    status_text = get_text("shop_owned")
                    status_color = (180, 180, 200)
            else:
                status_text = f"{price} coins"
                can_afford = save_manager.coins >= price
                status_color = (255, 215, 0) if can_afford else (255, 80, 80)

            status_surf = price_font.render(status_text, True, status_color)
            surface.blit(status_surf, (75, item_y + 28))

            # Skin ability description
            if self.active_tab == ShopTab.SKINS:
                skin_desc = {
                    "default": "Классический прыгун",
                    "red": "Огненный шлейф",
                    "blue": "Устойчивость ко льду",
                    "gold": "+25% Монет и Магнит",
                    "neon": "+25% Скорость бега",
                    "pixel": "+30% Шанс спавна монет",
                    "ghost": "Щит от 1 смертельного удара",
                    "rainbow": "+15% Высота прыжка",
                    "ninja": "Двойной прыжок в воздухе",
                    "robot": "Скорострельный лазер"
                }.get(item_id, "")
                desc_font = font_manager.get_font(11)
                desc_surf = desc_font.render(skin_desc, True, (160, 210, 255))
                surface.blit(desc_surf, (75, item_y + 46))

            # Buy/Equip button
            btn_w = 90
            btn_h = self.item_height - 30
            btn_x = self.screen_width - btn_w - 20
            btn_y = item_y + 15
            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            btn_hover = btn_rect.collidepoint(mx, my)

            if is_equipped:
                btn_color = (60, 100, 60)
                btn_text = get_text("shop_equipped")
            elif is_owned:
                btn_color = (60, 80, 140)
                btn_text = get_text("shop_equip")
            else:
                btn_color = (140, 100, 40)
                btn_text = get_text("shop_buy")

            draw_button(surface, btn_text, font_manager.get_font(12),
                        (btn_x, btn_y, btn_w, btn_h), btn_color,
                        hover=btn_hover, border_radius=6)

    def _draw_item_preview(self, surface, x, y, item_id, item_data):
        """Draw a small preview of the item."""
        preview_size = 50

        if self.active_tab == ShopTab.SKINS:
            # Draw mini player with skin
            sprite_renderer.draw_player(
                surface, x + 5, y + 5, 30, 30,
                skin_id=item_id, facing_right=True
            )

        elif self.active_tab == ShopTab.TRAILS:
            # Draw trail sample
            colors = {
                "none": (100, 100, 100),
                "fire": (255, 150, 50),
                "stars": (255, 255, 100),
                "rainbow": (255, 100, 200),
                "bubbles": (100, 200, 255),
                "snow": (220, 230, 255),
                "hearts": (255, 100, 120),
                "lightning": (150, 200, 255),
            }
            color = colors.get(item_id, (200, 200, 200))
            for i in range(5):
                px = x + 25 + i * 2
                py = y + 10 + i * 6
                size = max(2, 5 - i)
                alpha = 255 - i * 40
                dot_surf = create_surface_with_alpha(size * 2, size * 2)
                pygame.draw.circle(dot_surf, (*color, alpha), (size, size), size)
                surface.blit(dot_surf, (px - size, py - size))

        elif self.active_tab == ShopTab.THEMES:
            # Draw mini background gradient
            theme_colors = THEME_COLORS.get(item_id, THEME_COLORS["day"])
            top = theme_colors["bg_top"]
            bottom = theme_colors["bg_bottom"]
            preview_rect = pygame.Rect(x + 5, y + 5, 45, 50)
            for row in range(50):
                t = row / 50
                r = int(top[0] + (bottom[0] - top[0]) * t)
                g = int(top[1] + (bottom[1] - top[1]) * t)
                b = int(top[2] + (bottom[2] - top[2]) * t)
                pygame.draw.line(surface, (r, g, b),
                                 (x + 5, y + 5 + row), (x + 50, y + 5 + row))
            pygame.draw.rect(surface, (100, 100, 100), preview_rect, width=1, border_radius=3)

        elif self.active_tab == ShopTab.BOOSTERS:
            # Draw booster icon
            sprite_renderer.draw_booster_icon(surface, x + 8, y + 8, 40, item_id)
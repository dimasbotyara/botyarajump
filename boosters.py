"""
botyarajump - Boosters
Purchasable boosters that can be activated during gameplay.
Shared cooldown across all booster slots.
"""

import pygame
import time

from settings import save_manager, BOOSTER_COOLDOWN, BOOSTER_TYPES
from utils import key_name_to_key, clamp


class BoosterSlot:
    """Represents one equipped booster slot."""

    def __init__(self, slot_index, booster_id=""):
        self.slot_index = slot_index
        self.booster_id = booster_id
        self.uses_remaining = 0  # How many uses left this game

    def is_empty(self):
        return not self.booster_id or self.booster_id == ""

    def get_config(self):
        """Get booster configuration."""
        if self.is_empty():
            return None
        return BOOSTER_TYPES.get(self.booster_id, None)


class BoosterManager:
    """Manages booster activation and cooldowns during gameplay."""

    def __init__(self):
        self.slots = [BoosterSlot(i) for i in range(4)]
        self.shared_cooldown = 0.0
        self.cooldown_max = BOOSTER_COOLDOWN

        # Key bindings for booster slots
        self._booster_keys = [[] for _ in range(4)]

        # Visual feedback
        self.last_activated_slot = -1
        self.activation_flash_timer = 0
        self.activation_flash_duration = 0.3

        # Callback for effects
        self.on_activate = None  # Set by game.py

    def reset(self):
        """Reset for new game - load equipped boosters."""
        self.shared_cooldown = 0.0
        self.last_activated_slot = -1
        self.activation_flash_timer = 0

        equipped = save_manager.equipped.get("boosters", ["", "", "", ""])

        for i in range(4):
            booster_id = equipped[i] if i < len(equipped) else ""
            self.slots[i].booster_id = booster_id

            # Each booster gets 1 use per game (purchased)
            if booster_id and save_manager.is_unlocked("boosters", booster_id):
                self.slots[i].uses_remaining = 1
            else:
                self.slots[i].uses_remaining = 0

        self._update_keybindings()

    def _update_keybindings(self):
        """Load key bindings for booster slots."""
        controls = save_manager.get_controls()

        for i in range(4):
            key_name = f"booster_{i + 1}"
            bindings = controls.get(key_name, [])
            self._booster_keys[i] = []
            for kn in bindings:
                k = key_name_to_key(kn)
                if k is not None:
                    self._booster_keys[i].append(k)

    def handle_event(self, event):
        """Handle key events for booster activation."""
        if event.type == pygame.KEYDOWN:
            for i in range(4):
                if event.key in self._booster_keys[i]:
                    self.try_activate(i)
                    return True
        return False

    def try_activate(self, slot_index):
        """Try to activate booster in given slot. Returns True if activated."""
        if slot_index < 0 or slot_index >= 4:
            return False

        slot = self.slots[slot_index]

        # Check if slot has a booster
        if slot.is_empty():
            return False

        # Check uses remaining
        if slot.uses_remaining <= 0:
            return False

        # Check cooldown
        if self.shared_cooldown > 0:
            return False

        # Activate!
        slot.uses_remaining -= 1
        self.shared_cooldown = self.cooldown_max
        self.last_activated_slot = slot_index
        self.activation_flash_timer = self.activation_flash_duration

        # Track stats
        save_manager.add_stat("boosters_used")

        # Trigger effect callback
        if self.on_activate:
            self.on_activate(slot.booster_id)

        return True

    def update(self, dt):
        """Update cooldowns and timers."""
        if self.shared_cooldown > 0:
            self.shared_cooldown = max(0, self.shared_cooldown - dt)

        if self.activation_flash_timer > 0:
            self.activation_flash_timer = max(0, self.activation_flash_timer - dt)

    def get_cooldown_percent(self):
        """Get cooldown progress 0.0 (ready) to 1.0 (full cooldown)."""
        if self.cooldown_max <= 0:
            return 0.0
        return clamp(self.shared_cooldown / self.cooldown_max, 0, 1)

    def is_on_cooldown(self):
        """Check if boosters are on cooldown."""
        return self.shared_cooldown > 0

    def get_slot_info(self, slot_index):
        """Get info about a booster slot for HUD display.
        Returns dict with booster_id, uses, on_cooldown, cooldown_pct.
        """
        if slot_index < 0 or slot_index >= 4:
            return None

        slot = self.slots[slot_index]
        return {
            "booster_id": slot.booster_id,
            "uses": slot.uses_remaining,
            "on_cooldown": self.is_on_cooldown(),
            "cooldown_pct": self.get_cooldown_percent(),
            "is_empty": slot.is_empty(),
            "is_flashing": (self.last_activated_slot == slot_index
                            and self.activation_flash_timer > 0)
        }

    def has_any_booster(self):
        """Check if any slot has a booster equipped."""
        return any(not slot.is_empty() for slot in self.slots)

    def has_usable_booster(self):
        """Check if any booster can be activated."""
        if self.is_on_cooldown():
            return False
        return any(
            not slot.is_empty() and slot.uses_remaining > 0
            for slot in self.slots
        )
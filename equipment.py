"""Экипировка: броня и амулеты."""

import math
import random
import pygame

EQUIPMENT = {
    "leather_armor": {
        "slot": "armor",
        "name": "Кожаный доспех",
        "max_hp": 15,
        "damage_reduction": 0.04,
        "color": (160, 110, 60),
        "rarity": "common",
    },
    "chain_mail": {
        "slot": "armor",
        "name": "Кольчуга",
        "max_hp": 30,
        "damage_reduction": 0.08,
        "color": (170, 170, 190),
        "rarity": "rare",
    },
    "shadow_cloak": {
        "slot": "armor",
        "name": "Плащ тени",
        "max_hp": 10,
        "speed_bonus": 0.12,
        "damage_reduction": 0.05,
        "color": (80, 60, 120),
        "rarity": "rare",
    },
    "lucky_coin": {
        "slot": "charm",
        "name": "Счастливая монета",
        "gold_multiplier": 0.25,
        "color": (255, 210, 60),
        "rarity": "common",
    },
    "mystic_amulet": {
        "slot": "charm",
        "name": "Мистический амулет",
        "exp_multiplier": 0.20,
        "crit_bonus": 0.06,
        "color": (180, 120, 255),
        "rarity": "rare",
    },
    "thorn_ring": {
        "slot": "charm",
        "name": "Кольцо шипов",
        "thorn_damage": 4,
        "color": (200, 80, 80),
        "rarity": "common",
    },
    "padded_vest": {
        "slot": "armor",
        "name": "Стёганка караванщика",
        "max_hp": 12,
        "damage_reduction": 0.05,
        "color": (140, 100, 55),
        "rarity": "common",
    },
    "hunter_mail": {
        "slot": "armor",
        "name": "Кольчуга охотника",
        "max_hp": 22,
        "damage_reduction": 0.07,
        "color": (120, 130, 95),
        "rarity": "uncommon",
    },
    "frost_plate": {
        "slot": "armor",
        "name": "Ледяной нагрудник",
        "max_hp": 35,
        "damage_reduction": 0.10,
        "color": (130, 190, 220),
        "rarity": "rare",
    },
    "caravan_plate": {
        "slot": "armor",
        "name": "Латы каравана",
        "max_hp": 40,
        "damage_reduction": 0.11,
        "gold_multiplier": 0.08,
        "color": (190, 150, 70),
        "rarity": "rare",
    },
    "wraith_mail": {
        "slot": "armor",
        "name": "Кольчуга призраков",
        "max_hp": 28,
        "damage_reduction": 0.12,
        "speed_bonus": 0.08,
        "color": (110, 90, 150),
        "rarity": "epic",
    },
    "aegis_plate": {
        "slot": "armor",
        "name": "Эгида стража",
        "max_hp": 55,
        "damage_reduction": 0.14,
        "color": (210, 200, 120),
        "rarity": "epic",
    },
    "ice_bulwark": {
        "slot": "armor",
        "name": "Ледяной бастион",
        "max_hp": 65,
        "damage_reduction": 0.16,
        "color": (160, 210, 255),
        "rarity": "epic",
    },
    "border_armor": {
        "slot": "armor",
        "name": "Доспех рубежа",
        "max_hp": 80,
        "damage_reduction": 0.18,
        "exp_multiplier": 0.08,
        "color": (255, 200, 80),
        "rarity": "legendary",
    },
}

DROP_TABLE = {
    "common": ["leather_armor", "lucky_coin", "thorn_ring"],
    "rare": ["chain_mail", "shadow_cloak", "mystic_amulet"],
}


class EquipmentManager:
    def __init__(self):
        self.slots = {"armor": None, "charm": None}

    def reset(self):
        self.slots = {"armor": None, "charm": None}

    def clear_armor_visual(self, player):
        player.visual_armor_id = None

    def _apply_item_effects(self, player, item_id):
        item = EQUIPMENT[item_id]
        player.max_hp += item.get("max_hp", 0)
        player.damage_reduction = min(0.45, player.damage_reduction + item.get("damage_reduction", 0))
        player.speed_multiplier += item.get("speed_bonus", 0)
        player.gold_multiplier += item.get("gold_multiplier", 0)
        player.exp_multiplier += item.get("exp_multiplier", 0)
        player.thorn_damage += item.get("thorn_damage", 0)
        player.equipment_crit_bonus = getattr(player, "equipment_crit_bonus", 0) + item.get("crit_bonus", 0)

    def _remove_item_effects(self, player, item_id):
        item = EQUIPMENT[item_id]
        player.max_hp = max(1, player.max_hp - item.get("max_hp", 0))
        player.damage_reduction = max(0.0, player.damage_reduction - item.get("damage_reduction", 0))
        player.speed_multiplier = max(0.5, player.speed_multiplier - item.get("speed_bonus", 0))
        player.gold_multiplier = max(1.0, player.gold_multiplier - item.get("gold_multiplier", 0))
        player.exp_multiplier = max(1.0, player.exp_multiplier - item.get("exp_multiplier", 0))
        player.thorn_damage = max(0, player.thorn_damage - item.get("thorn_damage", 0))
        player.equipment_crit_bonus = max(0.0, getattr(player, "equipment_crit_bonus", 0) - item.get("crit_bonus", 0))

    def equip(self, player, item_id):
        item = EQUIPMENT.get(item_id)
        if not item:
            return None
        slot = item["slot"]
        old = self.slots.get(slot)
        if old:
            self._remove_item_effects(player, old)
        self.slots[slot] = item_id
        self._apply_item_effects(player, item_id)
        if slot == "armor":
            player.visual_armor_id = item_id
        player.hp = min(player.max_hp, player.hp)
        return old

    def unequip_slot(self, player, slot):
        old = self.slots.get(slot)
        if old:
            self._remove_item_effects(player, old)
            self.slots[slot] = None
            if slot == "armor":
                player.visual_armor_id = None
        return old

    def summary_lines(self):
        lines = []
        for slot in ("armor", "charm"):
            item_id = self.slots.get(slot)
            if item_id:
                lines.append(EQUIPMENT[item_id]["name"])
        return lines

    def to_dict(self):
        return dict(self.slots)

    def load_dict(self, player, data):
        if not data:
            return
        for slot in self.slots:
            item_id = data.get(slot)
            if item_id and item_id in EQUIPMENT:
                self.equip(player, item_id)


def roll_equipment_drop(is_elite=False, is_boss=False):
    if is_boss and random.random() < 0.55:
        pool = DROP_TABLE["rare"]
    elif is_elite and random.random() < 0.18:
        pool = DROP_TABLE["common"] + DROP_TABLE["rare"]
    elif random.random() < 0.04:
        pool = DROP_TABLE["common"]
    else:
        return None
    return random.choice(pool)


def format_armor_stats(item_id):
    """Краткая строка статов брони для UI."""
    item = EQUIPMENT.get(item_id, {})
    parts = []
    if item.get("max_hp"):
        parts.append(f"+{item['max_hp']} HP")
    if item.get("damage_reduction"):
        parts.append(f"−{int(item['damage_reduction'] * 100)}% урона")
    if item.get("speed_bonus"):
        parts.append(f"+{int(item['speed_bonus'] * 100)}% скорость")
    if item.get("gold_multiplier"):
        parts.append(f"+{int(item['gold_multiplier'] * 100)}% золото")
    if item.get("exp_multiplier"):
        parts.append(f"+{int(item['exp_multiplier'] * 100)}% опыт")
    return " · ".join(parts) if parts else "Броня"


def get_equipped_armor_name(equipment):
    if not equipment:
        return "нет"
    item_id = equipment.slots.get("armor")
    if not item_id:
        return "нет"
    return EQUIPMENT.get(item_id, {}).get("name", item_id)


class EquipmentDrop(pygame.sprite.Sprite):
    BOB_SPEED = 0.06

    def __init__(self, x, y, item_id):
        super().__init__()
        self.item_id = item_id
        self.item = EQUIPMENT[item_id]
        self.image = pygame.Surface((22, 22), pygame.SRCALPHA)
        color = self.item["color"]
        pygame.draw.circle(self.image, color, (11, 11), 9)
        pygame.draw.circle(self.image, (255, 255, 255), (11, 11), 9, 1)
        pygame.draw.polygon(self.image, (255, 255, 255), [(11, 4), (14, 10), (8, 10)])
        self.rect = self.image.get_rect(center=(x, y))
        self.base_y = y
        self.bob = random.random() * 6.28
        self.lifetime = 900

    def update(self):
        self.bob += self.BOB_SPEED
        self.rect.centery = self.base_y + int(math.sin(self.bob) * 3)
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

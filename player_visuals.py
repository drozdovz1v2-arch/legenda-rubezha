"""Визуальные стили оружия и брони на спрайте игрока."""
import pygame

from equipment import EQUIPMENT

DEFAULT_WEAPON_STYLE = {
    "blade": (185, 195, 215),
    "edge": (255, 255, 255),
    "handle": (120, 80, 40),
    "blade_len": 18,
    "swing": (255, 240, 140),
    "swing_hot": (255, 200, 60),
}

WEAPON_STYLES = {
    "Железный меч": {"blade": (170, 175, 185), "handle": (90, 70, 45), "blade_len": 16},
    "Стальной палаш": {"blade": (200, 210, 225), "handle": (100, 85, 55), "blade_len": 19},
    "Клинок охотника": {"blade": (140, 190, 120), "handle": (80, 110, 60), "blade_len": 20},
    "Морозный клинок": {"blade": (140, 210, 255), "edge": (220, 245, 255), "handle": (70, 100, 130), "blade_len": 21},
    "Секира каравана": {"blade": (210, 170, 90), "handle": (120, 80, 40), "blade_len": 17, "swing": (255, 210, 120)},
    "Клинок призраков": {"blade": (170, 140, 220), "edge": (220, 200, 255), "handle": (90, 70, 120), "blade_len": 22},
    "Светозарный клинок": {
        "blade": (255, 240, 160),
        "edge": (255, 255, 220),
        "handle": (180, 140, 60),
        "blade_len": 24,
        "swing": (255, 250, 180),
        "swing_hot": (255, 220, 80),
    },
    "Рассекатель льда": {"blade": (160, 220, 255), "edge": (240, 250, 255), "handle": (100, 140, 180), "blade_len": 25},
    "Глефа рубежа": {
        "blade": (255, 210, 90),
        "edge": (255, 240, 180),
        "handle": (140, 90, 40),
        "blade_len": 28,
        "swing": (255, 200, 80),
        "swing_hot": (255, 160, 40),
    },
    "Клинок света": {
        "blade": (255, 240, 160),
        "edge": (255, 255, 220),
        "handle": (180, 140, 60),
        "blade_len": 24,
    },
}

TIER_WEAPON_FALLBACK = {
    0: "Железный меч",
    1: "Стальной палаш",
    2: "Клинок охотника",
    3: "Морозный клинок",
    4: "Клинок призраков",
    5: "Светозарный клинок",
    6: "Глефа рубежа",
}


def get_weapon_style(weapon_name):
    style = dict(DEFAULT_WEAPON_STYLE)
    if weapon_name in WEAPON_STYLES:
        style.update(WEAPON_STYLES[weapon_name])
        return style
    for tier in range(6, -1, -1):
        key = TIER_WEAPON_FALLBACK.get(tier)
        if key and key in WEAPON_STYLES and weapon_name:
            style.update(WEAPON_STYLES[key])
            break
    return style


def get_armor_color(armor_id):
    if not armor_id:
        return None
    item = EQUIPMENT.get(armor_id)
    if not item or item.get("slot") != "armor":
        return None
    return item.get("color", (140, 140, 160))


def _shade(color, delta):
    return tuple(max(0, min(255, c + delta)) for c in color)


def _draw_armor_overlay(surface, facing, armor_color, armor_id):
    if not armor_color:
        return
    dark = _shade(armor_color, -35)
    light = _shade(armor_color, 30)
    tier_hint = 0
    if armor_id in ("aegis_plate", "ice_bulwark", "border_armor", "chain_mail", "caravan_plate"):
        tier_hint = 2
    elif armor_id in ("frost_plate", "wraith_mail", "hunter_mail", "shadow_cloak"):
        tier_hint = 1

    if facing == "down":
        body = pygame.Rect(7, 13, 18, 16)
        pygame.draw.rect(surface, dark, body, border_radius=3)
        pygame.draw.rect(surface, armor_color, body.inflate(-4, -4), border_radius=2)
        pygame.draw.rect(surface, light, (body.x + 2, body.y + 2, body.w - 4, 4), border_radius=1)
        if tier_hint >= 1:
            pygame.draw.rect(surface, dark, (5, 14, 4, 8), border_radius=1)
            pygame.draw.rect(surface, dark, (23, 14, 4, 8), border_radius=1)
        if tier_hint >= 2:
            pygame.draw.rect(surface, light, (12, 11, 8, 4), border_radius=1)
    elif facing == "up":
        body = pygame.Rect(8, 13, 16, 15)
        pygame.draw.rect(surface, armor_color, body, border_radius=2)
        pygame.draw.line(surface, dark, (body.x, body.y + 6), (body.right, body.y + 6), 1)
    elif facing == "left":
        body = pygame.Rect(11, 13, 12, 16)
        pygame.draw.rect(surface, armor_color, body, border_radius=2)
        pygame.draw.rect(surface, dark, (11, 13, 3, 16), border_radius=1)
        if tier_hint >= 1:
            pygame.draw.rect(surface, dark, (9, 14, 3, 6), border_radius=1)
    else:
        body = pygame.Rect(9, 13, 12, 16)
        pygame.draw.rect(surface, armor_color, body, border_radius=2)
        pygame.draw.rect(surface, light, (body.right - 3, body.y, 3, 16), border_radius=1)
        if tier_hint >= 1:
            pygame.draw.rect(surface, dark, (20, 14, 3, 6), border_radius=1)


def _draw_back_weapon(surface, facing, style):
    blade = style["blade"]
    handle = style["handle"]
    if facing == "down":
        pygame.draw.rect(surface, handle, (22, 15, 3, 5))
        pygame.draw.rect(surface, blade, (22, 12, 3, 8))
    elif facing == "up":
        pygame.draw.rect(surface, blade, (4, 14, 3, 8))
    elif facing == "left":
        pygame.draw.rect(surface, blade, (3, 15, 3, 9))
    else:
        pygame.draw.rect(surface, blade, (25, 15, 3, 9))


def compose_player_image(base_image, facing, armor_id, weapon_name):
    """Накладывает броню и цвет оружия на базовый спрайт."""
    image = base_image.copy()
    armor_color = get_armor_color(armor_id)
    style = get_weapon_style(weapon_name)
    _draw_armor_overlay(image, facing, armor_color, armor_id)
    _draw_back_weapon(image, facing, style)
    return image

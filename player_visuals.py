"""Визуальные стили оружия и брони на спрайте игрока."""
import math

import pygame

from equipment import EQUIPMENT

DEFAULT_WEAPON_STYLE = {
    "shape": "sword",
    "blade": (185, 195, 215),
    "edge": (255, 255, 255),
    "handle": (120, 80, 40),
    "blade_len": 18,
    "blade_w": 5,
    "swing": (255, 240, 140),
    "swing_hot": (255, 200, 60),
    "glow": None,
}

WEAPON_STYLES = {
    "Железный меч": {
        "shape": "sword",
        "blade": (170, 175, 185),
        "handle": (90, 70, 45),
        "blade_len": 16,
        "blade_w": 4,
    },
    "Стальной палаш": {
        "shape": "saber",
        "blade": (200, 210, 225),
        "handle": (100, 85, 55),
        "blade_len": 19,
        "blade_w": 5,
    },
    "Клинок охотника": {
        "shape": "sword",
        "blade": (140, 190, 120),
        "edge": (200, 240, 170),
        "handle": (80, 110, 60),
        "blade_len": 20,
        "blade_w": 4,
    },
    "Морозный клинок": {
        "shape": "frost",
        "blade": (140, 210, 255),
        "edge": (220, 245, 255),
        "handle": (70, 100, 130),
        "blade_len": 22,
        "blade_w": 5,
        "glow": (180, 230, 255),
        "swing": (180, 230, 255),
        "swing_hot": (120, 200, 255),
    },
    "Секира каравана": {
        "shape": "axe",
        "blade": (210, 170, 90),
        "edge": (255, 220, 140),
        "handle": (120, 80, 40),
        "blade_len": 16,
        "blade_w": 8,
        "swing": (255, 210, 120),
    },
    "Клинок призраков": {
        "shape": "wraith",
        "blade": (170, 140, 220),
        "edge": (220, 200, 255),
        "handle": (90, 70, 120),
        "blade_len": 23,
        "blade_w": 4,
        "glow": (140, 100, 200),
        "swing": (190, 150, 255),
    },
    "Светозарный клинок": {
        "shape": "holy",
        "blade": (255, 240, 160),
        "edge": (255, 255, 220),
        "handle": (180, 140, 60),
        "blade_len": 24,
        "blade_w": 6,
        "glow": (255, 230, 120),
        "swing": (255, 250, 180),
        "swing_hot": (255, 220, 80),
    },
    "Рассекатель льда": {
        "shape": "frost",
        "blade": (160, 220, 255),
        "edge": (240, 250, 255),
        "handle": (100, 140, 180),
        "blade_len": 26,
        "blade_w": 6,
        "glow": (200, 240, 255),
    },
    "Глефа рубежа": {
        "shape": "glaive",
        "blade": (255, 210, 90),
        "edge": (255, 240, 180),
        "handle": (140, 90, 40),
        "blade_len": 28,
        "blade_w": 7,
        "glow": (255, 200, 80),
        "swing": (255, 200, 80),
        "swing_hot": (255, 160, 40),
    },
    "Клинок света": {
        "shape": "holy",
        "blade": (255, 240, 160),
        "edge": (255, 255, 220),
        "handle": (180, 140, 60),
        "blade_len": 24,
        "blade_w": 6,
        "glow": (255, 230, 120),
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

ARMOR_VISUALS = {
    "leather_armor": {"helmet": "cap", "cloak": False, "tier": 0},
    "padded_vest": {"helmet": "cap", "cloak": False, "tier": 0},
    "hunter_mail": {"helmet": "coif", "cloak": False, "tier": 1},
    "chain_mail": {"helmet": "coif", "cloak": False, "tier": 1},
    "frost_plate": {"helmet": "frost_helm", "cloak": False, "tier": 2},
    "caravan_plate": {"helmet": "plate", "cloak": False, "tier": 2},
    "shadow_cloak": {"helmet": "hood", "cloak": True, "tier": 2},
    "wraith_mail": {"helmet": "hood", "cloak": True, "tier": 3},
    "aegis_plate": {"helmet": "plate", "cloak": False, "tier": 3, "glow": True},
    "ice_bulwark": {"helmet": "frost_helm", "cloak": True, "tier": 4, "glow": True},
    "border_armor": {"helmet": "crown", "cloak": True, "tier": 4, "glow": True},
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


def get_armor_visual(armor_id):
    if not armor_id:
        return None
    item = EQUIPMENT.get(armor_id)
    if not item or item.get("slot") != "armor":
        return None
    base = {
        "color": item.get("color", (140, 140, 160)),
        "helmet": "cap",
        "cloak": False,
        "tier": 0,
        "glow": False,
    }
    base.update(ARMOR_VISUALS.get(armor_id, {}))
    return base


def get_armor_color(armor_id):
    vis = get_armor_visual(armor_id)
    return vis["color"] if vis else None


def _shade(color, delta):
    return tuple(max(0, min(255, c + delta)) for c in color)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _point_at(x, y, angle, dist):
    return x + math.cos(angle) * dist, y + math.sin(angle) * dist


def _draw_cloak(surface, facing, color, armor_id):
    dark = _shade(color, -50)
    mid = _shade(color, -20)
    if facing == "down":
        pygame.draw.polygon(surface, dark, [(4, 16), (28, 16), (30, 30), (2, 30)])
        pygame.draw.polygon(surface, mid, [(7, 17), (25, 17), (27, 28), (5, 28)])
        if armor_id in ("wraith_mail", "shadow_cloak"):
            pygame.draw.line(surface, _shade(color, 40), (16, 17), (16, 29), 1)
    elif facing == "up":
        pygame.draw.polygon(surface, dark, [(5, 18), (27, 18), (29, 30), (3, 30)])
        pygame.draw.polygon(surface, mid, [(8, 19), (24, 19), (26, 28), (6, 28)])
    elif facing == "left":
        pygame.draw.polygon(surface, dark, [(3, 15), (14, 14), (12, 30), (2, 30)])
        pygame.draw.polygon(surface, mid, [(5, 16), (12, 15), (10, 28), (4, 28)])
    else:
        pygame.draw.polygon(surface, dark, [(18, 14), (29, 15), (30, 30), (20, 30)])
        pygame.draw.polygon(surface, mid, [(20, 15), (27, 16), (28, 28), (22, 28)])


def _draw_helmet(surface, facing, helmet_type, color):
    dark = _shade(color, -40)
    light = _shade(color, 35)
    # Закрываем стандартный шлем базового спрайта
    cover = pygame.Rect(7, 1, 18, 13)
    tunic = (0, 70, 140) if facing == "up" else (0, 102, 204)
    pygame.draw.rect(surface, tunic, cover)

    if helmet_type == "cap":
        if facing == "down":
            pygame.draw.rect(surface, dark, (9, 3, 14, 8), border_radius=2)
            pygame.draw.rect(surface, color, (10, 4, 12, 6), border_radius=1)
            pygame.draw.rect(surface, dark, (8, 9, 16, 2))
        elif facing == "up":
            pygame.draw.rect(surface, color, (10, 4, 12, 7), border_radius=2)
        elif facing == "left":
            pygame.draw.rect(surface, color, (7, 3, 12, 9), border_radius=2)
            pygame.draw.rect(surface, dark, (6, 10, 14, 2))
        else:
            pygame.draw.rect(surface, color, (13, 3, 12, 9), border_radius=2)
            pygame.draw.rect(surface, dark, (12, 10, 14, 2))

    elif helmet_type == "coif":
        head = pygame.Rect(8, 2, 16, 11)
        pygame.draw.rect(surface, dark, head, border_radius=2)
        pygame.draw.rect(surface, color, head.inflate(-3, -3), border_radius=1)
        for y in range(head.y + 2, head.bottom - 1, 2):
            pygame.draw.line(surface, dark, (head.x + 2, y), (head.right - 2, y), 1)
        if facing == "down":
            pygame.draw.rect(surface, (30, 30, 30), (10, 7, 12, 2))

    elif helmet_type == "plate":
        head = pygame.Rect(8, 2, 16, 12)
        pygame.draw.rect(surface, dark, head, border_radius=3)
        pygame.draw.rect(surface, color, head.inflate(-3, -2), border_radius=2)
        pygame.draw.rect(surface, light, (head.x + 3, head.y + 2, head.w - 6, 3), border_radius=1)
        visor_y = head.y + 7
        if facing in ("down", "left", "right"):
            pygame.draw.rect(surface, (25, 28, 35), (10, visor_y, 12, 2))
        if facing == "left":
            pygame.draw.rect(surface, light, (8, head.y + 2, 3, head.h - 4), border_radius=1)
        elif facing == "right":
            pygame.draw.rect(surface, light, (head.right - 4, head.y + 2, 3, head.h - 4), border_radius=1)

    elif helmet_type == "frost_helm":
        head = pygame.Rect(8, 2, 16, 12)
        pygame.draw.rect(surface, dark, head, border_radius=3)
        pygame.draw.rect(surface, color, head.inflate(-3, -2), border_radius=2)
        pygame.draw.rect(surface, (240, 250, 255), (10, 8, 12, 2))
        spike_x = 16 if facing != "left" else 12
        pygame.draw.polygon(
            surface,
            (220, 245, 255),
            [(spike_x, 0), (spike_x - 3, 4), (spike_x + 3, 4)],
        )

    elif helmet_type == "hood":
        if facing == "down":
            pygame.draw.polygon(surface, dark, [(8, 4), (24, 4), (26, 14), (6, 14)])
            pygame.draw.polygon(surface, color, [(10, 5), (22, 5), (24, 13), (8, 13)])
            pygame.draw.rect(surface, (20, 15, 30), (12, 8, 8, 2))
        elif facing == "up":
            pygame.draw.polygon(surface, color, [(9, 3), (23, 3), (25, 13), (7, 13)])
            pygame.draw.polygon(surface, dark, [(16, 1), (12, 4), (20, 4)])
        elif facing == "left":
            pygame.draw.polygon(surface, color, [(6, 3), (16, 2), (15, 14), (5, 13)])
            pygame.draw.polygon(surface, dark, [(4, 8), (6, 4), (6, 12)])
        else:
            pygame.draw.polygon(surface, color, [(16, 2), (26, 3), (27, 14), (17, 13)])
            pygame.draw.polygon(surface, dark, [(28, 8), (26, 4), (26, 12)])

    elif helmet_type == "crown":
        head = pygame.Rect(8, 3, 16, 11)
        pygame.draw.rect(surface, dark, head, border_radius=3)
        pygame.draw.rect(surface, color, head.inflate(-3, -2), border_radius=2)
        for ox in (11, 16, 21):
            pygame.draw.polygon(
                surface,
                (255, 230, 120),
                [(ox, 1), (ox - 2, 5), (ox + 2, 5)],
            )
        pygame.draw.rect(surface, (255, 240, 180), (11, 8, 10, 2))


def _draw_armor_overlay(surface, facing, armor_id):
    vis = get_armor_visual(armor_id)
    if not vis:
        return
    color = vis["color"]
    dark = _shade(color, -35)
    light = _shade(color, 30)
    tier = vis.get("tier", 0)

    if facing == "down":
        body = pygame.Rect(7, 13, 18, 16)
        pygame.draw.rect(surface, dark, body, border_radius=3)
        pygame.draw.rect(surface, color, body.inflate(-4, -4), border_radius=2)
        pygame.draw.rect(surface, light, (body.x + 2, body.y + 2, body.w - 4, 4), border_radius=1)
        if tier >= 1:
            pygame.draw.rect(surface, dark, (5, 14, 4, 9), border_radius=1)
            pygame.draw.rect(surface, dark, (23, 14, 4, 9), border_radius=1)
        if tier >= 2:
            pygame.draw.rect(surface, light, (12, 11, 8, 4), border_radius=1)
            pygame.draw.line(surface, dark, (16, 13), (16, 27), 1)
        if tier >= 3:
            pygame.draw.rect(surface, _shade(color, 50), (body.x + 6, body.y + 8, 4, 5), border_radius=1)
    elif facing == "up":
        body = pygame.Rect(8, 13, 16, 15)
        pygame.draw.rect(surface, color, body, border_radius=2)
        pygame.draw.line(surface, dark, (body.x, body.y + 6), (body.right, body.y + 6), 1)
        if tier >= 2:
            pygame.draw.rect(surface, light, (body.x + 2, body.y + 2, body.w - 4, 3), border_radius=1)
    elif facing == "left":
        body = pygame.Rect(11, 13, 12, 16)
        pygame.draw.rect(surface, color, body, border_radius=2)
        pygame.draw.rect(surface, dark, (11, 13, 3, 16), border_radius=1)
        if tier >= 1:
            pygame.draw.rect(surface, dark, (9, 14, 3, 7), border_radius=1)
    else:
        body = pygame.Rect(9, 13, 12, 16)
        pygame.draw.rect(surface, color, body, border_radius=2)
        pygame.draw.rect(surface, light, (body.right - 3, body.y, 3, 16), border_radius=1)
        if tier >= 1:
            pygame.draw.rect(surface, dark, (20, 14, 3, 7), border_radius=1)

    if vis.get("glow"):
        glow = pygame.Surface((32, 32), pygame.SRCALPHA)
        glow_color = (*_shade(color, 60), 28)
        pygame.draw.ellipse(glow, glow_color, (4, 8, 24, 22))
        surface.blit(glow, (0, 0))


def _draw_back_weapon(surface, facing, style):
    shape = style.get("shape", "sword")
    blade = style["blade"]
    handle = style["handle"]
    edge = style.get("edge", (255, 255, 255))

    if shape == "axe":
        if facing == "down":
            pygame.draw.line(surface, handle, (23, 18), (23, 14), 2)
            pygame.draw.rect(surface, blade, (19, 10, 8, 5))
            pygame.draw.rect(surface, edge, (19, 10, 8, 2))
        elif facing == "left":
            pygame.draw.line(surface, handle, (4, 16), (8, 16), 2)
            pygame.draw.rect(surface, blade, (2, 12, 5, 6))
        else:
            pygame.draw.line(surface, handle, (26, 16), (22, 16), 2)
            pygame.draw.rect(surface, blade, (25, 12, 5, 6))

    elif shape == "glaive":
        if facing == "down":
            pygame.draw.line(surface, handle, (23, 17), (23, 13), 2)
            pygame.draw.line(surface, blade, (23, 11), (27, 8), 3)
            pygame.draw.line(surface, edge, (24, 10), (26, 9), 1)
            pygame.draw.line(surface, blade, (21, 10), (19, 9), 2)
        elif facing == "left":
            pygame.draw.line(surface, blade, (2, 14), (6, 10), 3)
            pygame.draw.line(surface, handle, (6, 14), (9, 16), 2)
        else:
            pygame.draw.line(surface, blade, (28, 14), (24, 10), 3)
            pygame.draw.line(surface, handle, (24, 15), (21, 17), 2)

    elif shape == "saber":
        if facing == "down":
            pygame.draw.line(surface, handle, (23, 16), (23, 13), 2)
            pygame.draw.arc(surface, blade, (18, 8, 10, 10), 0.2, 1.4, 3)
        elif facing == "left":
            pygame.draw.line(surface, blade, (3, 16), (6, 11), 3)
        else:
            pygame.draw.line(surface, blade, (27, 16), (24, 11), 3)

    elif shape in ("frost", "wraith", "holy"):
        if facing == "down":
            pygame.draw.line(surface, handle, (23, 16), (23, 13), 2)
            pygame.draw.line(surface, blade, (23, 12), (23, 7), 4 if shape == "holy" else 3)
            pygame.draw.line(surface, edge, (23, 12), (23, 7), 1)
            if shape == "frost":
                pygame.draw.polygon(surface, (220, 245, 255), [(23, 6), (21, 9), (25, 9)])
            elif shape == "wraith":
                pygame.draw.line(surface, (*blade, 120), (22, 11), (24, 8), 2)
            elif shape == "holy":
                pygame.draw.line(surface, style.get("glow", (255, 230, 120)), (22, 11), (24, 8), 1)
        elif facing == "left":
            pygame.draw.line(surface, blade, (3, 15), (3, 8), 3)
        else:
            pygame.draw.line(surface, blade, (27, 15), (27, 8), 3)

    else:
        if facing == "down":
            pygame.draw.rect(surface, handle, (22, 15, 3, 5))
            pygame.draw.rect(surface, blade, (22, 10, 3, 8))
            pygame.draw.line(surface, edge, (22, 10), (22, 7), 1)
        elif facing == "up":
            pygame.draw.rect(surface, blade, (4, 14, 3, 8))
        elif facing == "left":
            pygame.draw.rect(surface, blade, (3, 15, 3, 9))
        else:
            pygame.draw.rect(surface, blade, (25, 15, 3, 9))


def draw_weapon_strike(screen, cx, cy, angle, style, progress):
    """Рисует удар оружием на экране (во время атаки)."""
    blade_len = style["blade_len"] + int(8 * math.sin(progress * math.pi))
    grip_dist = 7
    hx, hy = _point_at(cx, cy, angle - 0.35, grip_dist)
    tx, ty = _point_at(cx, cy, angle, grip_dist + blade_len)
    shape = style.get("shape", "sword")
    bw = style.get("blade_w", 5)

    pygame.draw.line(screen, style["handle"], (cx, cy), (hx, hy), 3)

    if shape == "axe":
        pygame.draw.line(screen, style["handle"], (hx, hy), (tx, ty), 3)
        perp = angle + math.pi / 2
        ax1, ay1 = _point_at(tx, ty, perp, bw)
        ax2, ay2 = _point_at(tx, ty, perp + math.pi, bw)
        bx, by = _point_at(tx, ty, angle, 4)
        pygame.draw.polygon(screen, style["blade"], [(ax1, ay1), (ax2, ay2), (bx, by)])
        pygame.draw.polygon(screen, style.get("edge", (255, 255, 255)), [(ax1, ay1), (ax2, ay2), (bx, by)], 1)

    elif shape == "glaive":
        pygame.draw.line(screen, style["handle"], (hx, hy), (tx, ty), 3)
        pygame.draw.line(screen, style["blade"], (hx, hy), (tx, ty), bw)
        hook_angle = angle + 0.9
        hx2, hy2 = _point_at(tx, ty, hook_angle, 10)
        pygame.draw.line(screen, style["blade"], (tx, ty), (hx2, hy2), max(3, bw - 1))
        pygame.draw.line(screen, style.get("edge", (255, 255, 255)), (hx, hy), (tx, ty), 1)

    elif shape == "saber":
        steps = 8
        points = []
        for i in range(steps + 1):
            t = i / steps
            curve = 0.35 * math.sin(t * math.pi)
            points.append(_lerp_point(hx, hy, tx, ty, t, angle, curve * 12))
        for i in range(len(points) - 1):
            pygame.draw.line(screen, style["blade"], points[i], points[i + 1], bw)
        pygame.draw.line(screen, style.get("edge", (255, 255, 255)), points[-2], points[-1], 1)

    elif shape == "frost":
        pygame.draw.line(screen, style["blade"], (hx, hy), (tx, ty), bw)
        pygame.draw.line(screen, style.get("edge", (255, 255, 255)), (hx, hy), (tx, ty), 1)
        crystal = _point_at(tx, ty, angle, 5)
        pygame.draw.polygon(
            screen,
            (220, 245, 255),
            [
                crystal,
                _point_at(tx, ty, angle + 2.4, 4),
                _point_at(tx, ty, angle - 2.4, 4),
            ],
        )
        if style.get("glow"):
            _draw_attack_glow(screen, hx, hy, tx, ty, style["glow"], bw + 3)

    elif shape == "wraith":
        off = 2
        ox, oy = math.cos(angle + math.pi / 2) * off, math.sin(angle + math.pi / 2) * off
        ghost_color = _shade(style["blade"], 50)
        pygame.draw.line(screen, ghost_color, (hx + ox, hy + oy), (tx + ox, ty + oy), bw - 1)
        pygame.draw.line(screen, style["blade"], (hx, hy), (tx, ty), bw - 1)
        pygame.draw.line(screen, style.get("edge", (255, 255, 255)), (hx, hy), (tx, ty), 1)

    elif shape == "holy":
        pygame.draw.line(screen, style["blade"], (hx, hy), (tx, ty), bw + 1)
        pygame.draw.line(screen, style.get("edge", (255, 255, 255)), (hx, hy), (tx, ty), 2)
        if style.get("glow"):
            _draw_attack_glow(screen, hx, hy, tx, ty, style["glow"], bw + 4)
        spark = _point_at(tx, ty, angle, 3)
        pygame.draw.circle(screen, (255, 255, 220), (int(spark[0]), int(spark[1])), 2)

    else:
        pygame.draw.line(screen, style["blade"], (hx, hy), (tx, ty), bw)
        pygame.draw.line(screen, style.get("edge", (255, 255, 255)), (hx, hy), (tx, ty), 1)

    if progress > 0.28 and progress < 0.72 and shape not in ("wraith",):
        trail_end = _point_at(hx, hy, angle, blade_len)
        _draw_swing_trail(screen, hx, hy, trail_end, style)


def _lerp_point(x1, y1, x2, y2, t, angle, curve_offset):
    bx = x1 + (x2 - x1) * t
    by = y1 + (y2 - y1) * t
    nx = -math.sin(angle) * curve_offset
    ny = math.cos(angle) * curve_offset
    return (bx + nx, by + ny)


def _draw_attack_glow(screen, x1, y1, x2, y2, color, width):
    glow_surf = pygame.Surface((abs(int(x2 - x1)) + width * 4, abs(int(y2 - y1)) + width * 4), pygame.SRCALPHA)
    ox = min(x1, x2) - width * 2
    oy = min(y1, y2) - width * 2
    pygame.draw.line(
        glow_surf,
        (*color, 70),
        (x1 - ox, y1 - oy),
        (x2 - ox, y2 - oy),
        width,
    )
    screen.blit(glow_surf, (ox, oy))


def _draw_swing_trail(screen, hx, hy, trail_end, style):
    dx = trail_end[0] - hx
    dy = trail_end[1] - hy
    size = int(max(abs(dx), abs(dy)) + 24)
    trail = pygame.Surface((size, size), pygame.SRCALPHA)
    local_c = (size // 2, size // 2)
    end = (local_c[0] + dx, local_c[1] + dy)
    pygame.draw.line(trail, (*style["swing"], 90), local_c, end, 8)
    screen.blit(trail, (hx - local_c[0], hy - local_c[1]))


def compose_player_image(base_image, facing, armor_id, weapon_name):
    """Накладывает плащ, броню, шлем и оружие на базовый спрайт."""
    image = base_image.copy()
    vis = get_armor_visual(armor_id)
    style = get_weapon_style(weapon_name)

    if vis and vis.get("cloak"):
        _draw_cloak(image, facing, vis["color"], armor_id)

    _draw_armor_overlay(image, facing, armor_id)

    if vis:
        _draw_helmet(image, facing, vis.get("helmet", "cap"), vis["color"])

    _draw_back_weapon(image, facing, style)
    return image

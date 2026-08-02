import pygame
import random
import math
from config import TILE_SIZE, PLAYER_SIZE


def _tile_rng(gx, gy, salt=0):
    return random.Random(gx * 73417 + gy * 19373 + salt * 997)


def _shade(color, delta):
    return tuple(max(0, min(255, c + delta)) for c in color)


def _blend(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _vertical_gradient(surface, top, bottom):
    w, h = surface.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(surface, _blend(top, bottom, t), (0, y), (w, y))


def _speckle(surface, gx, gy, colors, count=10, salt=0):
    rng = _tile_rng(gx, gy, salt)
    w, h = surface.get_size()
    for _ in range(count):
        x = rng.randint(1, w - 2)
        y = rng.randint(1, h - 2)
        surface.set_at((x, y), rng.choice(colors))


def create_grass_sprite(gx=0, gy=0):
    rng = _tile_rng(gx, gy, 1)
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    variant = (gx + gy) % 4
    base = (36, 118, 52) if variant % 2 == 0 else (42, 128, 58)
    _vertical_gradient(surface, _shade(base, 14), _shade(base, -16))
    _speckle(surface, gx, gy, [(28, 96, 40), (52, 142, 62), (24, 82, 34)], 12, 2)
    if rng.random() < 0.35:
        fx, fy = rng.randint(6, TILE_SIZE - 8), rng.randint(8, TILE_SIZE - 10)
        pygame.draw.circle(surface, (70, 168, 72), (fx, fy), 2)
    if rng.random() < 0.2:
        pygame.draw.line(surface, (58, 150, 64), (4, 26), (8, 18), 1)
        pygame.draw.line(surface, (58, 150, 64), (22, 28), (26, 20), 1)
    if gx % 3 == 0 and gy % 3 == 0:
        pygame.draw.rect(surface, _shade(base, -24), (0, TILE_SIZE - 3, TILE_SIZE, 3))
    return surface


def create_wall_sprite(gx=0, gy=0):
    rng = _tile_rng(gx, gy, 3)
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    _vertical_gradient(surface, (92, 96, 104), (62, 64, 72))
    brick_h = 8
    offset = (gx % 2) * 8
    for row in range(0, TILE_SIZE, brick_h):
        shift = offset if (row // brick_h) % 2 else 0
        for col in range(-shift, TILE_SIZE, 16):
            rect = pygame.Rect(col, row, 15, brick_h - 1)
            tone = rng.randint(-8, 8)
            pygame.draw.rect(surface, _shade((88, 90, 98), tone), rect)
            pygame.draw.rect(surface, (48, 50, 56), rect, 1)
    pygame.draw.line(surface, (130, 132, 140), (1, 1), (TILE_SIZE - 2, 1), 1)
    if rng.random() < 0.25:
        pygame.draw.line(surface, (40, 42, 48), (rng.randint(4, 24), rng.randint(4, 24)),
                         (rng.randint(4, 24), rng.randint(4, 24)), 1)
    return surface


def create_tree_sprite(gx=0, gy=0):
    rng = _tile_rng(gx, gy, 5)
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    grass = create_grass_sprite(gx, gy)
    surface.blit(grass, (0, 0))
    shadow = pygame.Surface((20, 8), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 60))
    surface.blit(shadow, (8, 24))
    trunk_w = 6 + rng.randint(0, 2)
    pygame.draw.rect(surface, (92, 58, 28), (16 - trunk_w // 2, 18, trunk_w, 12))
    pygame.draw.rect(surface, (120, 78, 38), (16 - trunk_w // 2 + 1, 18, trunk_w - 2, 12))
    for radius, color, ox, oy in (
        (13, (18, 92, 34), 0, 0),
        (10, (28, 118, 44), -3, -2),
        (8, (48, 148, 58), 4, -4),
        (5, (72, 176, 72), 0, -6),
    ):
        pygame.draw.circle(surface, color, (16 + ox, 12 + oy), radius)
    return surface

def _draw_knight(surface, direction, walk_frame=0, attack_phase=None):
    """Рисует рыцаря: direction = down/up/left/right, walk_frame = 0..3, attack_phase = 0..2 или None."""
    w, h = surface.get_size()
    cx, cy = w // 2, h // 2
    step = walk_frame % 4
    leg_shift = [0, 2, 0, -2][step]
    body_bob = [0, 1, 0, 1][step]

    def draw_boots(left_x, right_x, y, spread=0):
        pygame.draw.rect(surface, (50, 50, 50), (left_x - spread, y, 6, 2))
        pygame.draw.rect(surface, (50, 50, 50), (right_x + spread, y, 6, 2))

    if direction == "down":
        draw_boots(8 + leg_shift, 18 - leg_shift, 30 - body_bob, spread=abs(leg_shift) // 2)
        pygame.draw.rect(surface, (0, 102, 204), (6, 12 - body_bob, 20, 18))
        pygame.draw.rect(surface, (255, 215, 0), (14, 16 - body_bob, 4, 6))
        pygame.draw.rect(surface, (169, 169, 169), (8, 2, 16, 12))
        pygame.draw.rect(surface, (30, 30, 30), (10, 6, 12, 3))
        if attack_phase is None:
            pygame.draw.rect(surface, (180, 180, 190), (22, 16, 3, 10))
        elif attack_phase >= 2:
            pygame.draw.rect(surface, (255, 215, 0), (14, 17 - body_bob, 4, 6))
    elif direction == "up":
        draw_boots(8 - leg_shift, 18 + leg_shift, 30 - body_bob)
        pygame.draw.rect(surface, (0, 70, 140), (6, 12 - body_bob, 20, 18))
        pygame.draw.rect(surface, (120, 80, 40), (10, 14 - body_bob, 12, 10))
        pygame.draw.rect(surface, (130, 130, 130), (8, 2, 16, 10))
        if attack_phase is None:
            pygame.draw.rect(surface, (180, 180, 190), (4, 16, 3, 10))
    elif direction == "left":
        foot_y = 28 - body_bob
        pygame.draw.rect(surface, (50, 50, 50), (8 + leg_shift, foot_y, 5, 2))
        pygame.draw.rect(surface, (50, 50, 50), (16 - leg_shift, foot_y + 2, 5, 2))
        pygame.draw.rect(surface, (0, 102, 204), (10, 12 - body_bob, 14, 18))
        pygame.draw.rect(surface, (169, 169, 169), (6, 3, 14, 12))
        pygame.draw.rect(surface, (30, 30, 30), (8, 7, 4, 2))
        if attack_phase is None:
            pygame.draw.rect(surface, (180, 180, 190), (4, 16, 3, 10))
        elif attack_phase >= 2:
            pygame.draw.rect(surface, (255, 215, 0), (12, 16 - body_bob, 4, 5))
    else:
        foot_y = 28 - body_bob
        pygame.draw.rect(surface, (50, 50, 50), (11 + leg_shift, foot_y, 5, 2))
        pygame.draw.rect(surface, (50, 50, 50), (19 - leg_shift, foot_y + 2, 5, 2))
        pygame.draw.rect(surface, (0, 102, 204), (8, 12 - body_bob, 14, 18))
        pygame.draw.rect(surface, (169, 169, 169), (12, 3, 14, 12))
        pygame.draw.rect(surface, (30, 30, 30), (20, 7, 4, 2))
        if attack_phase is None:
            pygame.draw.rect(surface, (180, 180, 190), (25, 16, 3, 10))
        elif attack_phase >= 2:
            pygame.draw.rect(surface, (255, 215, 0), (16, 16 - body_bob, 4, 5))


def _build_player_animations():
    directions = ("down", "up", "left", "right")
    walk = {d: [] for d in directions}
    attack = {d: [] for d in directions}
    idle = {}

    for direction in directions:
        for frame in range(4):
            surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
            _draw_knight(surf, direction, frame, attack_phase=None)
            walk[direction].append(surf)
        idle[direction] = walk[direction][0]
        for phase in range(5):
            surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
            _draw_knight(surf, direction, 0, attack_phase=phase)
            attack[direction].append(surf)

    return {"walk": walk, "attack": attack, "idle": idle}


_PLAYER_ANIMS = None


def invalidate_player_animations():
    global _PLAYER_ANIMS
    _PLAYER_ANIMS = None


def get_player_animations():
    global _PLAYER_ANIMS
    if _PLAYER_ANIMS is None:
        _PLAYER_ANIMS = _build_player_animations()
    return _PLAYER_ANIMS


def create_player_sprite():
    """Статичный спрайт для совместимости — idle вниз."""
    return get_player_animations()["idle"]["down"].copy()


def create_slime_frames():
    frames = []
    for i in range(4):
        pulse = 1.0 + 0.1 * math.sin(i * math.pi / 2)
        squash = 1.0 + 0.08 * math.cos(i * math.pi / 2)
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)
        cx, base_y = 12, 14
        radius_x = max(7, int(10 * pulse))
        radius_y = max(7, int(10 * squash))
        pygame.draw.ellipse(surf, (220, 20, 60), (cx - radius_x, base_y - radius_y + 2, radius_x * 2, radius_y * 2))
        pygame.draw.ellipse(surf, (255, 69, 0), (cx - radius_x + 2, base_y - radius_y + 4, radius_x * 2 - 4, radius_y * 2 - 4))
        eye_y = base_y - 4 + int((1 - pulse) * 2)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 4, eye_y), 2)
        pygame.draw.circle(surf, (255, 255, 255), (cx + 4, eye_y), 2)
        pygame.draw.circle(surf, (0, 0, 0), (cx - 3, eye_y), 1)
        pygame.draw.circle(surf, (0, 0, 0), (cx + 5, eye_y), 1)
        frames.append(surf)
    return frames


def create_boss_idle_frames():
    frames = []
    for i in range(4):
        bob = int(2 * math.sin(i * math.pi / 2))
        pulse = 1.0 + 0.06 * math.cos(i * math.pi / 2)
        surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        cx, base_y = 18, 22 + bob
        rx = int(15 * pulse)
        ry = int(15 * (2 - pulse + 0.05))
        pygame.draw.ellipse(surf, (0, 0, 205), (cx - rx, base_y - ry + 2, rx * 2, ry * 2))
        pygame.draw.ellipse(surf, (30, 144, 255), (cx - rx + 3, base_y - ry + 5, rx * 2 - 6, ry * 2 - 6))
        crown_y = 6 + bob
        pygame.draw.polygon(
            surf,
            (255, 215, 0),
            [(12, crown_y + 6), (15, crown_y + 12), (18, crown_y + 4), (21, crown_y + 12), (24, crown_y + 6), (18, crown_y + 12)],
        )
        blink = i == 2
        eye_y = base_y - 4
        if blink:
            pygame.draw.line(surf, (255, 255, 255), (10, eye_y), (14, eye_y), 2)
            pygame.draw.line(surf, (255, 255, 255), (22, eye_y), (26, eye_y), 2)
        else:
            pygame.draw.circle(surf, (255, 255, 255), (12, eye_y), 3)
            pygame.draw.circle(surf, (255, 255, 255), (24, eye_y), 3)
            pygame.draw.circle(surf, (0, 0, 80), (12, eye_y), 1)
            pygame.draw.circle(surf, (0, 0, 80), (24, eye_y), 1)
        frames.append(surf)
    return frames

def create_sand_sprite(gx=0, gy=0):
    rng = _tile_rng(gx, gy, 7)
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    base = (228, 196, 148) if (gx + gy) % 2 == 0 else (218, 186, 138)
    _vertical_gradient(surface, _shade(base, 12), _shade(base, -18))
    for i in range(3):
        y = 8 + i * 9 + (gx % 3)
        pygame.draw.arc(surface, _shade(base, -22), (-6, y, TILE_SIZE + 12, 8), 0, math.pi, 1)
    _speckle(surface, gx, gy, [(200, 170, 120), (240, 210, 165), (180, 150, 110)], 14, 8)
    if rng.random() < 0.12:
        pygame.draw.circle(surface, (190, 160, 115), (rng.randint(6, 26), rng.randint(6, 26)), 1)
    return surface


def create_cactus_sprite(gx=0, gy=0):
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surface.blit(create_sand_sprite(gx, gy), (0, 0))
    pygame.draw.rect(surface, (28, 118, 48), (13, 7, 7, 20))
    pygame.draw.rect(surface, (40, 150, 62), (14, 7, 4, 20))
    pygame.draw.rect(surface, (28, 118, 48), (7, 13, 5, 4))
    pygame.draw.rect(surface, (28, 118, 48), (5, 9, 3, 6))
    pygame.draw.rect(surface, (28, 118, 48), (20, 16, 5, 4))
    pygame.draw.rect(surface, (28, 118, 48), (22, 12, 3, 6))
    for px in (8, 12, 18, 22):
        pygame.draw.circle(surface, (20, 80, 30), (px, 10), 1)
    return surface


def create_snow_sprite(gx=0, gy=0):
    rng = _tile_rng(gx, gy, 9)
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    _vertical_gradient(surface, (236, 244, 255), (205, 220, 240))
    _speckle(surface, gx, gy, [(220, 232, 248), (245, 250, 255), (190, 210, 230)], 16, 10)
    if rng.random() < 0.4:
        pygame.draw.circle(surface, (255, 255, 255), (rng.randint(4, 28), rng.randint(4, 28)), 2)
    if (gx + gy) % 5 == 0:
        pygame.draw.line(surface, (255, 255, 255), (2, 14), (30, 16), 1)
    return surface


def create_ice_sprite(gx=0, gy=0):
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surface.blit(create_snow_sprite(gx, gy), (0, 0))
    pygame.draw.polygon(
        surface,
        (130, 200, 235),
        [(16, 3), (27, 13), (23, 29), (9, 29), (5, 13)],
    )
    pygame.draw.polygon(
        surface,
        (190, 232, 255),
        [(16, 7), (23, 14), (21, 25), (11, 25), (9, 14)],
    )
    pygame.draw.line(surface, (255, 255, 255), (11, 11), (18, 18), 2)
    pygame.draw.line(surface, (90, 160, 210), (5, 13), (27, 13), 1)
    return surface


def create_frost_slime_frames():
    frames = []
    for i in range(4):
        pulse = 1.0 + 0.12 * math.sin(i * math.pi / 2)
        squash = 1.0 + 0.1 * math.cos(i * math.pi / 2)
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)
        cx, base_y = 12, 14
        radius_x = max(7, int(10 * pulse))
        radius_y = max(7, int(10 * squash))
        pygame.draw.ellipse(surf, (80, 180, 230), (cx - radius_x, base_y - radius_y + 2, radius_x * 2, radius_y * 2))
        pygame.draw.ellipse(surf, (140, 220, 255), (cx - radius_x + 2, base_y - radius_y + 4, radius_x * 2 - 4, radius_y * 2 - 4))
        eye_y = base_y - 4 + int((1 - pulse) * 2)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 4, eye_y), 2)
        pygame.draw.circle(surf, (255, 255, 255), (cx + 4, eye_y), 2)
        pygame.draw.circle(surf, (20, 60, 120), (cx - 3, eye_y), 1)
        pygame.draw.circle(surf, (20, 60, 120), (cx + 5, eye_y), 1)
        frames.append(surf)
    return frames


def create_ice_guardian_frames():
    frames = []
    for i in range(4):
        bob = int(2 * math.sin(i * math.pi / 2))
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        cx, base = 20, 28 + bob
        pygame.draw.ellipse(surf, (70, 150, 210), (8, base - 18, 24, 20))
        pygame.draw.polygon(
            surf,
            (120, 200, 255),
            [(20, 4 + bob), (30, 14 + bob), (28, 24 + bob), (12, 24 + bob), (10, 14 + bob)],
        )
        pygame.draw.polygon(surf, (180, 230, 255), [(20, 8 + bob), (26, 16 + bob), (24, 22 + bob), (16, 22 + bob), (14, 16 + bob)])
        eye_glow = 220 if i != 2 else 120
        pygame.draw.circle(surf, (eye_glow, 240, 255), (16, 14 + bob), 3)
        pygame.draw.circle(surf, (eye_glow, 240, 255), (24, 14 + bob), 3)
        pygame.draw.rect(surf, (90, 160, 210), (6, base - 4, 8, 10), border_radius=2)
        pygame.draw.rect(surf, (90, 160, 210), (26, base - 4, 8, 10), border_radius=2)
        frames.append(surf)
    return frames


def create_npc_sprite(role="elder"):
    """Процедурные спрайты NPC: elder, merchant, scout"""
    surf = pygame.Surface((28, 28), pygame.SRCALPHA)
    if role == "elder":
        pygame.draw.rect(surf, (90, 60, 40), (10, 8, 8, 10))
        pygame.draw.rect(surf, (180, 160, 130), (8, 4, 12, 10))
        pygame.draw.rect(surf, (120, 80, 50), (6, 18, 16, 10))
        pygame.draw.rect(surf, (200, 180, 140), (4, 20, 20, 6))
        pygame.draw.line(surf, (220, 200, 160), (14, 14), (14, 22), 2)
    elif role == "merchant":
        pygame.draw.rect(surf, (60, 40, 30), (10, 8, 8, 10))
        pygame.draw.rect(surf, (200, 160, 80), (6, 16, 16, 12))
        pygame.draw.rect(surf, (255, 215, 0), (8, 18, 12, 4))
        pygame.draw.circle(surf, (240, 200, 160), (14, 10), 6)
        pygame.draw.rect(surf, (100, 60, 20), (4, 6, 20, 4))
    elif role == "mystic":
        pygame.draw.polygon(surf, (120, 80, 180), [(14, 2), (22, 12), (18, 24), (10, 24), (6, 12)])
        pygame.draw.circle(surf, (200, 180, 220), (14, 12), 5)
        pygame.draw.circle(surf, (100, 255, 200), (12, 11), 2)
        pygame.draw.circle(surf, (100, 255, 200), (16, 11), 2)
        pygame.draw.rect(surf, (80, 50, 120), (8, 18, 12, 8))
    else:  # scout
        pygame.draw.rect(surf, (50, 80, 120), (8, 14, 12, 12))
        pygame.draw.circle(surf, (200, 180, 150), (14, 10), 6)
        pygame.draw.polygon(surf, (180, 200, 220), [(6, 8), (14, 2), (22, 8), (14, 10)])
        pygame.draw.line(surf, (100, 140, 180), (14, 16), (14, 24), 2)
    return surf


def create_ruins_sprite(gx=0, gy=0):
    rng = _tile_rng(gx, gy, 11)
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    _vertical_gradient(surface, (62, 58, 74), (42, 38, 52))
    _speckle(surface, gx, gy, [(78, 72, 90), (50, 46, 60), (90, 84, 102)], 14, 12)
    pygame.draw.line(surface, (88, 82, 98), (3, 22), (29, 19), 1)
    pygame.draw.line(surface, (70, 64, 80), (8, 10), (24, 26), 1)
    if rng.random() < 0.3:
        pygame.draw.circle(surface, (48, 90, 58), (rng.randint(5, 26), rng.randint(18, 28)), 2)
    return surface


def create_ruins_pillar_sprite(gx=0, gy=0):
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surface.blit(create_ruins_sprite(gx, gy), (0, 0))
    pygame.draw.rect(surface, (88, 82, 102), (10, 3, 12, 24))
    pygame.draw.rect(surface, (118, 112, 132), (12, 3, 6, 24))
    pygame.draw.rect(surface, (72, 66, 86), (8, 26, 16, 4))
    pygame.draw.rect(surface, (140, 132, 152), (11, 3, 8, 3))
    return surface


def create_ruins_spike_sprite(gx=0, gy=0):
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surface.blit(create_ruins_sprite(gx, gy), (0, 0))
    pygame.draw.polygon(surface, (120, 50, 90), [(16, 5), (26, 29), (6, 29)])
    pygame.draw.polygon(surface, (168, 78, 120), [(16, 10), (21, 27), (11, 27)])
    pygame.draw.line(surface, (200, 120, 150), (16, 10), (16, 24), 1)
    return surface


def create_wolf_frames():
    frames = []
    for i in range(4):
        leg = i % 2
        surf = pygame.Surface((28, 24), pygame.SRCALPHA)
        body_color = (120, 110, 100)
        pygame.draw.ellipse(surf, body_color, (6, 10, 18, 10))
        pygame.draw.circle(surf, body_color, (22, 12), 7)
        pygame.draw.circle(surf, (220, 200, 180), (24, 11), 2)
        pygame.draw.circle(surf, (40, 30, 30), (25, 11), 1)
        pygame.draw.rect(surf, (80, 70, 60), (8, 18 + leg, 4, 5))
        pygame.draw.rect(surf, (80, 70, 60), (16, 18 + (1 - leg), 4, 5))
        pygame.draw.polygon(surf, (100, 90, 80), [(22, 6), (26, 10), (20, 10)])
        frames.append(surf)
    return frames


def create_scorpion_frames():
    frames = []
    for i in range(4):
        tail_up = i % 2 == 0
        surf = pygame.Surface((26, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (180, 120, 40), (4, 10, 14, 8))
        pygame.draw.circle(surf, (200, 140, 50), (18, 12), 5)
        pygame.draw.line(surf, (160, 100, 30), (6, 16), (4, 20), 2)
        pygame.draw.line(surf, (160, 100, 30), (10, 16), (12, 20), 2)
        tail_y = 4 if tail_up else 8
        pygame.draw.line(surf, (140, 80, 30), (20, 10), (24, tail_y), 2)
        pygame.draw.circle(surf, (200, 60, 40), (24, tail_y), 2)
        frames.append(surf)
    return frames


def create_wraith_frames():
    frames = []
    for i in range(4):
        bob = int(2 * math.sin(i * math.pi / 2))
        surf = pygame.Surface((24, 28), pygame.SRCALPHA)
        alpha = 200
        ghost = pygame.Surface((20, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(ghost, (140, 100, 200, alpha), (0, 4 + bob, 20, 16))
        pygame.draw.circle(ghost, (180, 140, 255, alpha), (10, 8 + bob), 7)
        pygame.draw.circle(ghost, (80, 255, 200, alpha), (7, 7 + bob), 2)
        pygame.draw.circle(ghost, (80, 255, 200, alpha), (13, 7 + bob), 2)
        surf.blit(ghost, (2, 0))
        frames.append(surf)
    return frames


def create_colossus_frames():
    frames = []
    for i in range(4):
        pulse = 1.0 + 0.05 * math.sin(i * math.pi / 2)
        surf = pygame.Surface((44, 44), pygame.SRCALPHA)
        cx, base = 22, 36
        rw = int(16 * pulse)
        pygame.draw.ellipse(surf, (180, 140, 80), (cx - rw, base - 22, rw * 2, 18))
        pygame.draw.rect(surf, (160, 120, 70), (cx - 10, base - 30, 20, 14))
        pygame.draw.circle(surf, (220, 180, 100), (cx - 5, base - 26), 3)
        pygame.draw.circle(surf, (220, 180, 100), (cx + 5, base - 26), 3)
        pygame.draw.rect(surf, (140, 100, 60), (cx - 18, base - 14, 8, 12))
        pygame.draw.rect(surf, (140, 100, 60), (cx + 10, base - 14, 8, 12))
        frames.append(surf)
    return frames


_SKILL_ICON_CACHE = {}


def _skill_scale(size):
    return size / 32.0


def _draw_skill_symbol(surface, icon_type, color, size, cursed=False):
    cx, cy = size // 2, size // 2
    s = _skill_scale(size)
    dark = tuple(max(0, c - 80) for c in color)
    light = tuple(min(255, c + 50) for c in color)
    icon = icon_type or "star"

    if icon == "blade" or icon == "sharp_blade":
        pygame.draw.line(surface, dark, (cx - int(10 * s), cy + int(8 * s)), (cx + int(10 * s), cy - int(10 * s)), max(2, int(3 * s)))
        pygame.draw.line(surface, light, (cx - int(8 * s), cy + int(6 * s)), (cx + int(8 * s), cy - int(8 * s)), max(1, int(2 * s)))
        pygame.draw.rect(surface, color, (cx + int(4 * s), cy - int(12 * s), int(4 * s), int(5 * s)))
    elif icon == "heart":
        points = []
        for deg in range(0, 360, 12):
            rad = math.radians(deg)
            x = 16 * (math.sin(rad) ** 3)
            y = -(13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad))
            points.append((int(cx + x * s), int(cy + y * s - 2 * s)))
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, light, points, max(1, int(1 * s)))
    elif icon == "boot":
        pygame.draw.ellipse(surface, color, (cx - int(8 * s), cy - int(4 * s), int(10 * s), int(8 * s)))
        pygame.draw.rect(surface, dark, (cx - int(2 * s), cy - int(2 * s), int(8 * s), int(6 * s)), border_radius=int(2 * s))
        for i in range(3):
            pygame.draw.line(surface, light, (cx - int(10 * s) - i * int(3 * s), cy + int(2 * s)), (cx - int(4 * s) - i * int(3 * s), cy + int(2 * s)), max(1, int(2 * s)))
    elif icon == "blood":
        pygame.draw.circle(surface, color, (cx, cy + int(2 * s)), int(7 * s))
        pygame.draw.circle(surface, light, (cx - int(2 * s), cy - int(1 * s)), int(2 * s))
    elif icon == "fang":
        pygame.draw.polygon(surface, color, [(cx, cy - int(8 * s)), (cx - int(8 * s), cy + int(6 * s)), (cx + int(8 * s), cy + int(6 * s))])
        pygame.draw.line(surface, (240, 240, 255), (cx - int(3 * s), cy - int(2 * s)), (cx - int(1 * s), cy + int(2 * s)), max(1, int(2 * s)))
        pygame.draw.line(surface, (240, 240, 255), (cx + int(3 * s), cy - int(2 * s)), (cx + int(1 * s), cy + int(2 * s)), max(1, int(2 * s)))
    elif icon == "thorn":
        for ox, oy in ((-6, 4), (0, -6), (6, 4)):
            pts = [(cx + int(ox * s), cy + int(oy * s)), (cx + int((ox - 3) * s), cy + int((oy + 6) * s)), (cx + int((ox + 3) * s), cy + int((oy + 6) * s))]
            pygame.draw.polygon(surface, color, pts)
    elif icon == "coin":
        pygame.draw.circle(surface, color, (cx, cy), int(8 * s))
        pygame.draw.circle(surface, dark, (cx, cy), int(8 * s), max(1, int(2 * s)))
        font = pygame.font.SysFont("Arial", max(8, int(10 * s)), bold=True)
        label = font.render("G", True, dark)
        surface.blit(label, label.get_rect(center=(cx, cy + int(1 * s))))
    elif icon == "flask":
        pygame.draw.rect(surface, (180, 180, 200), (cx - int(3 * s), cy - int(10 * s), int(6 * s), int(4 * s)), border_radius=int(1 * s))
        pygame.draw.ellipse(surface, (190, 195, 215), (cx - int(7 * s), cy - int(6 * s), int(14 * s), int(14 * s)))
        pygame.draw.ellipse(surface, color, (cx - int(5 * s), cy - int(2 * s), int(10 * s), int(8 * s)))
    elif icon == "bolt":
        bolt = [(cx + int(2 * s), cy - int(10 * s)), (cx - int(4 * s), cy + int(1 * s)), (cx + int(1 * s), cy + int(1 * s)), (cx - int(2 * s), cy + int(10 * s)), (cx + int(6 * s), cy - int(1 * s)), (cx + int(1 * s), cy - int(1 * s))]
        pygame.draw.polygon(surface, color, bolt)
        pygame.draw.polygon(surface, light, bolt, max(1, int(1 * s)))
    elif icon == "dash":
        pygame.draw.ellipse(surface, (*color, 160), (cx - int(10 * s), cy - int(4 * s), int(14 * s), int(10 * s)))
        pygame.draw.circle(surface, color, (cx + int(2 * s), cy - int(2 * s)), int(5 * s))
        pygame.draw.line(surface, light, (cx - int(10 * s), cy + int(4 * s)), (cx - int(4 * s), cy + int(4 * s)), max(1, int(2 * s)))
    elif icon == "shield":
        pts = [(cx, cy - int(9 * s)), (cx + int(9 * s), cy - int(3 * s)), (cx + int(7 * s), cy + int(8 * s)), (cx - int(7 * s), cy + int(8 * s)), (cx - int(9 * s), cy - int(3 * s))]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.polygon(surface, light, pts, max(1, int(2 * s)))
        pygame.draw.line(surface, light, (cx, cy - int(5 * s)), (cx, cy + int(4 * s)), max(1, int(2 * s)))
    elif icon == "eye":
        pygame.draw.ellipse(surface, color, (cx - int(10 * s), cy - int(6 * s), int(20 * s), int(12 * s)))
        pygame.draw.circle(surface, (240, 240, 255), (cx, cy), int(4 * s))
        pygame.draw.circle(surface, dark, (cx, cy), int(2 * s))
    elif icon == "skull":
        pygame.draw.circle(surface, color, (cx, cy - int(2 * s)), int(7 * s))
        pygame.draw.rect(surface, color, (cx - int(6 * s), cy + int(2 * s), int(12 * s), int(6 * s)), border_radius=int(2 * s))
    elif icon == "curse":
        pygame.draw.polygon(surface, color, [(cx, cy - int(9 * s)), (cx - int(8 * s), cy + int(7 * s)), (cx + int(8 * s), cy + int(7 * s))])
        pygame.draw.line(surface, (240, 80, 90), (cx, cy - int(4 * s)), (cx, cy + int(4 * s)), max(1, int(2 * s)))
    elif icon == "bone":
        pygame.draw.line(surface, color, (cx - int(8 * s), cy + int(6 * s)), (cx + int(8 * s), cy - int(6 * s)), max(2, int(3 * s)))
    elif icon == "fire":
        pts = [(cx, cy - int(10 * s)), (cx - int(7 * s), cy + int(8 * s)), (cx, cy + int(4 * s)), (cx + int(7 * s), cy + int(8 * s))]
        pygame.draw.polygon(surface, color, pts)
    elif icon == "shadow":
        pygame.draw.ellipse(surface, (*color, 140), (cx - int(9 * s), cy - int(3 * s), int(18 * s), int(10 * s)))
    elif icon == "star":
        for i in range(5):
            ang = math.radians(-90 + i * 72)
            ox = cx + int(math.cos(ang) * 8 * s)
            oy = cy + int(math.sin(ang) * 8 * s)
            pygame.draw.line(surface, color, (cx, cy), (ox, oy), max(1, int(2 * s)))
    else:
        pygame.draw.circle(surface, color, (cx, cy), int(6 * s))

    if cursed:
        pygame.draw.line(surface, (255, 70, 90), (cx - int(8 * s), cy - int(8 * s)), (cx + int(8 * s), cy + int(8 * s)), max(1, int(2 * s)))


def create_skill_icon(skill_id, color, size=32, icon_type="star", cursed=False):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    radius = size // 2 - 2
    ring = (255, 80, 100) if cursed else color
    pygame.draw.circle(surf, (18, 20, 28, 230), (cx, cy), radius)
    pygame.draw.circle(surf, (*ring, 200), (cx, cy), radius, max(1, size // 16))
    shine = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(shine, (255, 255, 255, 35), (cx - radius // 3, cy - radius // 3), max(2, radius // 3))
    surf.blit(shine, (0, 0))
    _draw_skill_symbol(surf, icon_type, color, size, cursed)
    return surf


def get_skill_icon(skill_id, size=32):
    key = (skill_id, size)
    if key not in _SKILL_ICON_CACHE:
        from skill_catalog import SKILLS
        skill = SKILLS.get(skill_id, {})
        color = skill.get("color", (180, 180, 180))
        icon_type = skill.get("icon", "star")
        cursed = skill.get("cursed", False)
        _SKILL_ICON_CACHE[key] = create_skill_icon(skill_id, color, size, icon_type, cursed)
    return _SKILL_ICON_CACHE[key]


def clear_skill_icon_cache():
    _SKILL_ICON_CACHE.clear()

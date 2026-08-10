"""Ближний бой: прицеливание, конус удара, подсветка целей, урон по игроку."""

import math
import pygame

from collision import cached_line_of_sight


def deal_damage_to_player(player, amount):
    """Наносит игроку фиксированный целочисленный урон. Возвращает фактически снятые HP."""
    if amount <= 0 or player.invulnerable:
        return 0
    return player.apply_damage(amount)


def tick_contact_cooldown(enemy):
    timer = getattr(enemy, "contact_hit_timer", 0)
    if timer > 0:
        enemy.contact_hit_timer = timer - 1


def try_contact_hit(player, enemy, damage, cooldown_frames, can_see=True):
    """Контактный удар с пер-враговым кулдауном (не каждый кадр)."""
    if not (enemy.rect.colliderect(player.rect) and player.hp > 0 and can_see):
        return 0
    if player.invulnerable:
        return 0
    if getattr(enemy, "contact_hit_timer", 0) > 0:
        return 0
    dealt = deal_damage_to_player(player, damage)
    if dealt > 0:
        enemy.contact_hit_timer = cooldown_frames
        thorns = getattr(player, "thorn_damage", 0)
        if thorns > 0 and hasattr(enemy, "take_damage"):
            enemy.take_damage(thorns)
        extra = getattr(enemy, "on_contact_extra", None)
        if extra:
            extra(player)
    return dealt

ATTACK_ARC = math.radians(62)
SNAP_SCREEN_RADIUS = 56

_AIM_CONE_CACHE = {"size": None, "surface": None}
_SWING_SURF_CACHE = {"size": 0, "surface": None}


def _get_fullscreen_alpha_cache(cache, size):
    if cache["size"] != size or cache["surface"] is None:
        cache["size"] = size
        cache["surface"] = pygame.Surface(size, pygame.SRCALPHA)
    else:
        cache["surface"].fill((0, 0, 0, 0))
    return cache["surface"]


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def angle_to_facing(angle):
    dx = math.cos(angle)
    dy = math.sin(angle)
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    return "down" if dy > 0 else "up"


def facing_to_angle(facing):
    return {
        "right": 0.0,
        "down": math.pi / 2,
        "left": math.pi,
        "up": -math.pi / 2,
    }.get(facing, math.pi / 2)


def compute_aim_angle(player_rect, world_x, world_y):
    dx = world_x - player_rect.centerx
    dy = world_y - player_rect.centery
    if dx == 0 and dy == 0:
        return facing_to_angle("down")
    return math.atan2(dy, dx)


def target_in_attack_cone(player_rect, aim_angle, target_rect, attack_range, arc=ATTACK_ARC):
    dx = target_rect.centerx - player_rect.centerx
    dy = target_rect.centery - player_rect.centery
    dist_sq = dx * dx + dy * dy
    hit_padding = max(target_rect.width, target_rect.height) * 0.5
    max_dist = attack_range + hit_padding
    if dist_sq > max_dist * max_dist:
        return False
    if dist_sq <= 16 * 16:
        return True
    target_angle = math.atan2(dy, dx)
    diff = abs(normalize_angle(target_angle - aim_angle))
    return diff <= arc


def find_attack_targets(player, aim_angle, enemies_group, tilemap):
    targets = []
    px, py = player.rect.centerx, player.rect.centery
    scan_range = player.attack_range + 32
    scan_range_sq = scan_range * scan_range
    for enemy in enemies_group:
        ex, ey = enemy.rect.centerx, enemy.rect.centery
        dx, dy = ex - px, ey - py
        dist_sq = dx * dx + dy * dy
        if dist_sq > scan_range_sq:
            continue
        if not target_in_attack_cone(player.rect, aim_angle, enemy.rect, player.attack_range):
            continue
        if not cached_line_of_sight(player, player.rect, enemy.rect, tilemap):
            continue
        targets.append((dist_sq, enemy))
    targets.sort(key=lambda item: item[0])
    return [enemy for _, enemy in targets]


def preview_targets(player, aim_angle, enemies_group, tilemap):
    return find_attack_targets(player, aim_angle, enemies_group, tilemap)


def snap_aim_angle(player, mouse_world_x, mouse_world_y, enemies_group, camera, mouse_screen_pos):
    msx, msy = mouse_screen_pos
    best = None
    best_score = 999999

    for enemy in enemies_group:
        if enemy.rect.inflate(22, 22).collidepoint(int(mouse_world_x), int(mouse_world_y)):
            dx = enemy.rect.centerx - player.rect.centerx
            dy = enemy.rect.centery - player.rect.centery
            return math.atan2(dy, dx)

    for enemy in enemies_group:
        sx, sy = camera.apply_pos(enemy.rect.centerx, enemy.rect.centery)
        screen_dist = math.hypot(sx - msx, sy - msy)
        if screen_dist > SNAP_SCREEN_RADIUS:
            continue
        dx = enemy.rect.centerx - player.rect.centerx
        dy = enemy.rect.centery - player.rect.centery
        world_dist = math.hypot(dx, dy)
        if world_dist > player.attack_range + 24:
            continue
        score = screen_dist + world_dist * 0.12
        if score < best_score:
            best_score = score
            best = math.atan2(dy, dx)
    return best


def update_player_aim(player, mouse_world_x, mouse_world_y, enemies_group, camera, mouse_screen_pos):
    snapped = snap_aim_angle(player, mouse_world_x, mouse_world_y, enemies_group, camera, mouse_screen_pos)
    if snapped is not None:
        player.aim_angle = snapped
    else:
        player.aim_angle = compute_aim_angle(player.rect, mouse_world_x, mouse_world_y)


def _cone_points(cx, cy, aim_angle, radius, arc=ATTACK_ARC, segments=16):
    points = [(cx, cy)]
    start = aim_angle - arc
    end = aim_angle + arc
    for i in range(segments + 1):
        t = i / segments
        a = start + (end - start) * t
        points.append((cx + math.cos(a) * radius, cy + math.sin(a) * radius))
    return points


def draw_attack_aim(
    screen, camera, player, enemies_group=None, tilemap=None,
    can_attack=True, precomputed_targets=None,
):
    if player.is_dashing or player.hp <= 0:
        return

    cx, cy = camera.apply_pos(player.rect.centerx, player.rect.centery)
    if precomputed_targets is not None:
        targets = precomputed_targets
    elif enemies_group is not None and tilemap is not None:
        targets = preview_targets(player, player.aim_angle, enemies_group, tilemap)
    else:
        targets = []

    if can_attack and targets:
        cone_color = (60, 255, 140, 55)
        line_color = (120, 255, 180)
        tip_color = (180, 255, 200)
    elif can_attack:
        cone_color = (255, 210, 80, 45)
        line_color = (255, 220, 120)
        tip_color = (255, 240, 160)
    else:
        cone_color = (255, 90, 90, 40)
        line_color = (200, 100, 100)
        tip_color = (255, 140, 140)

    world_points = _cone_points(
        player.rect.centerx, player.rect.centery, player.aim_angle, player.attack_range
    )
    screen_points = [camera.apply_pos(x, y) for x, y in world_points]
    if len(screen_points) >= 3:
        cone_surf = _get_fullscreen_alpha_cache(_AIM_CONE_CACHE, screen.get_size())
        pygame.draw.polygon(cone_surf, cone_color, screen_points)
        pygame.draw.lines(cone_surf, (*line_color, 120), True, screen_points[1:], 2)
        screen.blit(cone_surf, (0, 0))

    end_x = player.rect.centerx + math.cos(player.aim_angle) * player.attack_range
    end_y = player.rect.centery + math.sin(player.aim_angle) * player.attack_range
    ex, ey = camera.apply_pos(end_x, end_y)
    pygame.draw.line(screen, line_color, (cx, cy), (ex, ey), 2)
    pygame.draw.circle(screen, tip_color, (ex, ey), 5)
    pygame.draw.circle(screen, (255, 255, 255), (ex, ey), 5, 1)

    if not can_attack and player.attack_cooldown > 0:
        max_cd = max(1, 25 - getattr(player, "attack_cooldown_bonus", 0))
        ratio = 1.0 - (player.attack_cooldown / max_cd)
        arc_rect = pygame.Rect(cx - 22, cy - 22, 44, 44)
        pygame.draw.arc(screen, (255, 120, 80), arc_rect, -math.pi / 2, -math.pi / 2 + math.pi * 2 * ratio, 3)

    for enemy in targets:
        pos = camera.apply(enemy)
        pygame.draw.rect(screen, (255, 80, 80), pos.inflate(8, 8), 2, border_radius=4)


def draw_crosshair(screen, mouse_pos, valid_target=False):
    mx, my = mouse_pos
    color = (255, 100, 100) if valid_target else (200, 240, 255)
    pygame.draw.line(screen, color, (mx - 10, my), (mx - 3, my), 2)
    pygame.draw.line(screen, color, (mx + 3, my), (mx + 10, my), 2)
    pygame.draw.line(screen, color, (mx, my - 10), (mx, my - 3), 2)
    pygame.draw.line(screen, color, (mx, my + 3), (mx, my + 10), 2)
    pygame.draw.circle(screen, color, (mx, my), 3, 1)


def draw_attack_swing(screen, camera, player, progress=1.0):
    from player_visuals import get_weapon_style

    style = get_weapon_style(getattr(player, "weapon_name", ""))
    cx, cy = camera.apply_pos(player.rect.centerx, player.rect.centery)
    radius = int(player.attack_range * (0.45 + 0.45 * progress))
    start = player.aim_angle - ATTACK_ARC * (0.35 + 0.65 * (1.0 - progress))
    end = player.aim_angle + ATTACK_ARC * (0.35 + 0.65 * progress)
    surf_size = radius * 2 + 16
    if _SWING_SURF_CACHE["size"] != surf_size or _SWING_SURF_CACHE["surface"] is None:
        _SWING_SURF_CACHE["size"] = surf_size
        _SWING_SURF_CACHE["surface"] = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    swing = _SWING_SURF_CACHE["surface"]
    swing.fill((0, 0, 0, 0))
    local_rect = swing.get_rect().inflate(-8, -8)
    outer = (*style["swing"], 160)
    inner = (*style["swing_hot"], 210)
    pygame.draw.arc(swing, outer, local_rect, start, end, 8)
    pygame.draw.arc(swing, inner, local_rect, start, end, 3)
    screen.blit(swing, (cx - radius - 8, cy - radius - 8))


def _sword_swing_offset(progress):
    if progress < 0.3:
        t = progress / 0.3
        return -1.15 + t * 0.25
    if progress < 0.62:
        t = (progress - 0.3) / 0.32
        return -0.9 + t * 1.75
    t = (progress - 0.62) / 0.38
    return 0.85 - t * 0.55


def draw_attack_sword_overlay(screen, camera, player):
    """Динамическое оружие по углу прицела во время атаки."""
    if not player.is_attacking:
        return
    from player_visuals import draw_weapon_strike, get_weapon_style

    style = get_weapon_style(getattr(player, "weapon_name", ""))
    progress = player.swing_progress()
    cx, cy = camera.apply_pos(player.rect.centerx, player.rect.centery)
    sword_angle = player.aim_angle + _sword_swing_offset(progress)
    draw_weapon_strike(screen, cx, cy, sword_angle, style, progress)

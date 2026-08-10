import math
import random
import pygame

from config import PLAYER_COLLISION_INSET, ENEMY_COLLISION_INSET

_LOS_PROBE = pygame.Rect(0, 0, 8, 8)


def _inset_for(sprite):
    return getattr(sprite, "collision_inset", PLAYER_COLLISION_INSET)


def get_collision_rect(sprite):
    left, top, width, height = _inset_for(sprite)
    return pygame.Rect(sprite.rect.x + left, sprite.rect.y + top, width, height)


def set_collision_rect(sprite, body_rect):
    left, top, _, _ = _inset_for(sprite)
    sprite.rect.x = body_rect.x - left
    sprite.rect.y = body_rect.y - top


def rect_blocked(rect, tilemap):
    return tilemap.rect_hits_blocking(rect)


def has_line_of_sight(from_rect, to_rect, tilemap, step=12):
    dx = to_rect.centerx - from_rect.centerx
    dy = to_rect.centery - from_rect.centery
    dist_sq = dx * dx + dy * dy
    step_sq = step * step
    if dist_sq <= step_sq:
        return True

    dist = math.sqrt(dist_sq)
    steps = max(int(dist // step), 1)
    for i in range(1, steps):
        t = i / steps
        x = from_rect.centerx + dx * t
        y = from_rect.centery + dy * t
        _LOS_PROBE.x = int(x - 4)
        _LOS_PROBE.y = int(y - 4)
        if rect_blocked(_LOS_PROBE, tilemap):
            return False
    return True


def cached_line_of_sight(entity, from_rect, to_rect, tilemap, ttl=10):
    """Кэш LOS на несколько кадров — сильно снижает число raycast при большом количестве мобов."""
    tick = getattr(tilemap, "los_tick", 0)
    target_key = (to_rect.centerx // 24, to_rect.centery // 24)
    cache = getattr(entity, "_los_cache", None)
    if cache and cache[0] == tick and cache[1] == target_key:
        return cache[2]
    result = has_line_of_sight(from_rect, to_rect, tilemap)
    entity._los_cache = (tick, target_key, result)
    return result


def attack_can_hit(attacker_rect, attack_rect, target_rect, tilemap):
    if not attack_rect.colliderect(target_rect):
        return False
    if rect_blocked(attack_rect, tilemap):
        return False
    return has_line_of_sight(attacker_rect, target_rect, tilemap)


def _resolve_obstacle_axis(sprite, tilemap, axis):
    body = get_collision_rect(sprite)
    for block_rect in tilemap.get_blocking_rects_touching(body):
        if not body.colliderect(block_rect):
            continue
        if axis == "x":
            if body.centerx < block_rect.centerx:
                body.right = block_rect.left
            else:
                body.left = block_rect.right
        else:
            if body.centery < block_rect.centery:
                body.bottom = block_rect.top
            else:
                body.top = block_rect.bottom
    set_collision_rect(sprite, body)


def _try_move(sprite, move_x, move_y, tilemap, order):
    start = get_collision_rect(sprite)
    set_collision_rect(sprite, start.copy())

    if order == "xy":
        axes = (("x", move_x), ("y", move_y))
    else:
        axes = (("y", move_y), ("x", move_x))

    for axis, delta in axes:
        if not delta:
            continue
        body = get_collision_rect(sprite)
        if axis == "x":
            body.x += delta
        else:
            body.y += delta
        set_collision_rect(sprite, body)
        _resolve_obstacle_axis(sprite, tilemap, axis)

    end = get_collision_rect(sprite)
    target_x = start.x + move_x
    target_y = start.y + move_y
    return math.hypot(end.x - target_x, end.y - target_y)


def move_and_collide(sprite, dx, dy, tilemap):
    if not hasattr(sprite, "_rem_x"):
        sprite._rem_x = 0.0
        sprite._rem_y = 0.0

    sprite._rem_x += dx
    sprite._rem_y += dy
    move_x = int(sprite._rem_x)
    move_y = int(sprite._rem_y)
    sprite._rem_x -= move_x
    sprite._rem_y -= move_y

    if move_x == 0 and move_y == 0:
        return

    start = get_collision_rect(sprite)
    target_x = start.x + move_x
    target_y = start.y + move_y
    primary = "xy" if abs(move_x) >= abs(move_y) else "yx"
    secondary = "yx" if primary == "xy" else "xy"

    set_collision_rect(sprite, start.copy())
    _try_move(sprite, move_x, move_y, tilemap, primary)
    end = get_collision_rect(sprite)
    if abs(end.x - target_x) > 0 or abs(end.y - target_y) > 0:
        set_collision_rect(sprite, start.copy())
        _try_move(sprite, move_x, move_y, tilemap, secondary)


def separate_from_entities(sprite, others, padding=2):
    moved = False
    body = get_collision_rect(sprite)
    for other in others:
        if other is sprite:
            continue
        other_body = get_collision_rect(other)
        if not body.colliderect(other_body):
            continue

        dx = body.centerx - other_body.centerx
        dy = body.centery - other_body.centery
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 1])

        overlap_x = (body.width + other_body.width) // 2 + padding - abs(dx)
        overlap_y = (body.height + other_body.height) // 2 + padding - abs(dy)
        if overlap_x <= 0 or overlap_y <= 0:
            continue

        if overlap_x < overlap_y:
            push = int(overlap_x / 2) + 1
            body.x += push if dx >= 0 else -push
        else:
            push = int(overlap_y / 2) + 1
            body.y += push if dy >= 0 else -push
        moved = True

    if moved:
        set_collision_rect(sprite, body)
    return moved


def apply_directional_knockback(sprite, origin_x, origin_y, force, tilemap, resist=0.0):
    """Сдвигает спрайт от точки origin (например, от удара меча)."""
    effective = force * (1.0 - max(0.0, min(1.0, float(resist))))
    if effective < 0.5:
        return
    body = get_collision_rect(sprite)
    dx = body.centerx - origin_x
    dy = body.centery - origin_y
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        dx, dy = 1.0, 0.0
    else:
        dx /= dist
        dy /= dist
    move_and_collide(sprite, dx * effective, dy * effective, tilemap)


def separate_player_from_enemies(player, enemies, tilemap, padding=3):
    if separate_from_entities(player, enemies, padding=padding):
        _resolve_obstacle_axis(player, tilemap, "x")
        _resolve_obstacle_axis(player, tilemap, "y")


def resolve_group_separation(group, tilemap, iterations=2, padding=2):
    sprites = group.sprites() if hasattr(group, "sprites") else list(group)
    count = len(sprites)
    if count == 0:
        return
    if count > 85:
        return
    if count > 45:
        iterations = 1
    cell = 48
    for _ in range(iterations):
        grid = {}
        for sprite in sprites:
            body = get_collision_rect(sprite)
            key = (body.centerx // cell, body.centery // cell)
            grid.setdefault(key, []).append(sprite)
        for sprite in sprites:
            body = get_collision_rect(sprite)
            cx, cy = body.centerx // cell, body.centery // cell
            neighbors = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    bucket = grid.get((cx + dx, cy + dy))
                    if bucket:
                        neighbors.extend(bucket)
            separate_from_entities(sprite, neighbors, padding=padding)
            _resolve_obstacle_axis(sprite, tilemap, "x")
            _resolve_obstacle_axis(sprite, tilemap, "y")


def separation_force(sprite, others, radius=28, strength=1.2):
    force_x = 0.0
    force_y = 0.0
    body = get_collision_rect(sprite)
    radius_sq = radius * radius
    for other in others:
        if other is sprite:
            continue
        other_body = get_collision_rect(other)
        dx = body.centerx - other_body.centerx
        dy = body.centery - other_body.centery
        dist_sq = dx * dx + dy * dy
        if dist_sq <= 0 or dist_sq > radius_sq:
            continue
        dist = math.sqrt(dist_sq)
        weight = (radius - dist) / radius
        force_x += (dx / dist) * weight * strength
        force_y += (dy / dist) * weight * strength
    return force_x, force_y


def steer_velocity(current_x, current_y, target_x, target_y, speed, sep_x, sep_y):
    dx = target_x - current_x
    dy = target_y - current_y
    dist = math.hypot(dx, dy)
    if dist > 0:
        dx = (dx / dist) * speed + sep_x
        dy = (dy / dist) * speed + sep_y
    else:
        dx, dy = sep_x, sep_y

    final_dist = math.hypot(dx, dy)
    if final_dist > speed and final_dist > 0:
        dx = dx / final_dist * speed
        dy = dy / final_dist * speed
    return dx, dy


def assign_default_collision_inset(sprite, is_player=False):
    sprite.collision_inset = PLAYER_COLLISION_INSET if is_player else ENEMY_COLLISION_INSET

"""Зоны сложности на карте — от центра к краям и по биомам."""
from config import PLAZA_MIN, PLAZA_MAX

ZONE_LABELS = (
    "I — Тихая опушка",
    "II — Лесная граница",
    "III — Опасные земли",
    "IV — Кровавые просторы",
    "V — Проклятые земли",
    "VI — Сердце тьмы",
)

BIOME_TIER_BASE = {
    "forest": 0,
    "snow": 1,
    "desert": 2,
    "ruins": 3,
}

PLAZA_CENTER_X = (PLAZA_MIN + PLAZA_MAX) // 2
PLAZA_CENTER_Y = (PLAZA_MIN + PLAZA_MAX) // 2


def zone_tier_at(gx, gy, biome="forest"):
    """Сложность зоны: 0 (легко) … 5 (очень сложно)."""
    if PLAZA_MIN <= gx <= PLAZA_MAX and PLAZA_MIN <= gy <= PLAZA_MAX:
        return 0

    dist = max(abs(gx - PLAZA_CENTER_X), abs(gy - PLAZA_CENTER_Y))
    if dist < 15:
        local = 0
    elif dist < 35:
        local = 1
    elif dist < 55:
        local = 2
    else:
        local = 3

    base = BIOME_TIER_BASE.get(biome, 0)
    return max(0, min(5, local + base))


def zone_label(tier):
    return ZONE_LABELS[min(max(0, tier), len(ZONE_LABELS) - 1)]


def zone_stat_multiplier(tier):
    return 1.0 + tier * 0.11


def wolf_spawn_chance(tier):
    if tier <= 0:
        return 0.0
    if tier == 1:
        return 0.12
    if tier == 2:
        return 0.28
    if tier == 3:
        return 0.42
    return 0.58


def desert_allows_boss(tier):
    return tier >= 4


def desert_min_spawn_tier():
    return 1

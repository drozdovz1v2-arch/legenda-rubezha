"""Каталог из 250 roguelike-скиллов: бонусы, проклятия и риск/награда."""

import random

SKILL_TARGET_COUNT = 250

# --- Имена и цвета ---
POSITIVE_ADJECTIVES = [
    "Острый", "Быстрый", "Живучий", "Древний", "Священный", "Яростный", "Тихий",
    "Молниеносный", "Стальной", "Золотой", "Ледяной", "Пылающий", "Теневой",
    "Благородный", "Дикий", "Хитрый", "Непоколебимый", "Ясный", "Могучий", "Ловкий",
    "Кровавый", "Светлый", "Глубокий", "Резкий", "Верный", "Суровый", "Безумный",
    "Холодный", "Рунический", "Безупречный", "Свирепый", "Небесный", "Подземный",
]

CURSE_ADJECTIVES = [
    "Проклятый", "Гнилой", "Хрупкий", "Слепой", "Жадный", "Ленивый", "Тяжёлый",
    "Рваный", "Мёртвый", "Тусклый", "Кровоточащий", "Голодный", "Зловещий",
    "Обречённый", "Сломанный", "Гневный", "Пустой", "Истощённый", "Глубокий",
    "Шипастый", "Кислотный", "Мрачный", "Забытый", "Ржавый", "Трещинный",
]

NOUNS = [
    "клинок", "дух", "путь", "дар", "обет", "шрам", "пульс", "клык", "щит",
    "глаз", "шаг", "жажда", "печать", "корень", "огонь", "лед", "шип", "коготь",
    "сердце", "пепел", "ритуал", "камень", "ветер", "яд", "свет", "тьма", "кровь",
    "знак", "кость", "пламень", "пыль", "гром", "шёпот", "кольцо", "цепь",
]

RARITY_COLORS = {
    "common": (180, 190, 200),
    "uncommon": (90, 210, 130),
    "rare": (100, 160, 255),
    "epic": (210, 120, 255),
    "cursed": (200, 60, 80),
}

ICON_BY_STAT = {
    "skill_attack_bonus": "blade",
    "max_hp": "heart",
    "speed_mult": "boot",
    "on_kill_heal": "blood",
    "on_kill_damage": "skull",
    "lifesteal": "fang",
    "life_drain": "curse",
    "thorns": "thorn",
    "thorn_self": "bone",
    "gold_mult": "coin",
    "exp_mult": "eye",
    "potion_bonus": "flask",
    "potion_mult": "flask",
    "attack_cd_bonus": "bolt",
    "attack_cd_penalty": "bolt",
    "dash_cd_bonus": "dash",
    "dash_cd_penalty": "dash",
    "damage_reduction": "shield",
    "damage_taken": "curse",
    "crit_chance": "star",
    "crit_damage": "star",
    "attack_range": "blade",
    "dash_speed": "dash",
    "dash_iframes_penalty": "shadow",
    "hp_regen": "heart",
    "self_damage_on_attack": "fire",
    "enemy_aggro": "eye",
}

# Шаблоны эффектов: (stat, base_delta, desc_fmt, cursed)
EFFECT_TEMPLATES = [
    ("skill_attack_bonus", 4, "{sign}{v} к урону атаки", False),
    ("skill_attack_bonus", -3, "{sign}{v} к урону атаки", True),
    ("max_hp", 14, "{sign}{v} к макс. HP", False),
    ("max_hp", -12, "{sign}{v} к макс. HP", True),
    ("speed_mult", 0.07, "{sign}{v:.0%} к скорости", False),
    ("speed_mult", -0.08, "{sign}{v:.0%} к скорости", True),
    ("on_kill_heal", 3, "+{v} HP за убийство", False),
    ("on_kill_damage", 2, "−{v} HP за каждое убийство", True),
    ("lifesteal", 0.05, "+{v:.0%} вампиризма", False),
    ("life_drain", 0.04, "−{v:.0%} HP от нанесённого урона", True),
    ("thorns", 2, "+{v} урона атакующим", False),
    ("thorn_self", 1, "−{v} HP при получении удара", True),
    ("gold_mult", 0.22, "+{v:.0%} золота", False),
    ("gold_mult", -0.15, "−{v:.0%} золота", True),
    ("exp_mult", 0.14, "+{v:.0%} опыта", False),
    ("exp_mult", -0.10, "−{v:.0%} опыта", True),
    ("potion_bonus", 10, "+{v} HP от зелий", False),
    ("potion_mult", -0.18, "−{v:.0%} эффект зелий", True),
    ("attack_cd_bonus", 3, "атака быстрее (−{v} кадр)", False),
    ("attack_cd_penalty", 4, "атака медленнее (+{v} кадр)", True),
    ("dash_cd_bonus", 7, "рывок быстрее (−{v} кадр)", False),
    ("dash_cd_penalty", 6, "рывок медленнее (+{v} кадр)", True),
    ("damage_reduction", 0.05, "−{v:.0%} получаемого урона", False),
    ("damage_taken", 0.08, "+{v:.0%} получаемого урона", True),
    ("crit_chance", 0.04, "+{v:.0%} шанс крита", False),
    ("crit_chance", -0.03, "−{v:.0%} шанс крита", True),
    ("crit_damage", 0.25, "+{v:.0%} урон крита", False),
    ("crit_damage", -0.20, "−{v:.0%} урон крита", True),
    ("attack_range", 6, "+{v} дальность атаки", False),
    ("attack_range", -5, "−{v} дальность атаки", True),
    ("dash_speed", 2, "+{v} скорость рывка", False),
    ("dash_speed", -1, "−{v} скорость рывка", True),
    ("dash_iframes_penalty", 1, "−{v} кадр неуязвимости рывка", True),
    ("hp_regen", 1.2, "+{v:.1f} HP/сек", False),
    ("hp_regen", -1.0, "−{v:.1f} HP/сек (кровотечение)", True),
    ("self_damage_on_attack", 2, "−{v} HP при каждой атаке", True),
    ("enemy_aggro", 0.10, "враги замечают на +{v:.0%} дальше", True),
]

# Классические 12 скиллов (совместимость)
LEGACY_SKILLS = {
    "sharp_blade": {
        "name": "Острый клинок",
        "desc": "+5 к урону атаки",
        "color": (255, 170, 70),
        "max_stacks": 5,
        "rarity": "common",
        "cursed": False,
        "icon": "blade",
        "effects": [("skill_attack_bonus", 5)],
    },
    "vitality": {
        "name": "Живучесть",
        "desc": "+12 макс. HP и исцеление",
        "color": (255, 90, 90),
        "max_stacks": 8,
        "rarity": "common",
        "cursed": False,
        "icon": "heart",
        "effects": [("max_hp", 12)],
    },
    "swift_feet": {
        "name": "Быстрые ноги",
        "desc": "+8% скорости передвижения",
        "color": (120, 255, 160),
        "max_stacks": 4,
        "rarity": "common",
        "cursed": False,
        "icon": "boot",
        "effects": [("speed_mult", 0.08)],
    },
    "bloodlust": {
        "name": "Кровожадность",
        "desc": "+3 HP за каждое убийство",
        "color": (200, 40, 60),
        "max_stacks": 5,
        "rarity": "uncommon",
        "cursed": False,
        "icon": "blood",
        "effects": [("on_kill_heal", 3)],
    },
    "vampire": {
        "name": "Вампиризм",
        "desc": "+6% вампиризма от урона",
        "color": (180, 50, 120),
        "max_stacks": 4,
        "rarity": "rare",
        "cursed": False,
        "icon": "fang",
        "effects": [("lifesteal", 0.06)],
    },
    "thorns": {
        "name": "Шипы",
        "desc": "+2 урона атакующим вблизи",
        "color": (140, 200, 80),
        "max_stacks": 5,
        "rarity": "uncommon",
        "cursed": False,
        "icon": "thorn",
        "effects": [("thorns", 2)],
    },
    "greedy": {
        "name": "Жадность",
        "desc": "+30% золота с врагов",
        "color": (255, 215, 0),
        "max_stacks": 4,
        "rarity": "uncommon",
        "cursed": False,
        "icon": "coin",
        "effects": [("gold_mult", 0.30)],
    },
    "alchemist": {
        "name": "Алхимик",
        "desc": "Зелья лечат на +12 HP",
        "color": (220, 80, 200),
        "max_stacks": 3,
        "rarity": "rare",
        "cursed": False,
        "icon": "flask",
        "effects": [("potion_bonus", 12)],
    },
    "haste": {
        "name": "Спешка",
        "desc": "Атака перезаряжается быстрее",
        "color": (100, 200, 255),
        "max_stacks": 4,
        "rarity": "uncommon",
        "cursed": False,
        "icon": "bolt",
        "effects": [("attack_cd_bonus", 4)],
    },
    "phantom_dash": {
        "name": "Фантомный рывок",
        "desc": "Рывок [Shift] — короче откат",
        "color": (160, 140, 255),
        "max_stacks": 3,
        "rarity": "rare",
        "cursed": False,
        "icon": "dash",
        "effects": [("dash_cd_bonus", 8)],
    },
    "iron_skin": {
        "name": "Железная кожа",
        "desc": "−6% получаемого урона",
        "color": (160, 170, 190),
        "max_stacks": 4,
        "rarity": "uncommon",
        "cursed": False,
        "icon": "shield",
        "effects": [("damage_reduction", 0.06)],
    },
    "keen_eye": {
        "name": "Острый глаз",
        "desc": "+15% опыта с врагов",
        "color": (190, 130, 255),
        "max_stacks": 4,
        "rarity": "uncommon",
        "cursed": False,
        "icon": "eye",
        "effects": [("exp_mult", 0.15)],
    },
}


def _format_desc(template, value):
    v = abs(value)
    sign = "+" if value >= 0 else "−"
    try:
        return template.format(v=v, sign=sign)
    except (ValueError, KeyError):
        return template.replace("{v}", str(int(v))).replace("{sign}", sign)


def _scale_delta(base, tier, cursed):
    mult = 1.0 + tier * 0.12
    if cursed:
        mult *= 1.05
    if isinstance(base, float):
        return round(base * mult, 3)
    return max(1, int(round(base * mult)))


def _pick_rarity(cursed, tier, rng):
    if cursed:
        return "cursed"
    if tier >= 7:
        return rng.choice(["epic", "rare", "rare"])
    if tier >= 4:
        return rng.choice(["rare", "uncommon", "uncommon"])
    if tier >= 2:
        return rng.choice(["uncommon", "common", "common"])
    return "common"


def _build_generated_catalog():
    rng = random.Random(20260802)
    skills = dict(LEGACY_SKILLS)
    used_names = {s["name"] for s in skills.values()}
    idx = 0

    while len(skills) < SKILL_TARGET_COUNT:
        stat, base_delta, desc_tpl, cursed = rng.choice(EFFECT_TEMPLATES)
        tier = rng.randint(0, 8)
        delta = _scale_delta(base_delta, tier, cursed)
        if delta == 0:
            continue

        adj_pool = CURSE_ADJECTIVES if cursed else POSITIVE_ADJECTIVES
        for _ in range(12):
            name = f"{rng.choice(adj_pool)} {rng.choice(NOUNS)}"
            if name not in used_names:
                used_names.add(name)
                break
        else:
            name = f"{rng.choice(adj_pool)} {rng.choice(NOUNS)} {idx}"

        rarity = _pick_rarity(cursed, tier, rng)
        max_stacks = rng.randint(2, 6)
        if rarity in ("rare", "epic"):
            max_stacks = max(2, max_stacks - 1)
        if cursed:
            max_stacks = rng.randint(3, 7)

        skill_id = f"gen_{idx:03d}"
        idx += 1
        color = RARITY_COLORS[rarity]
        if cursed:
            color = (
                min(255, color[0] + rng.randint(0, 30)),
                max(30, color[1] - rng.randint(0, 40)),
                max(40, color[2] - rng.randint(0, 30)),
            )

        skills[skill_id] = {
            "name": name,
            "desc": _format_desc(desc_tpl, delta),
            "color": color,
            "max_stacks": max_stacks,
            "rarity": rarity,
            "cursed": cursed,
            "icon": ICON_BY_STAT.get(stat, "star"),
            "effects": [(stat, delta)],
        }

    return skills


SKILLS = _build_generated_catalog()

# Проверка при импорте
assert len(SKILLS) == SKILL_TARGET_COUNT, f"Expected {SKILL_TARGET_COUNT} skills, got {len(SKILLS)}"

CURSED_SKILL_IDS = [sid for sid, s in SKILLS.items() if s.get("cursed")]
BLESSING_SKILL_IDS = [sid for sid, s in SKILLS.items() if not s.get("cursed")]

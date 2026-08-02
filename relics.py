"""Реликвии — пассивные артефакты, собираемые за забег (до 8)."""

import random

RELICS = {
    "blood_vial": {"name": "Фиал крови", "desc": "+4% вампиризма", "color": (200, 40, 60), "effect": ("lifesteal", 0.04), "rarity": "common"},
    "thorn_charm": {"name": "Шипастый амулет", "desc": "+3 урона шипам", "color": (140, 200, 80), "effect": ("thorns", 3), "rarity": "common"},
    "lucky_clover": {"name": "Клевер", "desc": "+12% золота", "color": (80, 200, 100), "effect": ("gold_mult", 0.12), "rarity": "common"},
    "swift_boots": {"name": "Быстрые сапоги", "desc": "+6% скорости", "color": (120, 255, 160), "effect": ("speed_mult", 0.06), "rarity": "common"},
    "iron_ring": {"name": "Железное кольцо", "desc": "−4% получаемого урона", "color": (160, 170, 190), "effect": ("damage_reduction", 0.04), "rarity": "common"},
    "exp_orb": {"name": "Сфера знаний", "desc": "+10% опыта", "color": (190, 130, 255), "effect": ("exp_mult", 0.10), "rarity": "common"},
    "crit_lens": {"name": "Линза крита", "desc": "+5% шанс крита", "color": (255, 200, 80), "effect": ("crit_chance", 0.05), "rarity": "uncommon"},
    "giant_heart": {"name": "Сердце гиганта", "desc": "+18 макс. HP", "color": (255, 90, 90), "effect": ("max_hp", 18), "rarity": "uncommon"},
    "dash_crystal": {"name": "Кристалл рывка", "desc": "−6 кадр отката рывка", "color": (160, 140, 255), "effect": ("dash_cd_bonus", 6), "rarity": "uncommon"},
    "haste_gear": {"name": "Шестерня спешки", "desc": "−4 кадр атаки", "color": (100, 200, 255), "effect": ("attack_cd_bonus", 4), "rarity": "uncommon"},
    "poison_fang": {"name": "Ядовитый клык", "desc": "Атаки накладывают яд", "color": (120, 200, 60), "effect": ("attack_poison", 1), "rarity": "rare"},
    "frost_shard": {"name": "Осколок льда", "desc": "10% заморозить при ударе", "color": (130, 200, 255), "effect": ("attack_freeze", 0.10), "rarity": "rare"},
    "boss_hunter": {"name": "Охотник на боссов", "desc": "+15% урона по боссам", "color": (255, 120, 60), "effect": ("boss_damage", 0.15), "rarity": "rare"},
    "soul_gem": {"name": "Камень душ", "desc": "+25% душ с забега", "color": (180, 140, 255), "effect": ("soul_mult", 0.25), "rarity": "rare"},
    "phoenix_feather": {"name": "Перо феникса", "desc": "Один раз возродиться с 30% HP", "color": (255, 180, 80), "effect": ("revive", 1), "rarity": "epic"},
    "void_blade": {"name": "Клинок пустоты", "desc": "+8 урона", "color": (140, 80, 200), "effect": ("skill_attack_bonus", 8), "rarity": "epic"},
    "cursed_crown": {"name": "Проклятая корона", "desc": "+20% урона, −10% HP", "color": (200, 60, 80), "effect": ("glass", 1), "rarity": "cursed"},
    "combo_blade": {"name": "Клинок серии", "desc": "+5% комбо за удар", "color": (255, 140, 60), "effect": ("combo_bonus", 0.05), "rarity": "uncommon"},
    "merchant_seal": {"name": "Печать торговца", "desc": "−15% цены в магазине", "color": (255, 215, 0), "effect": ("shop_discount", 0.15), "rarity": "rare"},
    "night_eye": {"name": "Ночной глаз", "desc": "+8% урона ночью", "color": (100, 80, 160), "effect": ("night_damage", 0.08), "rarity": "uncommon"},
    "elite_trophy": {"name": "Трофей элиты", "desc": "+20% золота с элит", "color": (255, 190, 60), "effect": ("elite_gold", 0.20), "rarity": "rare"},
    "heal_spring": {"name": "Источник", "desc": "+0.8 HP/сек", "color": (80, 220, 160), "effect": ("hp_regen", 0.8), "rarity": "uncommon"},
    "range_scope": {"name": "Прицел", "desc": "+10 дальность атаки", "color": (180, 200, 220), "effect": ("attack_range", 10), "rarity": "common"},
    "mirror_shield": {"name": "Зеркальный щит", "desc": "+6% отражения урона", "color": (200, 220, 255), "effect": ("reflect", 0.06), "rarity": "epic"},
}

MAX_RELICS = 8
DROP_WEIGHTS = {"common": 50, "uncommon": 28, "rare": 14, "epic": 5, "cursed": 3}


class RelicManager:
    def __init__(self):
        self.collected = []
        self.revive_used = False
        self._applied = False

    def reset(self):
        self.collected = []
        self.revive_used = False
        self._applied = False

    def has(self, relic_id):
        return relic_id in self.collected

    def can_collect(self):
        return len(self.collected) < MAX_RELICS

    def add(self, relic_id, game=None, x=None, y=None):
        if relic_id in RELICS and relic_id not in self.collected and self.can_collect():
            self.collected.append(relic_id)
            if game and game.player:
                self._apply_one(relic_id, game.player)
            if game:
                game.quests._notify(f"Реликвия: {RELICS[relic_id]['name']}")
                game.audio.play_sfx("relic_pickup")
                fx = x if x is not None else game.player.rect.centerx
                fy = y if y is not None else game.player.rect.centery
                game.effects.trigger_relic_pickup(fx, fy)
            return True
        return False

    def _apply_one(self, relic_id, player):
        from skill_effects import apply_stat_delta
        relic = RELICS[relic_id]
        eff = relic["effect"]
        if eff[0] == "glass":
            apply_stat_delta(player, "skill_attack_bonus", 4)
            apply_stat_delta(player, "max_hp", -8)
        elif eff[0] == "attack_poison":
            player.relic_poison = True
        elif eff[0] == "attack_freeze":
            player.relic_freeze_chance = getattr(player, "relic_freeze_chance", 0) + eff[1]
        elif eff[0] == "boss_damage":
            player.relic_boss_damage = getattr(player, "relic_boss_damage", 0) + eff[1]
        elif eff[0] == "combo_bonus":
            player.relic_combo_bonus = getattr(player, "relic_combo_bonus", 0) + eff[1]
        elif eff[0] == "night_damage":
            player.relic_night_damage = getattr(player, "relic_night_damage", 0) + eff[1]
        elif eff[0] == "elite_gold":
            player.relic_elite_gold = getattr(player, "relic_elite_gold", 0) + eff[1]
        elif eff[0] == "reflect":
            player.relic_reflect = getattr(player, "relic_reflect", 0) + eff[1]
        elif eff[0] == "shop_discount":
            player.relic_shop_discount = getattr(player, "relic_shop_discount", 0) + eff[1]
        elif eff[0] == "soul_mult":
            player.relic_soul_mult = getattr(player, "relic_soul_mult", 0) + eff[1]
        elif eff[0] == "revive":
            player.relic_revive = True
        else:
            apply_stat_delta(player, eff[0], eff[1])

    def apply_all(self, player):
        if self._applied:
            return
        for rid in self.collected:
            self._apply_one(rid, player)
        self._applied = True

    def try_revive(self, player, game):
        if self.revive_used or not getattr(player, "relic_revive", False):
            return False
        if player.hp > 0:
            return False
        self.revive_used = True
        player.hp = max(1, int(player.max_hp * 0.30))
        player.grant_spawn_protection(120)
        game.quests._notify("Перо феникса — второй шанс!")
        game.effects.spawn_heal_burst(player.rect.centerx, player.rect.centery)
        return True

    def roll_drop(self, is_elite=False, is_boss=False, bonus=0.0):
        if is_boss and random.random() < 0.55 + bonus:
            pool = [k for k, v in RELICS.items() if v["rarity"] in ("rare", "epic")]
        elif is_elite and random.random() < 0.12 + bonus:
            pool = [k for k, v in RELICS.items() if v["rarity"] in ("common", "uncommon", "rare")]
        elif random.random() < 0.025 + bonus * 0.5:
            pool = [k for k, v in RELICS.items() if v["rarity"] == "common"]
        else:
            return None
        available = [r for r in pool if r not in self.collected]
        if not available:
            return None
        return random.choice(available)

    def to_dict(self):
        return {"collected": list(self.collected), "revive_used": self.revive_used}

    def load_dict(self, data):
        if not data:
            return
        self.collected = list(data.get("collected", []))
        self.revive_used = bool(data.get("revive_used", False))
        self._applied = False

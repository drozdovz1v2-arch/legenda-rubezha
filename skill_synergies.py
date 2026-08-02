"""Синергии скиллов — бонусы за комбинации стаков."""

from skill_catalog import SKILLS

SYNERGIES = [
    {
        "id": "vampire_lord",
        "name": "Повелитель крови",
        "desc": "Вампиризм + кровожадность: +8% вампиризма",
        "requires": {"vampire": 2, "bloodlust": 2},
        "effects": [("lifesteal", 0.08)],
    },
    {
        "id": "glass_assassin",
        "name": "Стеклянный убийца",
        "desc": "Острый клинок ×3: +10 урона, −8 HP",
        "requires": {"sharp_blade": 3},
        "effects": [("skill_attack_bonus", 10), ("max_hp", -8)],
    },
    {
        "id": "iron_fortress",
        "name": "Крепость",
        "desc": "Железная кожа + живучесть: −12% урона",
        "requires": {"iron_skin": 2, "vitality": 2},
        "effects": [("damage_reduction", 0.12)],
    },
    {
        "id": "greedy_scholar",
        "name": "Жадный учёный",
        "desc": "Жадность + острый глаз: +20% золота и опыта",
        "requires": {"greedy": 2, "keen_eye": 2},
        "effects": [("gold_mult", 0.20), ("exp_mult", 0.20)],
    },
    {
        "id": "phantom_warrior",
        "name": "Фантомный воин",
        "desc": "Рывок + спешка: −10 кадр откатов",
        "requires": {"phantom_dash": 2, "haste": 2},
        "effects": [("dash_cd_bonus", 5), ("attack_cd_bonus", 5)],
    },
    {
        "id": "cursed_power",
        "name": "Сила проклятия",
        "desc": "3+ проклятых скилла: +6 урона",
        "requires_cursed_stacks": 3,
        "effects": [("skill_attack_bonus", 6)],
    },
    {
        "id": "thorn_king",
        "name": "Король шипов",
        "desc": "Шипы ×4: +6 урона шипам",
        "requires": {"thorns": 4},
        "effects": [("thorns", 6)],
    },
    {
        "id": "speed_demon",
        "name": "Демон скорости",
        "desc": "Быстрые ноги ×3: +15% скорости",
        "requires": {"swift_feet": 3},
        "effects": [("speed_mult", 0.15)],
    },
    {
        "id": "alchemist_master",
        "name": "Мастер зелий",
        "desc": "Алхимик ×2: +20 HP от зелий",
        "requires": {"alchemist": 2},
        "effects": [("potion_bonus", 20), ("potion_mult", 0.15)],
    },
    {
        "id": "diverse_build",
        "name": "Универсал",
        "desc": "8+ разных скиллов: +5% ко всем статам",
        "requires_unique": 8,
        "effects": [("skill_attack_bonus", 3), ("max_hp", 10), ("exp_mult", 0.05)],
    },
]


class SynergyManager:
    def __init__(self):
        self.active = set()
        self._last_check = None

    def reset(self):
        self.active = set()
        self._last_check = None

    def _count_cursed_stacks(self, stacks):
        total = 0
        for sid, count in stacks.items():
            skill = SKILLS.get(sid, {})
            if skill.get("cursed"):
                total += count
        return total

    def evaluate(self, player):
        stacks = player.skill_stacks
        key = tuple(sorted(stacks.items()))
        if key == self._last_check:
            return list(self.active)
        self._last_check = key
        found = set()
        for syn in SYNERGIES:
            req = syn.get("requires")
            if req:
                ok = all(stacks.get(sid, 0) >= need for sid, need in req.items())
            elif syn.get("requires_cursed_stacks"):
                ok = self._count_cursed_stacks(stacks) >= syn["requires_cursed_stacks"]
            elif syn.get("requires_unique"):
                ok = len(stacks) >= syn["requires_unique"]
            else:
                ok = False
            if ok:
                found.add(syn["id"])
        new_syns = found - self.active
        self.active = found
        return list(new_syns)

    def on_stacks_changed(self, player, game):
        new_ids = self.evaluate(player)
        from skill_effects import apply_stat_delta
        for syn_id in new_ids:
            syn = next(s for s in SYNERGIES if s["id"] == syn_id)
            for stat, val in syn.get("effects", []):
                apply_stat_delta(player, stat, val)
            game.quests._notify(f"⚡ Синергия: {syn['name']}")
        return new_ids

    def reapply_after_load(self, player):
        self._last_check = None
        self.evaluate(player)
        from skill_effects import apply_stat_delta
        for syn in SYNERGIES:
            if syn["id"] not in self.active:
                continue
            for stat, val in syn.get("effects", []):
                apply_stat_delta(player, stat, val)
        names = []
        for syn in SYNERGIES:
            if syn["id"] in self.active:
                names.append(syn["name"])
        return names

    def to_dict(self):
        return {"active": list(self.active)}

    def load_dict(self, data):
        if not data:
            return
        self.active = set(data.get("active", []))
        self._last_check = None

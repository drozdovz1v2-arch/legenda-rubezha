"""Мета-прогресс — души героев и древо талантов между забегами."""

SAVE_VERSION = 2

TALENTS = {
    "iron_will": {
        "name": "Железная воля",
        "desc": "+8 стартовых HP каждый забег",
        "cost": 3,
        "max_rank": 5,
        "effect": ("start_hp", 8),
    },
    "sharp_start": {
        "name": "Острый старт",
        "desc": "+1 урон в начале забега",
        "cost": 4,
        "max_rank": 3,
        "effect": ("start_damage", 1),
    },
    "lucky_pouch": {
        "name": "Счастливый мешок",
        "desc": "+15 стартового золота",
        "cost": 2,
        "max_rank": 5,
        "effect": ("start_gold", 15),
    },
    "quick_feet_meta": {
        "name": "Проворство предков",
        "desc": "−8% откат рывка",
        "cost": 5,
        "max_rank": 3,
        "effect": ("dash_cd_bonus", 4),
    },
    "soul_harvest": {
        "name": "Жнец душ",
        "desc": "+10% душ с забега",
        "cost": 6,
        "max_rank": 4,
        "effect": ("soul_mult", 0.10),
    },
    "relic_seeker": {
        "name": "Искатель реликвий",
        "desc": "+5% шанс реликвии",
        "cost": 7,
        "max_rank": 3,
        "effect": ("relic_chance", 0.05),
    },
    "potion_belt": {
        "name": "Пояс алхимика",
        "desc": "+1 зелье в начале забега",
        "cost": 4,
        "max_rank": 2,
        "effect": ("start_potion", 1),
    },
    "curse_resist": {
        "name": "Сопротивление проклятиям",
        "desc": "Проклятые скиллы слабее на 15%",
        "cost": 8,
        "max_rank": 2,
        "effect": ("curse_resist", 0.15),
    },
    "veteran_exp": {
        "name": "Опыт ветерана",
        "desc": "+8% опыта навсегда",
        "cost": 5,
        "max_rank": 4,
        "effect": ("exp_mult", 0.08),
    },
    "night_vision": {
        "name": "Ночное зрение",
        "desc": "Меньше затемнения ночью",
        "cost": 3,
        "max_rank": 1,
        "effect": ("night_vision", 0.25),
    },
    "combo_master": {
        "name": "Мастер серий",
        "desc": "+3% множитель комбо за стак",
        "cost": 6,
        "max_rank": 3,
        "effect": ("combo_bonus", 0.03),
    },
    "boss_slayer": {
        "name": "Убийца боссов",
        "desc": "+12% урона по боссам",
        "cost": 9,
        "max_rank": 3,
        "effect": ("boss_damage", 0.12),
    },
}


class MetaProgression:
    def __init__(self):
        self.souls = 0
        self.talent_ranks = {}
        self.lifetime_runs = 0
        self.lifetime_kills = 0
        self.lifetime_deaths = 0
        self.best_level = 0
        self.best_kills = 0
        self.best_wave = 0
        self.total_souls_earned = 0

    def reset_session(self):
        pass

    def talent_rank(self, talent_id):
        return int(self.talent_ranks.get(talent_id, 0))

    def can_buy(self, talent_id):
        talent = TALENTS.get(talent_id)
        if not talent:
            return False
        rank = self.talent_rank(talent_id)
        if rank >= talent["max_rank"]:
            return False
        return self.souls >= talent["cost"]

    def buy_talent(self, talent_id):
        if not self.can_buy(talent_id):
            return False
        talent = TALENTS[talent_id]
        self.souls -= talent["cost"]
        self.talent_ranks[talent_id] = self.talent_rank(talent_id) + 1
        return True

    def stat_bonus(self, key, default=0):
        total = default
        for tid, talent in TALENTS.items():
            rank = self.talent_rank(tid)
            if rank <= 0:
                continue
            eff_key, eff_val = talent["effect"]
            if eff_key == key:
                total += eff_val * rank
        return total

    def apply_run_start(self, player):
        player.max_hp_skill_bonus += int(self.stat_bonus("start_hp", 0))
        player.recalc_max_hp()
        player.hp = player.max_hp
        player.weapon_base_damage += int(self.stat_bonus("start_damage", 0))
        player.recalc_attack_damage()
        player.gold += int(self.stat_bonus("start_gold", 0))
        player.potions_count += int(self.stat_bonus("start_potion", 0))
        player.dash_cooldown_bonus += int(self.stat_bonus("dash_cd_bonus", 0))
        player.exp_multiplier += float(self.stat_bonus("exp_mult", 0))

    def compute_run_souls(self, run_stats):
        level = run_stats.get("level", 1)
        kills = run_stats.get("kills", 0)
        wave = run_stats.get("wave", 1)
        relics = run_stats.get("relics", 0)
        quests = run_stats.get("quests_done", 0)
        base = 2 + level // 2 + kills // 8 + wave // 2 + relics * 2 + quests * 3
        mult = 1.0 + float(self.stat_bonus("soul_mult", 0))
        return max(1, int(base * mult))

    def record_run_end(self, run_stats, souls_earned):
        self.lifetime_runs += 1
        self.lifetime_deaths += 1
        self.lifetime_kills += run_stats.get("kills", 0)
        self.souls += souls_earned
        self.total_souls_earned += souls_earned
        self.best_level = max(self.best_level, run_stats.get("level", 1))
        self.best_kills = max(self.best_kills, run_stats.get("kills", 0))
        self.best_wave = max(self.best_wave, run_stats.get("wave", 1))

    def to_dict(self):
        return {
            "souls": self.souls,
            "talent_ranks": dict(self.talent_ranks),
            "lifetime_runs": self.lifetime_runs,
            "lifetime_kills": self.lifetime_kills,
            "lifetime_deaths": self.lifetime_deaths,
            "best_level": self.best_level,
            "best_kills": self.best_kills,
            "best_wave": self.best_wave,
            "total_souls_earned": self.total_souls_earned,
        }

    def load_dict(self, data):
        if not data:
            return
        self.souls = int(data.get("souls", 0))
        self.talent_ranks = dict(data.get("talent_ranks", {}))
        self.lifetime_runs = int(data.get("lifetime_runs", 0))
        self.lifetime_kills = int(data.get("lifetime_kills", 0))
        self.lifetime_deaths = int(data.get("lifetime_deaths", 0))
        self.best_level = int(data.get("best_level", 0))
        self.best_kills = int(data.get("best_kills", 0))
        self.best_wave = int(data.get("best_wave", 0))
        self.total_souls_earned = int(data.get("total_souls_earned", 0))

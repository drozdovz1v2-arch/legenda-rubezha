"""Достижения — награды за особые подвиги."""

ACHIEVEMENTS = {
    "first_blood": {
        "name": "Первая кровь",
        "desc": "Убей первого врага",
        "reward_gold": 10,
    },
    "combo_5": {
        "name": "Серия!",
        "desc": "Достигни комбо x5",
        "reward_gold": 25,
    },
    "combo_10": {
        "name": "Мастер комбо",
        "desc": "Достигни комбо x10",
        "reward_gold": 50,
    },
    "night_hunter": {
        "name": "Ночной охотник",
        "desc": "Убей 10 врагов ночью",
        "reward_gold": 30,
    },
    "elite_slayer": {
        "name": "Охотник на элит",
        "desc": "Убей 5 элитных врагов",
        "reward_gold": 40,
    },
    "ruins_explorer": {
        "name": "Исследователь руин",
        "desc": "Посети биом Руин",
        "reward_gold": 20,
    },
    "level_10": {
        "name": "Ветеран",
        "desc": "Достигни 10 уровня",
        "reward_gold": 75,
    },
    "colossus_down": {
        "name": "Разрушитель пустыни",
        "desc": "Победи Песчаный колосс",
        "reward_gold": 100,
    },
    "relic_collector": {
        "name": "Коллекционер",
        "desc": "Собери 5 реликвий за один забег",
        "reward_gold": 60,
    },
    "synergy_master": {
        "name": "Синергист",
        "desc": "Активируй 3 синергии",
        "reward_gold": 45,
    },
    "wave_15": {
        "name": "Выживший",
        "desc": "Достигни 15 волны угрозы",
        "reward_gold": 80,
    },
    "soul_hoarder": {
        "name": "Купец душ",
        "desc": "Накопи 50 душ (между забегами)",
        "reward_gold": 50,
    },
    "modifier_legend": {
        "name": "Легенда модификаторов",
        "desc": "Продержись до 6 волны на «Легенда»",
        "reward_gold": 120,
    },
    "kill_100": {
        "name": "Мясорубка",
        "desc": "100 убийств за один забег",
        "reward_gold": 70,
    },
    "no_death_dash": {
        "name": "Герой Рубежа",
        "desc": "Достигни 8 уровня за один забег",
        "reward_gold": 50,
    },
}


class AchievementManager:
    def __init__(self):
        self.unlocked = []
        self.toast = None
        self.night_kills = 0
        self.elite_kills = 0
        self.visited_ruins = False

    def reset(self):
        self.unlocked = []
        self.toast = None
        self.night_kills = 0
        self.elite_kills = 0
        self.visited_ruins = False

    def unlock(self, achievement_id, game):
        if achievement_id in self.unlocked or achievement_id not in ACHIEVEMENTS:
            return
        self.unlocked.append(achievement_id)
        ach = ACHIEVEMENTS[achievement_id]
        reward = ach.get("reward_gold", 0)
        if reward:
            game.player.gold += reward
        self.toast = {"text": f"Достижение: {ach['name']}", "timer": 240}
        if reward:
            game.quests._notify(f"★ {ach['name']} (+{reward} золота)")
        else:
            game.quests._notify(f"★ {ach['name']}")

    def update(self, game):
        if self.toast:
            self.toast["timer"] -= 1
            if self.toast["timer"] <= 0:
                self.toast = None

        if game.session_kills >= 1:
            self.unlock("first_blood", game)
        if game.combo.peak >= 5:
            self.unlock("combo_5", game)
        if game.combo.peak >= 10:
            self.unlock("combo_10", game)
        if self.night_kills >= 10:
            self.unlock("night_hunter", game)
        if self.elite_kills >= 5:
            self.unlock("elite_slayer", game)
        if self.visited_ruins:
            self.unlock("ruins_explorer", game)
        if game.player.level >= 10:
            self.unlock("level_10", game)
        if game.player.level >= 8:
            self.unlock("no_death_dash", game)
        if game.session_kills >= 100:
            self.unlock("kill_100", game)
        if game.difficulty.wave >= 15:
            self.unlock("wave_15", game)
        relics = getattr(game, "relics", None)
        if relics and len(relics.collected) >= 5:
            self.unlock("relic_collector", game)
        synergies = getattr(game, "synergies", None)
        if synergies and len(synergies.active) >= 3:
            self.unlock("synergy_master", game)
        if getattr(game, "meta", None) and game.meta.souls >= 50:
            self.unlock("soul_hoarder", game)
        run_mods = getattr(game, "run_mods", None)
        if (
            run_mods
            and run_mods.active_id == "legend"
            and game.state == "GAMEOVER"
            and game.difficulty.wave >= 6
        ):
            self.unlock("modifier_legend", game)

    def on_kill(self, game, enemy, at_night):
        if at_night:
            self.night_kills += 1
        if getattr(enemy, "is_elite", False):
            self.elite_kills += 1

    def to_dict(self):
        return {
            "unlocked": list(self.unlocked),
            "night_kills": self.night_kills,
            "elite_kills": self.elite_kills,
            "visited_ruins": self.visited_ruins,
        }

    def load_dict(self, data):
        if not data:
            return
        self.unlocked = list(data.get("unlocked", []))
        self.night_kills = data.get("night_kills", 0)
        self.elite_kills = data.get("elite_kills", 0)
        self.visited_ruins = data.get("visited_ruins", False)

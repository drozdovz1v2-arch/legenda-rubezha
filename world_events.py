"""Мировые события — динамические модификаторы мира."""

import random


EVENTS = {
    "blood_moon": {
        "name": "КРОВАВАЯ ЛУНА",
        "desc": "Элитные враги появляются чаще!",
        "color": (255, 80, 100),
    },
    "aurora": {
        "name": "Полярное сияние",
        "desc": "+50% опыта",
        "color": (120, 255, 200),
    },
    "invasion": {
        "name": "Вторжение",
        "desc": "Волна врагов наступает!",
        "color": (255, 160, 60),
    },
    "meteor_shower": {
        "name": "Метеоритный дождь",
        "desc": "Огненные удары с неба!",
        "color": (255, 100, 40),
    },
    "fog": {
        "name": "Туман войны",
        "desc": "Элиты сильнее на 8%",
        "color": (140, 150, 170),
    },
    "golden_hour": {
        "name": "Золотой час",
        "desc": "+80% золота",
        "color": (255, 220, 80),
    },
    "plague": {
        "name": "Чума",
        "desc": "Периодический урон",
        "color": (120, 200, 80),
    },
    "eclipse": {
        "name": "Затмение",
        "desc": "Враги сильнее, больше опыта",
        "color": (80, 60, 120),
    },
}


class WorldEventManager:
    def __init__(self):
        self.active = None
        self.timer = 0
        self.cooldown = 600
        self.exp_bonus = 1.0
        self.gold_bonus = 1.0
        self.damage_bonus = 1.0
        self.plague_tick = 0
        self.meteor_tick = 0

    def reset(self):
        self.active = None
        self.timer = 0
        self.cooldown = 600
        self.exp_bonus = 1.0
        self.gold_bonus = 1.0
        self.damage_bonus = 1.0
        self.plague_tick = 0
        self.meteor_tick = 0

    def update(self, daynight):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.active:
            self.timer -= 1
            if self.timer <= 0:
                self._clear_bonuses()
            return

        roll = random.random()
        if daynight.is_deep_night and self.cooldown <= 0 and roll < 0.0022:
            self._start("blood_moon", 900)
        elif daynight.phase == "dawn" and self.cooldown <= 0 and roll < 0.0016:
            self._start("aurora", 1800)
            self.exp_bonus = 1.5
        elif daynight.phase == "day" and self.cooldown <= 0 and roll < 0.0011:
            self._start("invasion", 480)
        elif daynight.phase == "dusk" and self.cooldown <= 0 and roll < 0.0013:
            self._start("golden_hour", 1500)
            self.gold_bonus = 1.8
        elif daynight.phase == "night" and self.cooldown <= 0 and roll < 0.0011:
            self._start("eclipse", 1200)
            self.exp_bonus = 1.3
            self.damage_bonus = 1.2
        elif self.cooldown <= 0 and roll < 0.0009:
            event_id = random.choice(["meteor_shower", "fog", "plague"])
            self._start(event_id, 900)
            if event_id == "fog":
                self.damage_bonus = 1.08

    def _clear_bonuses(self):
        self.active = None
        self.exp_bonus = 1.0
        self.gold_bonus = 1.0
        self.damage_bonus = 1.0
        self.meteor_tick = 0

    def _start(self, event_id, duration):
        self.active = event_id
        self.timer = duration
        self.cooldown = 2400
        self.meteor_tick = random.randint(20, 60)

    def tick_plague(self, player):
        if self.active != "plague":
            return
        self.plague_tick += 1
        if self.plague_tick >= 120 and player.hp > 0:
            self.plague_tick = 0
            player.apply_damage(2)

    def tick_meteor(self, game):
        if self.active != "meteor_shower" or game.game_simulation_paused():
            return None
        self.meteor_tick += 1
        if self.meteor_tick < 65:
            return None
        self.meteor_tick = random.randint(0, 25)
        view = game.camera.world_view_rect(game.current_w, game.current_h)
        if view.width < 80 or view.height < 80:
            return None
        margin = 48
        x = random.randint(view.left + margin, max(view.left + margin, view.right - margin))
        y = random.randint(view.top + margin, max(view.top + margin, view.bottom - margin))
        return x, y, 52, 12

    @property
    def elite_bonus(self):
        if self.active == "blood_moon":
            return 0.15
        if self.active == "fog":
            return 0.10
        return 0.0

    def banner_text(self):
        if not self.active:
            return None
        return EVENTS[self.active]["name"]

    def event_desc(self):
        if not self.active:
            return None
        return EVENTS[self.active]["desc"]

    def banner_color(self):
        if not self.active:
            return (255, 255, 255)
        return EVENTS[self.active]["color"]

    def to_dict(self):
        return {
            "active": self.active,
            "timer": self.timer,
            "cooldown": self.cooldown,
            "exp_bonus": self.exp_bonus,
            "gold_bonus": self.gold_bonus,
            "damage_bonus": self.damage_bonus,
            "meteor_tick": self.meteor_tick,
        }

    def load_dict(self, data):
        if not data:
            return
        self.active = data.get("active")
        self.timer = int(data.get("timer", 0))
        self.cooldown = int(data.get("cooldown", 600))
        self.exp_bonus = float(data.get("exp_bonus", 1.0))
        self.gold_bonus = float(data.get("gold_bonus", 1.0))
        self.damage_bonus = float(data.get("damage_bonus", 1.0))
        self.meteor_tick = int(data.get("meteor_tick", 0))

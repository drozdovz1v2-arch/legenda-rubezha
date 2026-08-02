"""Цикл день/ночь — влияет на освещение, спавн и события."""

from config import DAY_CYCLE_LENGTH, NIGHT_START, DAWN_START


class DayNightCycle:
    PHASES = {
        "dawn": "Рассвет",
        "day": "День",
        "dusk": "Закат",
        "night": "Ночь",
    }

    def __init__(self):
        self.time = DAY_CYCLE_LENGTH // 4
        self.paused = False

    def reset(self):
        self.time = DAY_CYCLE_LENGTH // 4

    def update(self, speed=1.0):
        if self.paused:
            return
        accum = getattr(self, "_accum", 0.0) + speed
        while accum >= 1.0:
            self.time = (self.time + 1) % DAY_CYCLE_LENGTH
            accum -= 1.0
        self._accum = accum

    @property
    def progress(self):
        return self.time / DAY_CYCLE_LENGTH

    @property
    def phase(self):
        p = self.progress
        if p < 0.08 or p >= 0.92:
            return "dawn"
        if p < NIGHT_START:
            return "day"
        if p < DAWN_START:
            return "night"
        return "dusk"

    @property
    def is_night(self):
        return self.phase in ("night", "dusk")

    @property
    def is_deep_night(self):
        p = self.progress
        return NIGHT_START <= p < (NIGHT_START + 0.18)

    @property
    def darkness(self):
        p = self.progress
        if p < 0.08:
            return 1.0 - p / 0.08
        if p < NIGHT_START:
            return 0.0
        if p < DAWN_START:
            if p < NIGHT_START + 0.12:
                return (p - NIGHT_START) / 0.12
            if p > DAWN_START - 0.10:
                return (DAWN_START - p) / 0.10
            return 1.0
        return max(0.0, (p - DAWN_START) / 0.08)

    @property
    def spawn_multiplier(self):
        if self.is_deep_night:
            return 1.6
        if self.is_night:
            return 1.25
        return 1.0

    @property
    def elite_chance_bonus(self):
        return 0.08 if self.is_deep_night else (0.04 if self.is_night else 0.0)

    def clock_text(self):
        hours = int(self.progress * 24) % 24
        minutes = int((self.progress * 24 * 60) % 60)
        return f"{hours:02d}:{minutes:02d}  {self.PHASES[self.phase]}"

    def to_dict(self):
        return {"time": self.time}

    def load_dict(self, data):
        if data and "time" in data:
            self.time = int(data["time"]) % DAY_CYCLE_LENGTH

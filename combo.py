"""Комбо-система: серия убийств даёт бонус золота и опыта."""

COMBO_WINDOW = 180  # кадров (~3 сек при 60 FPS)


class ComboTracker:
    def __init__(self):
        self.count = 0
        self.timer = 0
        self.peak = 0
        self.flash_timer = 0

    def reset(self):
        self.count = 0
        self.timer = 0
        self.peak = 0
        self.flash_timer = 0
        self._extra_bonus = 0.0

    def on_kill(self, extra_bonus=0.0):
        if self.timer > 0:
            self.count += 1
        else:
            self.count = 1
        self.timer = COMBO_WINDOW
        self.peak = max(self.peak, self.count)
        if self.count >= 2:
            self.flash_timer = 45
        self._extra_bonus = extra_bonus

    def update(self):
        if self.timer > 0:
            self.timer -= 1
        if self.timer <= 0 and self.count > 0:
            self.count = 0
        if self.flash_timer > 0:
            self.flash_timer -= 1

    @property
    def multiplier(self):
        if self.count < 2:
            return 1.0
        bonus = getattr(self, "_extra_bonus", 0.0)
        return 1.0 + (self.count - 1) * (0.08 + bonus)

    def bonus_text(self):
        if self.count < 2:
            return None
        pct = int((self.multiplier - 1.0) * 100)
        return f"КОМБО x{self.count}  +{pct}%"

    def to_dict(self):
        return {"count": self.count, "timer": self.timer, "peak": self.peak}

    def load_dict(self, data):
        if not data:
            return
        self.count = int(data.get("count", 0))
        self.timer = int(data.get("timer", 0))
        self.peak = int(data.get("peak", 0))
